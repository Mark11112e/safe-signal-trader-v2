"""Initial foundation schema placeholder
Revision ID: 001
Revises:
"""
from typing import Sequence, Union
revision = "001"
down_revision = None
branch_labels = None
depends_on = None
def upgrade() -> None:
    # Tables defined in infrastructure.db.models – use alembic revision --autogenerate
    pass
def downgrade() -> None:
    pass
