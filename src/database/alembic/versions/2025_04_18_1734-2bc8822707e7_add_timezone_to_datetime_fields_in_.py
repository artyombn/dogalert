"""Add timezone to datetime fields in Report model

Revision ID: 2bc8822707e7
Revises: 46c1d7c38e5d
Create Date: 2025-04-18 17:34:41.475083

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2bc8822707e7'
down_revision: Union[str, None] = '46c1d7c38e5d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("""
            UPDATE reports SET 
                created_at = created_at AT TIME ZONE 'UTC',
                updated_at = updated_at AT TIME ZONE 'UTC';
        """)
    op.alter_column('reports', 'created_at',
                    existing_type=postgresql.TIMESTAMP(),
                    type_=sa.DateTime(timezone=True),
                    existing_nullable=False,
                    existing_server_default=sa.text('now()'))
    op.alter_column('reports', 'updated_at',
                    existing_type=postgresql.TIMESTAMP(),
                    type_=sa.DateTime(timezone=True),
                    existing_nullable=False,
                    existing_server_default=sa.text('now()'))
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('reports', 'updated_at',
                    existing_type=sa.DateTime(timezone=True),
                    type_=postgresql.TIMESTAMP(),
                    existing_nullable=False,
                    existing_server_default=sa.text('now()'))
    op.alter_column('reports', 'created_at',
                    existing_type=sa.DateTime(timezone=True),
                    type_=postgresql.TIMESTAMP(),
                    existing_nullable=False,
                    existing_server_default=sa.text('now()'))
    # ### end Alembic commands ###
