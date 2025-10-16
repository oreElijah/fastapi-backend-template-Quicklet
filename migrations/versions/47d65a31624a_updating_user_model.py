"""Updating user model

Revision ID: 47d65a31624a
Revises: de6671ae9781
Create Date: 2025-09-27 00:10:32.741199

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '47d65a31624a'
down_revision: Union[str, Sequence[str], None] = 'de6671ae9781'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
