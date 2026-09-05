"""enforce one active cart per user and shop

Revision ID: 20260905_0002
Revises: 20260905_0001
"""

from alembic import op
import sqlalchemy as sa

revision = "20260905_0002"
down_revision = "20260905_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "uq_active_cart_user_shop",
        "carts",
        ["user_id", "shop_id"],
        unique=True,
        postgresql_where=sa.text("status = 'ACTIVE'"),
        sqlite_where=sa.text("status = 'ACTIVE'"),
    )


def downgrade() -> None:
    op.drop_index("uq_active_cart_user_shop", table_name="carts")
