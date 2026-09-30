"""update_medicine_model

Revision ID: 73e8633732cc
Revises: 52a055cd4ddb
Create Date: 2026-10-01 00:13:22.768931

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '73e8633732cc'
down_revision: Union[str, None] = '52a055cd4ddb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
