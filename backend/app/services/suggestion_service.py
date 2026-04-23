"""Servicio de sugerencias de categorización para transacciones.

Implementa el árbol de 5 niveles descrito en
pliego_s10_sugerencias_categorizacion_v1.md.

Python puro, sin dependencias externas (numpy/sklearn).
Rendimiento objetivo: <50ms p95 con corpus ≤5.000 documentos.
"""

import math
import time
import unicodedata
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session

from app.models import catalogs as m


# =============================================================================
# CONSTANTES DE DISEÑO (ver sección 9 del pliego)
# =============================================================================

STOP_WORDS: Set[str] = {
    "para", "por", "con", "sin", "del", "los", "las", "una", "uno",
    "sobre", "hasta", "desde", "entre",
    "enero", "febrero", "marzo", "abril", "mayo", "junio",
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre",
    "mes", "ano", "semana", "dia",
}

MIN_TOKEN_LENGTH = 3
JACCARD_THRESHOLD_L1 = 0.5
COSINE_THRESHOLD_L2 = 0.3
PROJECT_DOMINANCE_GATE = 0.50
L3_HIGH_WEIGHT = 0.50
L3_LOW_WEIGHT = 0.30
L4_MIN_MOVEMENTS = 3
L4_MODE_THRESHOLD = 0.70

CACHE_TTL_SECONDS = 300


# =============================================================================
# CACHÉ EN MEMORIA (TTL 5 min, sin invalidación por evento — ver 6.2 del pliego)
# =============================================================================

_cache: Dict = {
    "idf": None,                  # Dict[str, float]
    "corpus_docs": None,           # List[Dict] — cada doc con tokens, tfidf, cat, subcat, etc.
    "counterparty_index": None,    # Dict[str_normalizada, List[idx en corpus_docs]]
    "counterparty_mode": None,     # Dict[str_normalizada, (cat_id, subcat_id, pct, n)]
    "project_dominance": None,     # Dict[project_id, float]
    "refreshed_at": 0.0,
}


def _cache_is_fresh() -> bool:
    return (
        _cache["idf"] is not None
        and (time.time() - _cache["refreshed_at"]) < CACHE_TTL_SECONDS
    )


# =============================================================================
# NORMALIZACIÓN Y TOKENIZACIÓN
# =============================================================================

def normalize_text(s: str) -> str:
    """Minúsculas + sin acentos + sin puntuación + espacios colapsados."""
    if not s:
        return ""
    s = s.lower()
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    out_chars = []
    for c in s:
        if c.isalnum() or c == " ":
            out_chars.append(c)
        else:
            out_chars.append(" ")
    return " ".join("".join(out_chars).split())


def tokenize(s: str) -> Set[str]:
    """Devuelve conjunto de tokens útiles (≥3 letras, sin stop-words, sin números puros).

    Filtrado adicional de tokens compuestos solo por dígitos: los números
    (kilometrajes, importes parciales, referencias numéricas) actúan como
    ruido — inflan la norma L2 del vector sin aportar señal categorial.
    """
    if not s:
        return set()
    normalized = normalize_text(s)
    return {
        tok for tok in normalized.split()
        if len(tok) >= MIN_TOKEN_LENGTH
        and tok not in STOP_WORDS
        and not tok.isdigit()
    }


# =============================================================================
# CÁLCULO DE TF-IDF (Python puro)
# =============================================================================

def _compute_idf(docs_tokens: List[Set[str]]) -> Dict[str, float]:
    """IDF suavizado: log((N+1) / (df+1)) + 1."""
    n = len(docs_tokens)
    if n == 0:
        return {}
    df: Dict[str, int] = defaultdict(int)
    for tokens in docs_tokens:
        for tok in tokens:
            df[tok] += 1
    return {tok: math.log((n + 1) / (dfi + 1)) + 1 for tok, dfi in df.items()}


def _tfidf_vector(tokens_list: List[str], idf: Dict[str, float]) -> Dict[str, float]:
    """Vector TF-IDF de un documento, L2-normalizado."""
    if not tokens_list:
        return {}
    tf = Counter(tokens_list)
    total = len(tokens_list)
    vec = {
        tok: (count / total) * idf.get(tok, 0.0)
        for tok, count in tf.items()
    }
    norm = math.sqrt(sum(v * v for v in vec.values()))
    if norm == 0:
        return {}
    return {tok: v / norm for tok, v in vec.items()}


