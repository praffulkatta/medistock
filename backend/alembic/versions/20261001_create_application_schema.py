"""Create the application schema for the first deployed database.

Revision ID: 20261001_schema
Revises: 59d3a8ccd487
"""
from alembic import op

from app.models import Base  # noqa: E402,F401

revision = "20261001_schema"
down_revision = "59d3a8ccd487"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # pg_trgm enables indexed partial, case-insensitive catalog searches.
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())
