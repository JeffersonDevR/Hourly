"""`historial_cambio.deshecho`: separa la pila de deshacer de la de rehacer.

Deshacer marca la entrada como deshecha en vez de borrarla, así rehacer sabe qué
reaplicar. Cualquier edición nueva borra las entradas deshechas: el redo no sobrevive
a un cambio distinto (GAPS.md).

Revision ID: 9c1f0a7d2b3e
Revises: 773f1b7a928a
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "9c1f0a7d2b3e"
down_revision: str | None = "773f1b7a928a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("historial_cambio") as batch:
        batch.add_column(
            sa.Column("deshecho", sa.Boolean(), nullable=False, server_default=sa.false())
        )


def downgrade() -> None:
    with op.batch_alter_table("historial_cambio") as batch:
        batch.drop_column("deshecho")
