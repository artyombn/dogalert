"""Initial migration

Revision ID: 4c196dfcf07e
Revises: 
Create Date: 2025-04-01 01:28:14.162755

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from src.database.models.report import ReportStatus

# revision identifiers, used by Alembic.
revision: str = '4c196dfcf07e'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('pets',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('breed', sa.String(), nullable=True),
    sa.Column('age', sa.Integer(), nullable=True),
    sa.Column('color', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    sa.Column('last_vaccination', sa.DateTime(), nullable=True),
    sa.Column('next_vaccination', sa.DateTime(), nullable=True),
    sa.Column('last_parasite_treatment', sa.DateTime(), nullable=True),
    sa.Column('next_parasite_treatment', sa.DateTime(), nullable=True),
    sa.Column('last_fleas_ticks_treatment', sa.DateTime(), nullable=True),
    sa.Column('next_fleas_ticks_treatment', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pets_breed'), 'pets', ['breed'], unique=False)
    op.create_index(op.f('ix_pets_name'), 'pets', ['name'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('telegram_id', sa.BigInteger(), nullable=False),
    sa.Column('username', sa.String(), nullable=True),
    sa.Column('first_name', sa.String(), nullable=True),
    sa.Column('last_name', sa.String(), nullable=True),
    sa.Column('phone', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    sa.Column('region', sa.String(), nullable=True),
    sa.Column('geo_latitude', sa.Float(), nullable=True),
    sa.Column('geo_longitude', sa.Float(), nullable=True),
    sa.Column('agreement', sa.Boolean(), nullable=False, server_default=sa.false()),
    sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default=sa.false()),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_phone'), 'users', ['phone'], unique=False)
    op.create_index(op.f('ix_users_region'), 'users', ['region'], unique=False)
    op.create_index(op.f('ix_users_telegram_id'), 'users', ['telegram_id'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=False)
    op.create_table('petphotos',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('url', sa.String(), nullable=False),
    sa.Column('pet_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['pet_id'], ['pets.id'], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('reports',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('content', sa.String(), nullable=False),
    sa.Column('status', sa.String(), nullable=False, server_default=ReportStatus.ACTIVE.value),
    sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
    sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
    sa.Column('location', sa.String(), nullable=True),
    sa.Column('region', sa.String(), nullable=True),
    sa.Column('search_radius', sa.Integer(), nullable=False, server_default="5000"),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('pet_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['pet_id'], ['pets.id'], ondelete="CASCADE"),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_pet_id'), 'reports', ['pet_id'], unique=False)
    op.create_index(op.f('ix_reports_region'), 'reports', ['region'], unique=False)
    op.create_index(op.f('ix_reports_title'), 'reports', ['title'], unique=False)
    op.create_index(op.f('ix_reports_user_id'), 'reports', ['user_id'], unique=False)
    op.create_table('user_pet_association',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('pet_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['pet_id'], ['pets.id'], ondelete="CASCADE"),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint('user_id', 'pet_id')
    )
    op.create_table('reportphotos',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('url', sa.String(), nullable=False),
    sa.Column('report_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ondelete="CASCADE"),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('reportphotos')
    op.drop_table('user_pet_association')
    op.drop_index(op.f('ix_reports_user_id'), table_name='reports')
    op.drop_index(op.f('ix_reports_title'), table_name='reports')
    op.drop_index(op.f('ix_reports_region'), table_name='reports')
    op.drop_index(op.f('ix_reports_pet_id'), table_name='reports')
    op.drop_table('reports')
    op.drop_table('petphotos')
    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_index(op.f('ix_users_telegram_id'), table_name='users')
    op.drop_index(op.f('ix_users_region'), table_name='users')
    op.drop_index(op.f('ix_users_phone'), table_name='users')
    op.drop_table('users')
    op.drop_index(op.f('ix_pets_name'), table_name='pets')
    op.drop_index(op.f('ix_pets_breed'), table_name='pets')
    op.drop_table('pets')
    # ### end Alembic commands ###
