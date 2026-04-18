"""
Crea catálogos nuevos para Malabo en la BD.
Ejecutar: docker compose exec backend python create_malabo_catalogs.py
"""
from app.database import SessionLocal
from app.models.catalogs import Project, Work, Vehicle, TransactionCategory, TransactionSubcategory

def run():
    db = SessionLocal()
    try:
        def get_or_create_project(code, name=None):
            p = db.query(Project).filter(Project.code == code).first()
            if not p:
                p = Project(code=code, name=name or code)
                db.add(p)
                db.flush()
                print(f"  + Proyecto: {code}")
            else:
                print(f"  = Proyecto existente: {code}")
            return p

        def get_or_create_work(project, code, name=None):
            w = db.query(Work).filter(
                Work.project_id == project.id, Work.code == code
            ).first()
            if not w:
                w = Work(project_id=project.id, code=code, name=name or code.replace('_', ' '))
                db.add(w)
                db.flush()
                print(f"    + Obra: {code}")
            else:
                print(f"    = Obra existente: {code}")
            return w

        # === OBRAS NUEVAS EN GENERAL ===
        print("\n--- General ---")
        p_general = get_or_create_project("General")
        get_or_create_work(p_general, "Cobros_Facturas", "Cobros Facturas")
        get_or_create_work(p_general, "Vivienda_Daniel_Malabo", "Vivienda Daniel Malabo")
        get_or_create_work(p_general, "Vivienda_Fotsing_Malabo", "Vivienda Fotsing Malabo")

        # === OBRAS NUEVAS EN GETESA ===
        print("\n--- GETESA ---")
        p_getesa = get_or_create_project("GETESA")
        get_or_create_work(p_getesa, "Getesa_Central_Sala_Energia_2", "Getesa Central Sala Energia 2")
        get_or_create_work(p_getesa, "Obra_Injuly", "Obra Injuly")

        # === OBRA NUEVA EN SOCIOS ===
        print("\n--- Socios ---")
        p_socios = get_or_create_project("Socios")
        get_or_create_work(p_socios, "Obra_Buena_Esperanza", "Obra Buena Esperanza")

        # === OBRAS Y VEHÍCULOS NUEVOS EN FLOTA ===
        print("\n--- Flota ---")
        p_flota = get_or_create_project("Flota")
        malabo_vehicles = ["WN-524-AO", "WN-699-AG", "LT-128-AI", "LT-582-S"]
        for plate in malabo_vehicles:
            get_or_create_work(p_flota, plate, plate)
            existing = db.query(Vehicle).filter(Vehicle.plate == plate).first()
            if not existing:
                v = Vehicle(plate=plate, brand=None, model=None, year=None, delegacion="Malabo")
                db.add(v)
                print(f"    + Vehículo: {plate}")
            else:
                print(f"    = Vehículo existente: {plate}")

        # === SUBCATEGORÍA TMGE EN COBRO_FACTURAS ===
        print("\n--- Subcategoría TMGE ---")
        cat_cobro = db.query(TransactionCategory).filter(
            TransactionCategory.name == "Cobro_Facturas"
        ).first()
        if cat_cobro:
            existing = db.query(TransactionSubcategory).filter(
                TransactionSubcategory.category_id == cat_cobro.id,
                TransactionSubcategory.name == "TMGE"
            ).first()
            if not existing:
                sub = TransactionSubcategory(category_id=cat_cobro.id, name="TMGE")
                db.add(sub)
                print(f"  + Subcategoría: TMGE en Cobro_Facturas")
            else:
                print(f"  = Subcategoría existente: TMGE")
        else:
            print("  ✗ ERROR: Categoría Cobro_Facturas no encontrada")

        db.commit()
        print("\n✓ Catálogos Malabo creados correctamente.")

    except Exception as e:
        db.rollback()
        print(f"\n✗ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run()
