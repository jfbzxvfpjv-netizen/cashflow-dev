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
    """Baseline: estado actual de la BD a 27/05/2026.
    NO aplica cambios. La BD ya tiene todas las tablas de Capa1+Capa2 hasta M10b-v2.
    Migraciones nuevas (incrementales) se generan a partir de esta revision.
    """
    pass


def downgrade() -> None:
    """No procede: baseline no es reversible."""
    pass
