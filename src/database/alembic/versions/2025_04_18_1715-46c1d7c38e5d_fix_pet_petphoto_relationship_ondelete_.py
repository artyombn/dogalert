"""Fix Pet & PetPhoto relationship ondelete=CASCADE

Revision ID: 46c1d7c38e5d
Revises: 27148388ab47
Create Date: 2025-04-18 17:15:19.566203

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '46c1d7c38e5d'
down_revision: Union[str, None] = '27148388ab47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('petphotos_pet_id_fkey', 'petphotos', type_='foreignkey')
    op.create_foreign_key(
        'petphotos_pet_id_fkey',
        'petphotos',
        'pets',
        ['pet_id'],
        ['id'],
        ondelete='CASCADE'
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('petphotos_pet_id_fkey', 'petphotos', type_='foreignkey')
    op.create_foreign_key(
        'petphotos_pet_id_fkey',
        'petphotos',
        'pets',
        ['pet_id'],
        ['id']
    )
    # ### end Alembic commands ###
