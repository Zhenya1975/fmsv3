"""init

Revision ID: 48750827249e
Revises: 9cbacce19b51
Create Date: 2022-08-16 08:21:07.432861

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '48750827249e'
down_revision = '9cbacce19b51'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('participantsDB', schema=None) as batch_op:
        batch_op.alter_column('active_status',
               existing_type=sa.INTEGER(),
               type_=sa.Boolean(),
               existing_nullable=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('participantsDB', schema=None) as batch_op:
        batch_op.alter_column('active_status',
               existing_type=sa.Boolean(),
               type_=sa.INTEGER(),
               existing_nullable=True)

    # ### end Alembic commands ###