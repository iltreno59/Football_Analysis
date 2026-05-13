"""Add nullable user_login to report

Revision ID: f2a8b1c9d0e1
Revises: e3119ec568cd
Create Date: 2026-05-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f2a8b1c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e3119ec568cd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("report", sa.Column("user_login", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("report", "user_login")
