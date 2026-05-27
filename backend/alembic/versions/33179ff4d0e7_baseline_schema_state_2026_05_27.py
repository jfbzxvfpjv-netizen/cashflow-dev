"""baseline schema state 2026-05-27

Revision ID: 33179ff4d0e7
Revises: 
Create Date: 2026-05-27 16:09:07.227084

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '33179ff4d0e7'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Baseline: crea todas las tablas si la BD esta vacia.
    Si la BD ya tiene tablas (caso de BDs existentes stampeadas), NO hace nada.
    Esto permite desplegar en BD nueva con 'alembic upgrade head' y obtener
    el estado completo del schema (38 tablas) hasta M10b-v3.
    """
    import os
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    existing_tables = inspector.get_table_names()

    # Si ya hay tablas distintas de alembic_version, asumimos BD existente stampeada
    business_tables = [t for t in existing_tables if t != 'alembic_version']
    if business_tables:
        print(f"BD ya tiene {len(business_tables)} tablas; no se aplica init_full_schema.sql")
        return

    # BD vacia: ejecutar init_full_schema.sql via conexion raw
    sql_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'init_full_schema.sql')
    with open(sql_path, 'r') as f:
        sql = f.read()
    raw_conn = conn.connection.dbapi_connection
    cur = raw_conn.cursor()
    try:
        cur.execute(sql)
        print("Schema inicial aplicado desde init_full_schema.sql")
    except Exception as e:
        print(f"ERROR ejecutando init_full_schema: {type(e).__name__}: {e}")
        raise
    finally:
        cur.close()


def downgrade() -> None:
    """No procede: baseline no es reversible."""
    pass
