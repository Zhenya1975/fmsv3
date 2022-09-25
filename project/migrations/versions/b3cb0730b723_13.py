"""13

Revision ID: b3cb0730b723
Revises: 1ef0dca4b091
Create Date: 2022-09-25 08:08:42.422600

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b3cb0730b723'
down_revision = '1ef0dca4b091'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('userDB',
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('user_saved_weight_cat_id', sa.Integer(), nullable=True),
    sa.Column('user_saved_age_cat_id', sa.Integer(), nullable=True),
    sa.Column('user_saved_round_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_saved_age_cat_id'], ['agecategoriesDB.age_cat_id'], name=op.f('fk_userDB_user_saved_age_cat_id_agecategoriesDB')),
    sa.ForeignKeyConstraint(['user_saved_round_id'], ['roundsDB.round_id'], name=op.f('fk_userDB_user_saved_round_id_roundsDB')),
    sa.ForeignKeyConstraint(['user_saved_weight_cat_id'], ['weightcategoriesDB.weight_cat_id'], name=op.f('fk_userDB_user_saved_weight_cat_id_weightcategoriesDB')),
    sa.PrimaryKeyConstraint('user_id', name=op.f('pk_userDB'))
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('userDB')
    # ### end Alembic commands ###