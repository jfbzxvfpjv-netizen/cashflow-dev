"""
Carga de catálogos reales: empleados, proveedores y cuentas corporativas.
Ejecutar dentro del contenedor backend:
  docker compose exec backend python /app/load_catalogs.py
O copiar al directorio backend/ y:
  docker compose exec backend python load_catalogs.py
"""
import unicodedata
from decimal import Decimal
from datetime import date
from app.database import SessionLocal
from app.models.catalogs import Employee, Supplier, CorporateAccount

def strip_accents(s):
    """Elimina acentos y normaliza espacios."""
    if not s:
        return s
    s = s.strip()
    nfkd = unicodedata.normalize('NFKD', s)
    return ''.join(c for c in nfkd if not unicodedata.combining(c))

# ============================================================================
# EMPLEADOS — 31 registros (22 Bata + 9 Malabo)
# ============================================================================
EMPLOYEES = [
    # (code, full_name, department, position, delegacion, salary_gross, salary_transfer, effective_date)
    # --- BATA (22) ---
    ("B001", "Pedro Lopez Requena", "Directiva", "Gerente", "Bata", 2850846, 2850846, "2026-01-01"),
    ("B002", "Ana Jessi Mayer Kowe", "Administracion", "Responsable_Administracion", "Bata", 560000, 560000, "2026-01-01"),
    ("B003", "Juan Carlos Sierra Rodriguez", "Tecnico", "Tecnico_Coordinador", "Bata", 1250000, 1250000, "2026-01-01"),
    ("B004", "Jose Ramon Caballero Castillo", "Tecnico", "Tecnico_Jefe_Obra", "Bata", 1550000, 1550000, "2026-01-01"),
    ("B005", "Enmanuel Domenech Zaldivar", "Tecnico", "Tecnico_Campo", "Bata", 750000, 750000, "2026-01-01"),
    ("B006", "Yosvani Echemendia Marin", "Tecnico", "Tecnico_Campo", "Bata", 1600000, 1600000, "2026-01-01"),
    ("B007", "Vatsy Manampy Tongasoa Rakotomahefa", "Tecnico", "Tecnico_IP", "Bata", 2092500, 2092500, "2026-01-01"),
    ("B008", "Yemalin Isidore Gbovoechan", "Mecanica", "Mecanico_Primera", "Bata", 850000, 850000, "2026-01-01"),
    ("B009", "Mamadou Bakayoko", "Mecanica", "Mecanico_Primera", "Bata", 850000, 850000, "2026-01-01"),
    ("B010", "Bamaba Bazoumana", "Mecanica", "Mecanico_Primera", "Bata", 850000, 850000, "2026-01-01"),
    ("B011", "Tella Olamide Bienvenu", "Mecanica", "Mecanico_Primera", "Bata", 450000, 0, "2026-01-01"),
    ("B012", "Sekou Sylla", "Mecanica", "Mecanico_Primera", "Bata", 450000, 0, "2026-01-01"),
    ("B013", "Yaya Tuo Kparadjogo", "Mecanica", "Mecanico_Primera", "Bata", 400000, 400000, "2026-01-01"),
    ("B014", "Marcos Owono Nguema Nzang", "Tecnico", "Tecnico_Instalador", "Bata", 600000, 600000, "2026-01-01"),
    ("B015", "Angel Maye Bayeme Mikue", "Tecnico", "Ayudante_Tecnico", "Bata", 250000, 250000, "2026-01-01"),
    ("B016", "Robustiano Ateba Mbomio", "Tecnico", "Ayudante_Tecnico", "Bata", 250000, 250000, "2026-01-01"),
    ("B017", "Lorenzo Eyene Nze Onguene", "Tecnico", "Ayudante_Tecnico", "Bata", 200000, 200000, "2026-01-01"),
    ("B018", "Luis Marcelino Idjable Mbokoto", "Mecanica", "Mecanico_Primera", "Bata", 350000, 0, "2026-01-01"),
    ("B019", "Adama Kondoago", "Servicios_Generales", "Sereno", "Bata", 120000, 0, "2026-01-01"),
    ("B020", "Dodani Do Sacramento", "Servicios_Generales", "Sereno", "Bata", 200000, 0, "2026-01-01"),
    ("B021", "Asuncion Bilogo Ndong Angono", "Servicios_Generales", "Moza_Limpieza", "Bata", 150000, 150000, "2026-01-01"),
    ("B022", "Jose Mba Eyene", "Logistica", "Logistico", "Bata", 150000, 0, "2026-01-01"),
    # --- MALABO (9) ---
    ("M001", "Daniel Moreno Castillo", "Tecnico", "Tecnico_Jefe_Obra", "Malabo", 800605, 0, "2026-01-01"),
    ("M002", "Girmanesh Araya Gebresilasse", "Tecnico", "Responsable_IP", "Malabo", 3170083, 3170083, "2026-01-01"),
    ("M003", "Yudisleidy Nunez Lavastida", "Administracion", "Responsable_Administracion", "Malabo", 950000, 950000, "2026-01-01"),
    ("M004", "Lisdami Corzo Do Pico", "Administracion", "Administracion_Contable", "Malabo", 950000, 950000, "2026-01-01"),
    ("M005", "Maria Del Carmen Mangue Asumu Obono", "Administracion", "Auxiliar_Administrativo", "Malabo", 750000, 750000, "2026-01-01"),
    ("M006", "Ines Alfaro Leon", "Servicios_Generales", "Moza_Limpieza", "Malabo", 170000, 170000, "2026-01-01"),
    ("M007", "Almudena Francisca Ayetebe Owono Onguene", "Administracion", "Asistente_Administrativa", "Malabo", 100000, 100000, "2026-01-01"),
    ("M008", "Josehp Fotsing", "Tecnico", "Tecnico_Instalador", "Malabo", 450000, 0, "2026-01-01"),
    ("M009", "Mohamed Conde", "Servicios_Generales", "Sereno", "Malabo", 200000, 0, "2026-01-01"),
]

