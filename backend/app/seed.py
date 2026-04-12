"""
Seed de datos iniciales — Crea tablas, usuarios y catálogos.
Ejecutar: docker compose exec backend python -m app.seed
"""

from app.database import engine, SessionLocal, Base
from app.models.user import User
from app.models.audit_log import AuditLog  # noqa: F401
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)


def seed_users():
    """Crea los 5 usuarios del sistema si la tabla está vacía."""
    db = SessionLocal()
    try:
        count = db.query(User).count()
        if count > 0:
            print(f"  La tabla users ya tiene {count} registros. Seed de usuarios omitido.")
            return

        users = [
            User(username="admin", password_hash=pwd_context.hash("Admin1234!"),
                 full_name="Administrador del Sistema", role="admin", delegacion="Ambas"),
            User(username="contable1", password_hash=pwd_context.hash("Contable1234!"),
                 full_name="Contable Principal", role="contable", delegacion="Ambas"),
            User(username="gestor_bata", password_hash=pwd_context.hash("Gestor1234!"),
                 full_name="Gestor de Caja Bata", role="gestor", delegacion="Bata"),
            User(username="gestor_malabo", password_hash=pwd_context.hash("Gestor1234!"),
                 full_name="Gestor de Caja Malabo", role="gestor", delegacion="Malabo"),
            User(username="consulta1", password_hash=pwd_context.hash("Consulta1234!"),
                 full_name="Usuario de Consulta", role="consulta", delegacion="Ambas"),
        ]

        db.add_all(users)
        db.commit()
        print(f"✓ {len(users)} usuarios creados:")
        for u in users:
            print(f"    {u.username} / {u.role} / {u.delegacion}")
    finally:
        db.close()


def run_seed():
    """Ejecuta el seed completo: tablas, usuarios y catálogos."""
    Base.metadata.create_all(bind=engine)
    print("✓ Tablas creadas / verificadas.")

    # M1/M3 — Usuarios
    seed_users()

    # M4 — Catálogos
    from app.seed_catalogs import seed_catalogs_sync
    seed_catalogs_sync()


if __name__ == "__main__":
    run_seed()
