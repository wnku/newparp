"""Add LogMarker

Revision ID: 418d40c91e2e
Revises: 8c6a92703ad
Create Date: 2016-03-09 23:15:48.954420

"""

# revision identifiers, used by Alembic.
revision = '418d40c91e2e'
down_revision = '8c6a92703ad'
branch_labels = None
depends_on = None

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.create_table('log_markers',
    sa.Column('chat_id', sa.Integer(), nullable=False),
    sa.Column('type', sa.Enum(u'page_with_system_messages', u'page_without_system_messages', name='log_markers_type'), nullable=False),
    sa.Column('number', sa.Integer(), nullable=False, autoincrement=False),
    sa.Column('message_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['chat_id'], ['chats.id'], ),
    sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ),
    sa.PrimaryKeyConstraint('chat_id', 'type', 'number')
    )
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('log_markers')
    ### end Alembic commands ###