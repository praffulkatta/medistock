"""Require non-negative batch prices.

Revision ID: 20261002_batch_prices
Revises: 20261001_schema
"""
from alembic import op

revision = "20261002_batch_prices"
down_revision = "20261001_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_check_constraint(
        "check_batch_cost_nonnegative", "medicine_batches", "cost_price >= 0"
    )
    op.create_check_constraint(
        "check_batch_price_nonnegative", "medicine_batches", "selling_price >= 0"
    )


def downgrade() -> None:
    op.drop_constraint("check_batch_price_nonnegative", "medicine_batches", type_="check")
    op.drop_constraint("check_batch_cost_nonnegative", "medicine_batches", type_="check")
