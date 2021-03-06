"""Remove unique chat ID

Revision ID: f336f81e84dc
Revises: 1fb4a98e3a4d
Create Date: 2022-02-27 13:57:46.355752

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f336f81e84dc'
down_revision = '1fb4a98e3a4d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('games_chat_id_key', 'games', type_='unique')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_unique_constraint('games_chat_id_key', 'games', ['chat_id'])
    # ### end Alembic commands ###
