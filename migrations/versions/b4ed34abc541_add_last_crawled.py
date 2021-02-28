"""add last_crawled

Revision ID: b4ed34abc541
Revises: 16796554014
Create Date: 2021-02-28 14:38:44.130005

"""

# revision identifiers, used by Alembic.
revision = 'b4ed34abc541'
down_revision = '16796554014'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('servers', sa.Column('last_crawled', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('servers', 'last_crawled')
    # ### end Alembic commands ###