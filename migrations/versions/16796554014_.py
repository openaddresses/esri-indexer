"""empty message

Revision ID: 16796554014
Revises: 2b08988270a4
Create Date: 2015-03-31 09:52:15.840333

"""

# revision identifiers, used by Alembic.
revision = '16796554014'
down_revision = '2b08988270a4'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('servers', sa.Column('job_id', sa.String(), nullable=True))
    op.add_column('servers', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.create_unique_constraint(None, 'servers', ['url'])
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'servers', type_='unique')
    op.drop_column('servers', 'updated_at')
    op.drop_column('servers', 'job_id')
    ### end Alembic commands ###
