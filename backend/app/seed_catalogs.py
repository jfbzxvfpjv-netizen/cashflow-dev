"""
Módulo 4 — Seed de catálogos con datos reales (versión síncrona).
Compatible con el seed.py existente que usa SQLAlchemy síncrono.

Datos reales extraídos del fichero Caja_Bata_06.xlsx:
- 6 proyectos con todas sus obras
- 27 categorías con subcategorías
- 16 vehículos de flota
- 4 socios
"""

from decimal import Decimal
from app.database import SessionLocal

# ─── Importar modelos ─────────────────────────────────────────
# Los modelos se importan dentro de la función para evitar
# problemas de importación circular antes de crear tablas.


# ─── DATOS REALES ─────────────────────────────────────────────

PROJECTS_WITH_WORKS = {
    "General": {
        "name": "General",
        "description": "Gastos generales de administración y operativa",
        "works": [
            "Administracion", "Oficina_Bata", "Oficina_Malabo",
            "Almacen_Bata", "Piso_Vatsy_Bata", "Piso_Pedro_Bata",
            "Vivienda_Mongomo", "Vivienda_Ebibeyin", "Perro_Zarra_Bata",
            "Malabo_Bata", "Bata_Malabo", "Mantenimiento_Grupos",
        ],
    },
    "Socios": {
        "name": "Socios",
        "description": "Operaciones relacionadas con los socios de la empresa",
        "works": ["Anticipos", "Dividendos"],
    },
    "Mto_GETESA": {
        "name": "Mantenimiento GETESA",
        "description": "Mantenimiento de estaciones base y centros emisores del contrato GETESA",
        "works": [
            "Acoga_GETESA", "Anvam_GETESA", "Akom_GETESA", "Anisok_GETESA",
            "Abama_1_GETESA", "Abama_2_GETESA", "Ayene_GETESA",
            "Ayen_Sat_GETESA", "Alum_GETESA", "Akurenam_GETESA",
            "Afanangui_GETESA", "Ayanve_GETESA", "Akam_Atom_GETESA",
            "Bilosi_GETESA", "Bisobinam_GETESA", "Bidjabidjan_GETESA",
            "Bitica_GETESA", "Bongoro_GETESA", "Corisco_GETESA",
            "Cabo_San_Juan_GETESA", "Cogo_GETESA", "Djibloho_GETESA",
            "Echam_GETESA", "Enoc_Eseng_GETESA", "Esabok_Eyen_GETESA",
            "Evinayong_GETESA", "Ebolowa_GETESA", "Ebibeyin_Tv_GETESA",
            "Ebibeyin_Fh_GETESA", "Ebibeyin_Seguibat_GETESA",
            "Elat_GETESA", "Efulan_GETESA", "Forrestier_GETESA",
            "Km_17_GETESA", "Mbeka_GETESA", "Mican_GETESA",
            "Monte_Bata_GETESA", "Monte_Duba_GETESA",
            "Monte_Chocolate_GETESA", "Monte_Allen_GETESA",
            "Mongomo_Fh_GETESA", "Minang_GETESA", "Micomiseng_GETESA",
        ],
    },
    "Mto_RTVGE": {
        "name": "Mantenimiento RTVGE",
        "description": "Mantenimiento de instalaciones de Radio Televisión de Guinea Ecuatorial",
        "works": [
            "General_RTVGE", "Equipos_RTVGE", "Ayanve_RTVGE",
            "Ayene_RTVGE", "Anisok_RTVGE", "Akonibe_RTVGE",
            "Asokabia_RTVGE", "Bitica_RTVGE", "Bilossi_RTVGE",
            "Bisobinam_RTVGE", "Cogo_RTVGE", "Elat_RTVGE",
            "Ebolowa_RTVGE", "Evinayong_RTVGE", "Ebibeyin_RTVGE",
            "Forestier_RTVGE", "Monte_Chocolate_RTVGE",
            "Monte_Duba_RTVGE", "Monte_Allen_RTVGE", "Mongomo_RTVGE",
            "Micomiseng_RTVGE", "Mbe_Mboma_RTVGE", "Mbayop_RTVGE",
            "Mbini_RTVGE", "Nkue_RTVGE", "Nvom_RTVGE",
            "Nfaman_RTVGE", "Niefang_RTVGE", "Oyec_Esong_RTVGE",
            "Ongoma_RTVGE",
        ],
    },
    "GETESA": {
        "name": "GETESA",
        "description": "Obras específicas del cliente GETESA",
        "works": [
            "Casa_DG_Mongomo", "Sala_Ac_Ceiba1_Ceiba2",
            "Incidencias_Ran_de_Getesa",
        ],
    },
    "Flota": {
        "name": "Flota",
        "description": "Gastos vinculados a los vehículos de la flota",
        "works": [
            "AN_063_L", "AN_448_H", "BN_563_AC", "LT_553_N",
            "LT_083_AB", "LT_782_AM", "LT_857_AM", "LT_860_AM",
            "WN_044_AH", "WN_181_AF", "WN_190_AM", "WN_192_AM",
            "WN_194_AM", "WN_421_T", "WN_545_AG", "WN_789_AE",
        ],
    },
}

