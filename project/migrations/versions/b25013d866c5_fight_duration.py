"""fight duration

Revision ID: b25013d866c5
Revises: 2de4abb0046a
Create Date: 2022-09-14 14:04:19.271135

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b25013d866c5'
down_revision = '2de4abb0046a'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('competitionsDB', schema=None) as batch_op:
        batch_op.add_column(sa.Column('fight_duration', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('competitionsDB', schema=None) as batch_op:
        batch_op.drop_column('fight_duration')

    # ### end Alembic commands ###
