"""add timezone to datetime columns

Revision ID: 7ba0dc36499c
Revises: 53b24a19da86
Create Date: 2026-09-14 15:14:18.310920

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '7ba0dc36499c'
down_revision: Union[str, Sequence[str], None] = '53b24a19da86'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column('failed_events', 'failed_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using="failed_at AT TIME ZONE 'UTC'")
    op.alter_column('linked_commits', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using="created_at AT TIME ZONE 'UTC'")
    op.alter_column('notifications', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using="created_at AT TIME ZONE 'UTC'")
    op.alter_column('repo_links', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using="created_at AT TIME ZONE 'UTC'")
    op.alter_column('team_integrations', 'created_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using="created_at AT TIME ZONE 'UTC'")
    op.alter_column('team_integrations', 'updated_at',
               existing_type=postgresql.TIMESTAMP(),
               type_=sa.DateTime(timezone=True),
               existing_nullable=False,
               postgresql_using="updated_at AT TIME ZONE 'UTC'")


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column('team_integrations', 'updated_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=False,
               postgresql_using="updated_at AT TIME ZONE 'UTC'")
    op.alter_column('team_integrations', 'created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=False,
               postgresql_using="created_at AT TIME ZONE 'UTC'")
    op.alter_column('repo_links', 'created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=False,
               postgresql_using="created_at AT TIME ZONE 'UTC'")
    op.alter_column('notifications', 'created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=False,
               postgresql_using="created_at AT TIME ZONE 'UTC'")
    op.alter_column('linked_commits', 'created_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=False,
               postgresql_using="created_at AT TIME ZONE 'UTC'")
    op.alter_column('failed_events', 'failed_at',
               existing_type=sa.DateTime(timezone=True),
               type_=postgresql.TIMESTAMP(),
               existing_nullable=False,
               postgresql_using="failed_at AT TIME ZONE 'UTC'")