def _cosine(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """Similaridad coseno entre dos vectores TF-IDF ya L2-normalizados."""
    if not vec_a or not vec_b:
        return 0.0
    if len(vec_a) > len(vec_b):
        vec_a, vec_b = vec_b, vec_a
    return sum(v * vec_b.get(tok, 0.0) for tok, v in vec_a.items())


# =============================================================================
# CARGA Y CACHEO DEL CORPUS
# =============================================================================

def _load_corpus(db: Session, delegacion: Optional[str]) -> None:
    """Construye el caché leyendo transacciones aprobadas no canceladas.

    Filtra por delegación si viene especificada. El caché es global al
    proceso; la delegación se almacena por documento para filtrar en matching.
    """
    query = db.query(m.Transaction).filter(
        m.Transaction.approval_status == "approved",
        m.Transaction.cancelled == False,  # noqa: E712
        m.Transaction.concept.isnot(None),
    )

    txns = query.all()

    corpus_docs: List[Dict] = []
    docs_tokens: List[Set[str]] = []

    for t in txns:
        tokens_set = tokenize(t.concept or "")
        if not tokens_set:
            continue
        tokens_list = list(tokens_set)
        corpus_docs.append({
            "id": t.id,
            "tokens_set": tokens_set,
            "tokens_list": tokens_list,
            "tfidf": None,  # se calcula tras tener IDF
            "category_id": t.category_id,
            "subcategory_id": t.subcategory_id,
            "delegacion": t.delegacion,
            "counterparty_key": _counterparty_key(t),
            "supplier_id": t.supplier_id,
            "employee_id": t.employee_id,
            "partner_id": t.partner_id,
            "project_ids": [],  # se rellena tras el bucle con _project_ids_bulk
        })
        docs_tokens.append(tokens_set)

    # Carga bulk de project_ids (la relación no está mapeada en Transaction)
    txn_ids = [doc["id"] for doc in corpus_docs]
    project_map = _project_ids_bulk(db, txn_ids)
    for doc in corpus_docs:
        doc["project_ids"] = project_map.get(doc["id"], [])

    idf = _compute_idf(docs_tokens)

    for doc in corpus_docs:
        doc["tfidf"] = _tfidf_vector(doc["tokens_list"], idf)

    counterparty_index: Dict[str, List[int]] = defaultdict(list)
    for idx, doc in enumerate(corpus_docs):
        if doc["counterparty_key"]:
            counterparty_index[doc["counterparty_key"]].append(idx)

    counterparty_mode: Dict[str, Tuple[int, int, float, int]] = {}
    for key, indices in counterparty_index.items():
        n = len(indices)
        if n < L4_MIN_MOVEMENTS:
            continue
        cat_counter: Counter = Counter()
        subcat_by_cat: Dict[int, Counter] = defaultdict(Counter)
        for i in indices:
            cat = corpus_docs[i]["category_id"]
            sub = corpus_docs[i]["subcategory_id"]
            cat_counter[cat] += 1
            subcat_by_cat[cat][sub] += 1
        cat_mode, cat_count = cat_counter.most_common(1)[0]
        pct = cat_count / n
        if pct < L4_MODE_THRESHOLD:
            continue
        subcat_mode = subcat_by_cat[cat_mode].most_common(1)[0][0]
        counterparty_mode[key] = (cat_mode, subcat_mode, pct, n)

    project_dominance: Dict[int, float] = {}
    project_docs: Dict[int, List[int]] = defaultdict(list)
    for idx, doc in enumerate(corpus_docs):
        for pid in doc["project_ids"]:
            project_docs[pid].append(idx)
    for pid, indices in project_docs.items():
        cat_counter = Counter(corpus_docs[i]["category_id"] for i in indices)
        if not cat_counter:
            continue
        _, max_count = cat_counter.most_common(1)[0]
        project_dominance[pid] = max_count / len(indices)

    _cache["idf"] = idf
    _cache["corpus_docs"] = corpus_docs
    _cache["counterparty_index"] = dict(counterparty_index)
    _cache["counterparty_mode"] = counterparty_mode
    _cache["project_dominance"] = project_dominance
    _cache["refreshed_at"] = time.time()


def _counterparty_key(t) -> Optional[str]:
    """Genera una clave de contraparte unificada.

    Prioriza FK (supplier/employee/partner) sobre texto libre.
    Retorna string tipo 'sup:42', 'emp:17', 'par:3' o 'free:texto normalizado'.
    """
    if t.supplier_id:
        return f"sup:{t.supplier_id}"
    if t.employee_id:
        return f"emp:{t.employee_id}"
    if t.partner_id:
        return f"par:{t.partner_id}"
    if t.counterparty_free:
        normalized = normalize_text(t.counterparty_free)
        if normalized:
            return f"free:{normalized}"
    return None


def _project_ids_bulk(db: Session, txn_ids: List[int]) -> Dict[int, List[int]]:
    """Query SQL directa a transaction_projects en bloque.

    La relación no está mapeada como atributo en el modelo Transaction;
    se resuelve por consulta agrupada una sola vez al cargar el corpus.
    """
    from sqlalchemy import text
    if not txn_ids:
        return {}
    result: Dict[int, List[int]] = defaultdict(list)
    rows = db.execute(
        text("""
            SELECT transaction_id, project_id
            FROM transaction_projects
            WHERE transaction_id = ANY(:ids)
        """),
        {"ids": txn_ids},
    ).fetchall()
    for txn_id, project_id in rows:
        result[txn_id].append(project_id)
    return dict(result)


def _ensure_cache_fresh(db: Session) -> None:
    if not _cache_is_fresh():
        _load_corpus(db, delegacion=None)


# =============================================================================
# CONSTRUCCIÓN DE CLAVE DE CONTRAPARTE DESDE REQUEST
# =============================================================================

def _request_counterparty_key(
    supplier_id: Optional[int],
    employee_id: Optional[int],
    partner_id: Optional[int],
    counterparty_free: Optional[str],
) -> Optional[str]:
    if supplier_id:
        return f"sup:{supplier_id}"
    if employee_id:
        return f"emp:{employee_id}"
    if partner_id:
        return f"par:{partner_id}"
    if counterparty_free:
        normalized = normalize_text(counterparty_free)
        if normalized:
            return f"free:{normalized}"
    return None


# =============================================================================
# NIVELES DEL ÁRBOL DE MATCHING
# =============================================================================

def _level_1_counterparty_and_concept(
    concept_tokens: Set[str],
    cp_key: Optional[str],
    delegacion: Optional[str],
) -> Optional[Dict]:
    """Nivel 1 — contraparte exacta + Jaccard concepto ≥0.5. Confianza alta."""
    if not cp_key or not concept_tokens:
        return None
    indices = _cache["counterparty_index"].get(cp_key, [])
    if not indices:
        return None
    matches: List[int] = []
    for i in indices:
        doc = _cache["corpus_docs"][i]
        if delegacion and doc["delegacion"] != delegacion:
            continue
        inter = len(concept_tokens & doc["tokens_set"])
        union = len(concept_tokens | doc["tokens_set"])
        if union == 0:
            continue
        if inter / union >= JACCARD_THRESHOLD_L1:
            matches.append(i)
    if not matches:
        return None
    return _mode_from_indices(matches, source_level=1, scope="counterparty", confidence="high")


def _level_2_project_concept(
    concept_tokens: Set[str],
    project_id: Optional[int],
    delegacion: Optional[str],
    query_tfidf: Dict[str, float],
) -> Optional[Dict]:
    """Nivel 2 — TF-IDF agregado dentro de proyecto con dominancia ≥50%. Confianza alta.

    Agregación ponderada por similaridad coseno (misma lógica que nivel 3, pero
    restringida al subcorpus del proyecto). Exige coseno ≥0.3 por doc y ≥2 docs
    contribuyentes para descartar coincidencias espurias de un único documento.
    """
    if not project_id or not concept_tokens:
        return None
    dominance = _cache["project_dominance"].get(project_id, 0.0)
    if dominance < PROJECT_DOMINANCE_GATE:
        return None
    weights_by_cat: Dict[Tuple[int, int], float] = defaultdict(float)
    total_weight = 0.0
    samples = 0
    for doc in _cache["corpus_docs"]:
        if project_id not in doc["project_ids"]:
            continue
        if delegacion and doc["delegacion"] != delegacion:
            continue
        sim = _cosine(query_tfidf, doc["tfidf"])
        if sim < COSINE_THRESHOLD_L2:
            continue
        key = (doc["category_id"], doc["subcategory_id"])
        weights_by_cat[key] += sim
        total_weight += sim
        samples += 1
    if samples < 2 or total_weight == 0:
        return None
    (cat_id, sub_id), _ = max(weights_by_cat.items(), key=lambda kv: kv[1])
    return {
        "category_id": cat_id,
        "subcategory_id": sub_id,
        "confidence": "high",
        "source_level": 2,
        "sample_count": samples,
        "scope": "project",
    }


def _level_3_concept_global(
    concept_tokens: Set[str],
    delegacion: Optional[str],
    query_tfidf: Dict[str, float],
) -> Optional[Dict]:
    """Nivel 3 — votos ponderados por similaridad coseno en todo el corpus."""
    if not concept_tokens:
        return None
    weights_by_cat: Dict[Tuple[int, int], float] = defaultdict(float)
    total_weight = 0.0
    samples = 0
    for doc in _cache["corpus_docs"]:
        if delegacion and doc["delegacion"] != delegacion:
            continue
        sim = _cosine(query_tfidf, doc["tfidf"])
        if sim <= 0:
            continue
        key = (doc["category_id"], doc["subcategory_id"])
        weights_by_cat[key] += sim
        total_weight += sim
        samples += 1
    if total_weight == 0:
        return None
    (cat_id, sub_id), top_weight = max(weights_by_cat.items(), key=lambda kv: kv[1])
    pct = top_weight / total_weight
    if pct >= L3_HIGH_WEIGHT:
        confidence = "medium"
    elif pct >= L3_LOW_WEIGHT:
        confidence = "medium-low"
    else:
        return None
    return {
        "category_id": cat_id,
        "subcategory_id": sub_id,
        "confidence": confidence,
        "source_level": 3,
        "sample_count": samples,
        "scope": "global",
    }


def _level_4_counterparty_mode(
    cp_key: Optional[str],
    delegacion: Optional[str],
) -> Optional[Dict]:
    """Nivel 4 — moda categorial de contraparte recurrente ≥70%."""
    if not cp_key:
        return None
    mode = _cache["counterparty_mode"].get(cp_key)
    if not mode:
        return None
    cat_id, sub_id, pct, n = mode
    if delegacion:
        indices = _cache["counterparty_index"].get(cp_key, [])
        n_deleg = sum(
            1 for i in indices
            if _cache["corpus_docs"][i]["delegacion"] == delegacion
        )
        if n_deleg < L4_MIN_MOVEMENTS:
            return None
    return {
        "category_id": cat_id,
        "subcategory_id": sub_id,
        "confidence": "medium-low",
        "source_level": 4,
        "sample_count": n,
        "scope": "counterparty",
    }


# =============================================================================
# UTILIDADES
# =============================================================================

def _mode_from_indices(
    indices: List[int],
    source_level: int,
    scope: str,
    confidence: str,
) -> Dict:
    """Agrupa por (cat, subcat) y devuelve la moda."""
    pairs = [
        (_cache["corpus_docs"][i]["category_id"],
         _cache["corpus_docs"][i]["subcategory_id"])
        for i in indices
    ]
    counter = Counter(pairs)
    (cat_id, sub_id), count = counter.most_common(1)[0]
    return {
        "category_id": cat_id,
        "subcategory_id": sub_id,
        "confidence": confidence,
        "source_level": source_level,
        "sample_count": count,
        "scope": scope,
    }


def _resolve_names(db: Session, category_id: int, subcategory_id: int) -> Tuple[str, str]:
    cat = db.query(m.TransactionCategory).filter(m.TransactionCategory.id == category_id).first()
    sub = db.query(m.TransactionSubcategory).filter(m.TransactionSubcategory.id == subcategory_id).first()
    return (cat.name if cat else "", sub.name if sub else "")


def _silence() -> Dict:
    return {
        "category_id": None,
        "subcategory_id": None,
        "category_name": None,
        "subcategory_name": None,
        "confidence": None,
        "source_level": 5,
        "sample_count": None,
        "scope": None,
    }


# =============================================================================
# ORQUESTADOR PÚBLICO
# =============================================================================

def suggest_categorization(
    db: Session,
    concept: Optional[str],
    supplier_id: Optional[int],
    employee_id: Optional[int],
    partner_id: Optional[int],
    counterparty_free: Optional[str],
    project_id: Optional[int],
    delegacion: Optional[str],
) -> Dict:
    """Punto de entrada único. Devuelve dict listo para serializar con el schema."""
    _ensure_cache_fresh(db)

    concept_tokens = tokenize(concept or "")
    cp_key = _request_counterparty_key(supplier_id, employee_id, partner_id, counterparty_free)
    query_tfidf = _tfidf_vector(list(concept_tokens), _cache["idf"]) if concept_tokens else {}

    result = _level_1_counterparty_and_concept(concept_tokens, cp_key, delegacion)
    if result is None:
        result = _level_2_project_concept(concept_tokens, project_id, delegacion, query_tfidf)
    if result is None:
        result = _level_3_concept_global(concept_tokens, delegacion, query_tfidf)
    if result is None:
        result = _level_4_counterparty_mode(cp_key, delegacion)
    if result is None:
        return _silence()

    cat_name, sub_name = _resolve_names(db, result["category_id"], result["subcategory_id"])
    result["category_name"] = cat_name
    result["subcategory_name"] = sub_name
    return result