CATEGORIES_WITH_SUBCATEGORIES = [
    ("Transporte", "expense", True, [
        "Peajes", "Taxi", "Vuelos", "Barco", "Envio_Terrestre", "Alquiler_Vehiculo"]),
    ("Flota_vehiculos", "expense", True, [
        "Combustible_Flota", "Reparacion", "Neumaticos",
        "Compra_vehiculos", "Impuestos_Circulacion", "Seguro", "ITV_Revision"]),
    ("Energia", "expense", True, ["Combustible_Grupos", "Electricidad"]),
    ("Mantenimiento", "expense", True, [
        "Grupos_Electrogenos", "Instalaciones", "Equipos", "Vehiculos"]),
    ("Nomina_Salarios", "expense", True, [
        "Salarios", "Anticipo_Salario", "Vacaciones", "Gratificaciones",
        "Seguridad_Social", "Indemnizaciones"]),
    ("Servicios_Externos", "expense", True, [
        "Estajistas", "Subcontratas", "Servicios_Varios",
        "Asesorias", "Honorarios_profesionales"]),
    ("Servicios_Basicos", "expense", True, [
        "Internet", "Telefono", "Electricidad", "Agua", "Basura", "Canales"]),
    ("Suministros", "expense", True, [
        "Limpieza", "Papeleria", "Cafeteria", "Suministros_Varios"]),
    ("Arriendo", "expense", True, ["Viviendas", "Oficinas", "Almacenes"]),
    ("Dietas", "expense", True, ["Hoteles", "Comidas", "Otros_dietas"]),
    ("Logistica", "expense", True, [
        "Envio_Aereo", "Envio_Maritimo", "Envio_Terrestre"]),
    ("Maquinaria", "expense", True, [
        "Combustible_Maq", "Reparacion_Maq", "Compra_Maquinaria", "Alquiler_Maquinaria"]),
    ("Compras_mercancia", "expense", True, [
        "Materiales", "Herramientas", "Equipos", "Consumibles", "Repuestos"]),
    ("Otros_gastos", "expense", True, ["Gastos_Varios"]),
    ("Atenciones_comerciales", "expense", False, [
        "Representacion", "Protocolo", "Obsequios"]),
    ("Gastos_Sociales", "expense", True, [
        "Gastos_medicos", "Formacion", "Bienestar"]),
    ("Transferencia_entrada", "income", True, [
        "Cheque", "Transferencia_bancaria"]),
    ("Otros_ingresos", "income", True, [
        "Ingresos_Varios", "Devoluciones", "Intereses_bancarios", "Subvenciones"]),
    ("Divisas", "both", True, ["Compra_Euros", "Entrega_Euros", "Otras_divisas"]),
    ("Anticipos_empleados", "expense", True, [
        "Anticipo_Salario", "Anticipo_Gastos"]),
    ("Circulantes", "both", True, [
        "Apertura_Circulante", "Liquidacion_Circulante", "Devolucion_Sobrante"]),
    ("Socios", "both", True, [
        "Anticipo_Socio", "Pago_Factura_Socio",
        "Compensacion_Dividendos", "Aportacion_Socio"]),
    ("Envios_Dinero", "both", True, [
        "Western_Union", "MoneyGram", "Operador_Local", "Comision_Envio"]),
    ("Gastos_Reembolsables", "expense", True, [
        "Tarjeta_Personal", "Transferencia_Personal", "Efectivo_Personal"]),
    ("Ingresos_Delegacion", "both", True, [
        "Transferencia_Bata_Malabo", "Transferencia_Malabo_Bata"]),
    ("Pagos_Fraccionados", "expense", True, [
        "Primer_Plazo", "Plazo_Intermedio", "Plazo_Final"]),
    ("Anticipos_socios", "expense", True, [
        "Anticipo_Socio", "Pago_Factura_Socio"]),
]

VEHICLES = [
    "AN_063_L", "AN_448_H", "BN_563_AC", "LT_553_N",
    "LT_083_AB", "LT_782_AM", "LT_857_AM", "LT_860_AM",
    "WN_044_AH", "WN_181_AF", "WN_190_AM", "WN_192_AM",
    "WN_194_AM", "WN_421_T", "WN_545_AG", "WN_789_AE",
]

PARTNERS = [
    {"code": "S001", "full_name": "Socio Principal",
     "participation_pct": Decimal("40.00"), "can_contribute": True},
    {"code": "S002", "full_name": "Socio Segundo",
     "participation_pct": Decimal("30.00"), "can_contribute": False},
    {"code": "S003", "full_name": "Socio Tercero",
     "participation_pct": Decimal("20.00"), "can_contribute": False},
    {"code": "S004", "full_name": "Socio Cuarto",
     "participation_pct": Decimal("10.00"), "can_contribute": False},
]


