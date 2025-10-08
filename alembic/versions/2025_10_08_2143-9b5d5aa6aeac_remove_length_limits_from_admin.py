"""remove_length_limits_from_admin

Revision ID: 9b5d5aa6aeac
Revises: 03e647da3dc6
Create Date: 2025-10-08 21:43:32.140940

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9b5d5aa6aeac'
down_revision: Union[str, Sequence[str], None] = '03e647da3dc6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('admins', 'login',
               existing_type=sa.String(32),
               type_=sa.String(),
               existing_nullable=False)
    op.alter_column('admins', 'password',
               existing_type=sa.String(32),
               type_=sa.String(),
               existing_nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('admins', 'password',
               existing_type=sa.String(),
               type_=sa.String(32),
               existing_nullable=False)
    op.alter_column('admins', 'login',
               existing_type=sa.String(),
               type_=sa.String(32),
               existing_nullable=False)