# ============================================================================
# PROVEEDORES — 14 registros
# ============================================================================
SUPPLIERS = [
    # (code, name, supplier_type, tax_id, contact_name, phone, email)
    ("PROV01", "Tradex", "gasolinera", "GQ-12345", "Pedro Mba", "+240 222 1234", "info@gasolinera.gq"),
    ("PROV02", "Gepetrol", "gasolinera", None, None, None, None),
    ("PROV03", "Total", "gasolinera", None, None, None, None),
    ("PROV04", "Ferreteria Bocoum Hibrahim Abdoul", "empresa", "7.728C-015", "Abdoulay", "00240 222 770 102", None),
    ("PROV05", "Ali Ejeij", "empresa", None, "Mohamed", "00240 222 077 077", None),
    ("PROV06", "Sosem", "empresa", None, "Pedro Galiana", "00240 222 275 559", None),
    ("PROV07", "Abayak", "empresa", None, "Raimundo", "00240 222 235 400", None),
    ("PROV08", "Ryesa", "empresa", "00797R", "Rafael", "00240 222 207 738", None),
    ("PROV09", "Fiagsa", "empresa", "02103FI-21", "Marcelo", "00240 222 471 551", None),
    ("PROV10", "Conexxia", "empresa", None, "Hussein", "00240 222 022 698", None),
    ("PROV11", "Casa Mongomo", "empresa", None, None, "00240 222 842 987", None),
    ("PROV12", "Getesa", "empresa", None, None, None, None),
    ("PROV13", "Martinez y Hermanos", "empresa", None, None, None, None),
    ("PROV14", "TMGE", "empresa", None, None, None, None),
]

# ============================================================================
# CUENTAS CORPORATIVAS — 5 registros (todas Malabo)
# ============================================================================
CORPORATE_ACCOUNTS = [
    # (bank_name, account_number, account_holder, delegacion)
    ("BGFI Bank", "50004 05120 42013247011 73", "Telecomunicaciones y Energias Renovables R2i G.E. S.L", "Malabo"),
    ("SGBGE", "GQ70 50002 00100 37153274001 47", "Telecomunicaciones y Energias Renovables R2i G.E. S.L", "Malabo"),
    ("CCEI BANK", "50001 00005 01158701001 57", "Telecomunicaciones y Energias Renovables R2i G.E. S.L", "Malabo"),
    ("ECOBANK", "50006 00001 39360008992 31", "Telecomunicaciones y Energias Renovables R2i G.E. S.L", "Malabo"),
    ("BANGE", "GQ60 50005 00012 37111542301 46", "Telecomunicaciones y Energias Renovables R2i G.E. S.L", "Malabo"),
]


def load_all():
    db = SessionLocal()
    try:
        # --- Empleados ---
        emp_created = 0
        emp_skipped = 0
        for code, name, dept, pos, deleg, gross, transfer, eff_date in EMPLOYEES:
            existing = db.query(Employee).filter(Employee.code == code).first()
            if existing:
                emp_skipped += 1
                continue
            emp = Employee(
                code=code,
                full_name=name.strip(),
                department=dept,
                position=strip_accents(pos),
                delegacion=deleg,
                salary_gross=Decimal(str(gross)),
                salary_transfer=Decimal(str(transfer)),
                salary_effective_date=date.fromisoformat(eff_date),
            )
            db.add(emp)
            emp_created += 1
        db.flush()
        print(f"✓ Empleados: {emp_created} creados, {emp_skipped} omitidos (ya existian)")

        # --- Proveedores ---
        sup_created = 0
        sup_skipped = 0
        for code, name, stype, tax_id, contact, phone, email in SUPPLIERS:
            existing = db.query(Supplier).filter(Supplier.code == code).first()
            if existing:
                sup_skipped += 1
                continue
            sup = Supplier(
                code=code,
                name=name.strip(),
                supplier_type=stype,
                tax_id=tax_id,
                contact_name=contact.strip() if contact else None,
                phone=phone.strip() if phone else None,
                email=email.strip() if email else None,
            )
            db.add(sup)
            sup_created += 1
        db.flush()
        print(f"✓ Proveedores: {sup_created} creados, {sup_skipped} omitidos (ya existian)")

        # --- Cuentas Corporativas ---
        acc_created = 0
        acc_skipped = 0
        for bank, number, holder, deleg in CORPORATE_ACCOUNTS:
            existing = db.query(CorporateAccount).filter(
                CorporateAccount.account_number == number
            ).first()
            if existing:
                acc_skipped += 1
                continue
            acc = CorporateAccount(
                bank_name=bank.strip(),
                account_number=number.strip(),
                account_holder=holder.strip(),
                delegacion=deleg,
            )
            db.add(acc)
            acc_created += 1
        db.flush()
        print(f"✓ Cuentas corporativas: {acc_created} creadas, {acc_skipped} omitidas (ya existian)")

        db.commit()
        print("\n✓ Todos los catálogos cargados correctamente.")

    except Exception as e:
        db.rollback()
        print(f"\n✗ Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    load_all()