# ─── FUNCIÓN PRINCIPAL (SÍNCRONA) ─────────────────────────────

def seed_catalogs_sync():
    """
    Carga todos los catálogos con datos reales. Versión síncrona
    compatible con el seed.py existente que usa SessionLocal.
    Idempotente: no duplica registros si ya existen.
    """
    # Importar modelos aquí para evitar problemas de importación circular
    from app.models import (
        Project, Work, TransactionCategory, TransactionSubcategory,
        Supplier, Employee, Partner, CorporateAccount, Vehicle,
    )

    db = SessionLocal()
    try:
        print("")
        print("=" * 60)
        print("  SEED DE CATÁLOGOS — Módulo 4")
        print("=" * 60)

        # ── Proyectos y obras ──────────────────────
        print("\n> Cargando proyectos y obras...")
        projects_created = 0
        works_created = 0

        for code, data in PROJECTS_WITH_WORKS.items():
            project = db.query(Project).filter(Project.code == code).first()

            if not project:
                project = Project(
                    code=code,
                    name=data["name"],
                    description=data.get("description"),
                )
                db.add(project)
                db.flush()
                projects_created += 1

            for work_code in data["works"]:
                existing = db.query(Work).filter(
                    Work.project_id == project.id,
                    Work.code == work_code
                ).first()
                if not existing:
                    work = Work(
                        project_id=project.id,
                        code=work_code,
                        name=work_code.replace("_", " "),
                    )
                    db.add(work)
                    works_created += 1

        db.commit()
        total_works = sum(len(d["works"]) for d in PROJECTS_WITH_WORKS.values())
        print(f"  {projects_created} proyectos creados, {works_created} obras creadas")
        print(f"  Total en BD: {len(PROJECTS_WITH_WORKS)} proyectos, {total_works} obras")

        # ── Categorías y subcategorías ─────────────
        print("\n> Cargando categorías y subcategorías...")
        cats_created = 0
        subcats_created = 0

        for cat_name, cat_type, req_attach, subcats in CATEGORIES_WITH_SUBCATEGORIES:
            category = db.query(TransactionCategory).filter(
                TransactionCategory.name == cat_name
            ).first()

            if not category:
                category = TransactionCategory(
                    name=cat_name,
                    type=cat_type,
                    requires_attachment=req_attach,
                )
                db.add(category)
                db.flush()
                cats_created += 1

            for subcat_name in subcats:
                existing = db.query(TransactionSubcategory).filter(
                    TransactionSubcategory.category_id == category.id,
                    TransactionSubcategory.name == subcat_name
                ).first()
                if not existing:
                    subcat = TransactionSubcategory(
                        category_id=category.id,
                        name=subcat_name,
                    )
                    db.add(subcat)
                    subcats_created += 1

        db.commit()
        total_subcats = sum(len(s) for _, _, _, s in CATEGORIES_WITH_SUBCATEGORIES)
        print(f"  {cats_created} categorías creadas, {subcats_created} subcategorías creadas")
        print(f"  Total en BD: {len(CATEGORIES_WITH_SUBCATEGORIES)} categorías, {total_subcats} subcategorías")

        # ── Vehículos de flota ─────────────────────
        print("\n> Cargando vehículos de flota...")
        vehicles_created = 0

        for plate in VEHICLES:
            existing = db.query(Vehicle).filter(Vehicle.plate == plate).first()
            if not existing:
                vehicle = Vehicle(
                    plate=plate,
                    brand=None,
                    model=None,
                    year=None,
                    delegacion="Bata",
                )
                db.add(vehicle)
                vehicles_created += 1

        db.commit()
        print(f"  {vehicles_created} vehículos creados (delegación Bata)")

        # ── Socios ─────────────────────────────────
        print("\n> Cargando socios...")
        partners_created = 0

        for p_data in PARTNERS:
            existing = db.query(Partner).filter(Partner.code == p_data["code"]).first()
            if not existing:
                partner = Partner(
                    code=p_data["code"],
                    full_name=p_data["full_name"],
                    participation_pct=p_data["participation_pct"],
                    can_contribute=p_data["can_contribute"],
                    current_balance=Decimal("0.00"),
                )
                db.add(partner)
                partners_created += 1

        db.commit()
        print(f"  {partners_created} socios creados (saldo inicial 0)")

        # ── Resumen ────────────────────────────────
        print("")
        print("=" * 60)
        print("  SEED DE CATÁLOGOS COMPLETADO")
        print("=" * 60)

    except Exception as e:
        db.rollback()
        print(f"\nError en seed de catálogos: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_catalogs_sync()
