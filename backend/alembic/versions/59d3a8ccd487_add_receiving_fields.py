"""add_receiving_fields

Revision ID: 59d3a8ccd487
Revises: 73e8633732cc
Create Date: 2026-10-01 00:23:05.934581

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '59d3a8ccd487'
down_revision: Union[str, None] = '73e8633732cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
