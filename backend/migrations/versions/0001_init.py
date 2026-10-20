"""Initial schema: users, projects, conversations, messages, model providers, agent runs.

Revision ID: 0001_init
Revises:
Create Date: 2026-10-19
"""
from alembic import op

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    from app.models import Base
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    from app.models import Base
    Base.metadata.drop_all(bind=op.get_bind())
