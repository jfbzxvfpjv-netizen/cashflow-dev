"""
Crea proyectos, obras y vehículos nuevos en la BD.
Renombra obras de Flota de guion bajo a guion medio.
Ejecutar: docker compose exec backend python create_new_catalogs.py
"""
from app.database import SessionLocal
from app.models.catalogs import Project, Work, Vehicle

def run():
    db = SessionLocal()
    try:
        # === HELPER ===
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

        # === 1. OBRAS NUEVAS EN PROYECTO GENERAL ===
        print("\n--- Proyecto General ---")
        p_general = get_or_create_project("General")
        get_or_create_work(p_general, "General", "General")
        get_or_create_work(p_general, "Gestion_Comercial", "Gestion Comercial")
        get_or_create_work(p_general, "Telecomunicaciones", "Telecomunicaciones")

        # === 2. PROYECTO Mto_General ===
        print("\n--- Proyecto Mto_General ---")
        p_mto_gen = get_or_create_project("Mto_General", "Mantenimiento General")
        get_or_create_work(p_mto_gen, "Combustible_Grupos", "Combustible Grupos")
        get_or_create_work(p_mto_gen, "Dietas_Campo", "Dietas Campo")

        # === 3. PROYECTO CONEXXIA ===
        print("\n--- Proyecto CONEXXIA ---")
        p_conexxia = get_or_create_project("CONEXXIA")
        get_or_create_work(p_conexxia, "Mongomeyen_CONEXXIA", "Mongomeyen CONEXXIA")

        # === 4. PROYECTO Mto_CONEXXIA (vacío) ===
        print("\n--- Proyecto Mto_CONEXXIA ---")
        get_or_create_project("Mto_CONEXXIA", "Mantenimiento CONEXXIA")

        # === 5. PROYECTO R2i_Gabon ===
        print("\n--- Proyecto R2i_Gabon ---")
        p_gabon = get_or_create_project("R2i_Gabon", "R2i Gabon")
        get_or_create_work(p_gabon, "Implantacion", "Implantacion")

        # === 6. OBRAS NUEVAS EN Mto_GETESA ===
        print("\n--- Obras nuevas en Mto_GETESA ---")
        p_mto_getesa = get_or_create_project("Mto_GETESA")
        nuevas_getesa = [
            "Nsok_Nzomo_GETESA", "Oyala_Arg_GETESA", "General_GETESA",
            "Oyec_Esong_GETESA", "Mongomeyen_GETESA", "Meban_GETESA",
            "Sendje_GETESA", "Mbini_GETESA", "Nvom_GETESA", "Mesama_GETESA"
        ]
        for code in nuevas_getesa:
            name = code.replace('_', ' ')
            get_or_create_work(p_mto_getesa, code, name)

        # === 7. OBRAS NUEVAS EN FLOTA ===
        print("\n--- Obras nuevas en Flota ---")
        p_flota = get_or_create_project("Flota")
        get_or_create_work(p_flota, "General", "General")
        get_or_create_work(p_flota, "KN-493-AC", "KN-493-AC")
        get_or_create_work(p_flota, "WN-934-AH", "WN-934-AH")

        # === 8. VEHÍCULOS NUEVOS ===
        print("\n--- Vehículos nuevos ---")
        for plate in ["KN-493-AC", "WN-934-AH"]:
            existing = db.query(Vehicle).filter(Vehicle.plate == plate).first()
            if not existing:
                v = Vehicle(plate=plate, brand=None, model=None, year=None, delegacion="Bata")
                db.add(v)
                print(f"  + Vehículo: {plate}")
            else:
                print(f"  = Vehículo existente: {plate}")

        # === 9. RENOMBRAR OBRAS DE FLOTA: guion bajo → guion medio ===
        print("\n--- Renombrar obras Flota (guion bajo → guion medio) ---")
        flota_works = db.query(Work).filter(Work.project_id == p_flota.id).all()
        renamed = 0
        for w in flota_works:
            if w.code == "General":
                continue
            new_code = w.code.replace('_', '-')
            new_name = new_code  # nombre = matrícula con guion medio
            if new_code != w.code:
                old = w.code
                w.code = new_code
                w.name = new_name
                renamed += 1
                print(f"    {old} → {new_code}")
        print(f"  {renamed} obras renombradas")

        db.commit()
        print("\n✓ Todos los cambios aplicados correctamente.")

    except Exception as e:
        db.rollback()
        print(f"\n✗ Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    run()
