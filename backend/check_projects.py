from app.database import SessionLocal
from app.models.catalogs import Project, Work

db = SessionLocal()
try:
    projects = db.query(Project).order_by(Project.name).all()
    print(f"=== {len(projects)} proyectos en BD ===\n")
    for p in projects:
        works = db.query(Work).filter(Work.project_id == p.id).order_by(Work.name).all()
        print(f"{p.name}  (code: {p.code}, {len(works)} obras)")
        for w in works:
            print(f"  - {w.name}  [code: {w.code}]")
        print()
finally:
    db.close()
