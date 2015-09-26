"""Add admin_tier_id column to users.

Revision ID: 5659d2671cc8
Revises: 3bff2bf1b0ab
Create Date: 2015-09-26 22:43:46.910815

"""

# revision identifiers, used by Alembic.
revision = '5659d2671cc8'
down_revision = '3bff2bf1b0ab'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('admin_tier_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'users', 'admin_tiers', ['admin_tier_id'], ['id'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'users', type_='foreignkey')
    op.drop_column('users', 'admin_tier_id')
    ### end Alembic commands ###
