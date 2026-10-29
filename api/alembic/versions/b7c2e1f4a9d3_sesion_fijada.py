"""`sesion.fijada`: el pin de la grilla (D-017).

Sin pin, `generar` re-planifica todas las sesiones existentes. Con el pin, el usuario
declara qué sesiones no se tocan y el solver puede mover el resto.

Revision ID: b7c2e1f4a9d3
Revises: 9c1f0a7d2b3e
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b7c2e1f4a9d3"
down_revision: str | None = "9c1f0a7d2b3e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("sesion") as batch:
        batch.add_column(
            sa.Column("fijada", sa.Boolean(), nullable=False, server_default=sa.false())
        )


def downgrade() -> None:
    with op.batch_alter_table("sesion") as batch:
        batch.drop_column("fijada")
