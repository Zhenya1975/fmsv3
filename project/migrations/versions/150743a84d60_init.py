"""init

Revision ID: 150743a84d60
Revises: 
Create Date: 2022-09-19 07:06:06.032871

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '150743a84d60'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('competitionsDB',
    sa.Column('competition_id', sa.Integer(), nullable=False),
    sa.Column('competition_name', sa.String(), nullable=True),
    sa.Column('competition_date_start', sa.Date(), nullable=True),
    sa.Column('competition_date_finish', sa.Date(), nullable=True),
    sa.Column('competition_city', sa.String(), nullable=True),
    sa.Column('fight_duration', sa.Integer(), nullable=True),
    sa.Column('added_time', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('competition_id', name=op.f('pk_competitionsDB'))
    )
    op.create_table('participantsDB',
    sa.Column('participant_id', sa.Integer(), nullable=False),
    sa.Column('participant_first_name', sa.String(), nullable=True),
    sa.Column('participant_last_name', sa.String(), nullable=True),
    sa.Column('fighter_image', sa.String(), nullable=True),
    sa.Column('birthday', sa.Date(), nullable=True),
    sa.Column('participant_city', sa.String(), nullable=True),
    sa.Column('active_status', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('participant_id', name=op.f('pk_participantsDB'))
    )
    op.create_table('agecategoriesDB',
    sa.Column('age_cat_id', sa.Integer(), nullable=False),
    sa.Column('competition_id', sa.Integer(), nullable=True),
    sa.Column('sort_index', sa.Integer(), nullable=True),
    sa.Column('age_category_name', sa.String(), nullable=True),
    sa.Column('age_category_start', sa.Integer(), nullable=True),
    sa.Column('age_category_finish', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['competition_id'], ['competitionsDB.competition_id'], name=op.f('fk_agecategoriesDB_competition_id_competitionsDB')),
    sa.PrimaryKeyConstraint('age_cat_id', name=op.f('pk_agecategoriesDB'))
    )
    op.create_table('tatamiDB',
    sa.Column('tatami_id', sa.Integer(), nullable=False),
    sa.Column('tatami_name', sa.String(), nullable=True),
    sa.Column('competition_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['competition_id'], ['competitionsDB.competition_id'], name=op.f('fk_tatamiDB_competition_id_competitionsDB')),
    sa.PrimaryKeyConstraint('tatami_id', name=op.f('pk_tatamiDB'))
    )
    op.create_table('weightcategoriesDB',
    sa.Column('weight_cat_id', sa.Integer(), nullable=False),
    sa.Column('competition_id', sa.Integer(), nullable=True),
    sa.Column('sort_index', sa.Integer(), nullable=True),
    sa.Column('weight_category_name', sa.String(), nullable=True),
    sa.Column('weight_category_start', sa.Integer(), nullable=True),
    sa.Column('weight_category_finish', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['competition_id'], ['competitionsDB.competition_id'], name=op.f('fk_weightcategoriesDB_competition_id_competitionsDB')),
    sa.PrimaryKeyConstraint('weight_cat_id', name=op.f('pk_weightcategoriesDB'))
    )
    op.create_table('registrationsDB',
    sa.Column('reg_id', sa.Integer(), nullable=False),
    sa.Column('weight_value', sa.Float(), nullable=True),
    sa.Column('participant_id', sa.Integer(), nullable=True),
    sa.Column('competition_id', sa.Integer(), nullable=True),
    sa.Column('weight_cat_id', sa.Integer(), nullable=True),
    sa.Column('age_value', sa.Float(), nullable=True),
    sa.Column('age_cat_id', sa.Integer(), nullable=True),
    sa.Column('activity_status', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['age_cat_id'], ['agecategoriesDB.age_cat_id'], name=op.f('fk_registrationsDB_age_cat_id_agecategoriesDB')),
    sa.ForeignKeyConstraint(['competition_id'], ['competitionsDB.competition_id'], name=op.f('fk_registrationsDB_competition_id_competitionsDB')),
    sa.ForeignKeyConstraint(['participant_id'], ['participantsDB.participant_id'], name=op.f('fk_registrationsDB_participant_id_participantsDB')),
    sa.ForeignKeyConstraint(['weight_cat_id'], ['weightcategoriesDB.weight_cat_id'], name=op.f('fk_registrationsDB_weight_cat_id_weightcategoriesDB')),
    sa.PrimaryKeyConstraint('reg_id', name=op.f('pk_registrationsDB'))
    )
    op.create_table('roundsDB',
    sa.Column('round_id', sa.Integer(), nullable=False),
    sa.Column('round_name', sa.String(), nullable=True),
    sa.Column('competition_id', sa.Integer(), nullable=True),
    sa.Column('weight_cat_id', sa.Integer(), nullable=True),
    sa.Column('age_cat_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['age_cat_id'], ['agecategoriesDB.age_cat_id'], name=op.f('fk_roundsDB_age_cat_id_agecategoriesDB')),
    sa.ForeignKeyConstraint(['competition_id'], ['competitionsDB.competition_id'], name=op.f('fk_roundsDB_competition_id_competitionsDB')),
    sa.ForeignKeyConstraint(['weight_cat_id'], ['weightcategoriesDB.weight_cat_id'], name=op.f('fk_roundsDB_weight_cat_id_weightcategoriesDB')),
    sa.PrimaryKeyConstraint('round_id', name=op.f('pk_roundsDB'))
    )
    op.create_table('backlogDB',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('reg_id', sa.Integer(), nullable=True),
    sa.Column('competition_id', sa.Integer(), nullable=True),
    sa.Column('round_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['competition_id'], ['competitionsDB.competition_id'], name=op.f('fk_backlogDB_competition_id_competitionsDB')),
    sa.ForeignKeyConstraint(['reg_id'], ['registrationsDB.reg_id'], name=op.f('fk_backlogDB_reg_id_registrationsDB')),
    sa.ForeignKeyConstraint(['round_id'], ['roundsDB.round_id'], name=op.f('fk_backlogDB_round_id_roundsDB')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_backlogDB'))
    )
    op.create_table('fightcandidateDB',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('round_id', sa.Integer(), nullable=True),
    sa.Column('red_candidate_reg_id', sa.Integer(), nullable=True),
    sa.Column('blue_candidate_reg_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['blue_candidate_reg_id'], ['registrationsDB.reg_id'], name=op.f('fk_fightcandidateDB_blue_candidate_reg_id_registrationsDB')),
    sa.ForeignKeyConstraint(['red_candidate_reg_id'], ['registrationsDB.reg_id'], name=op.f('fk_fightcandidateDB_red_candidate_reg_id_registrationsDB')),
    sa.ForeignKeyConstraint(['round_id'], ['roundsDB.round_id'], name=op.f('fk_fightcandidateDB_round_id_roundsDB')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_fightcandidateDB'))
    )
    op.create_table('fightsDB',
    sa.Column('fight_id', sa.Integer(), nullable=False),
    sa.Column('competition_id', sa.Integer(), nullable=True),
    sa.Column('round_number', sa.Integer(), nullable=True),
    sa.Column('red_fighter_id', sa.Integer(), nullable=True),
    sa.Column('blue_fighter_id', sa.Integer(), nullable=True),
    sa.Column('fight_winner_id', sa.Integer(), nullable=True),
    sa.Column('tatami_id', sa.Integer(), nullable=True),
    sa.Column('fight_status', sa.Integer(), nullable=True),
    sa.Column('final_status', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['blue_fighter_id'], ['registrationsDB.reg_id'], name=op.f('fk_fightsDB_blue_fighter_id_registrationsDB')),
    sa.ForeignKeyConstraint(['competition_id'], ['competitionsDB.competition_id'], name=op.f('fk_fightsDB_competition_id_competitionsDB')),
    sa.ForeignKeyConstraint(['fight_winner_id'], ['registrationsDB.reg_id'], name=op.f('fk_fightsDB_fight_winner_id_registrationsDB')),
    sa.ForeignKeyConstraint(['red_fighter_id'], ['registrationsDB.reg_id'], name=op.f('fk_fightsDB_red_fighter_id_registrationsDB')),
    sa.ForeignKeyConstraint(['round_number'], ['roundsDB.round_id'], name=op.f('fk_fightsDB_round_number_roundsDB')),
    sa.ForeignKeyConstraint(['tatami_id'], ['tatamiDB.tatami_id'], name=op.f('fk_fightsDB_tatami_id_tatamiDB')),
    sa.PrimaryKeyConstraint('fight_id', name=op.f('pk_fightsDB'))
    )
    op.create_table('queueDB',
    sa.Column('queue_id', sa.Integer(), nullable=False),
    sa.Column('competition_id', sa.Integer(), nullable=True),
    sa.Column('tatami_id', sa.Integer(), nullable=True),
    sa.Column('fight_id', sa.Integer(), nullable=True),
    sa.Column('queue_sort_index', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['competition_id'], ['competitionsDB.competition_id'], name=op.f('fk_queueDB_competition_id_competitionsDB')),
    sa.ForeignKeyConstraint(['fight_id'], ['fightsDB.fight_id'], name=op.f('fk_queueDB_fight_id_fightsDB')),
    sa.ForeignKeyConstraint(['tatami_id'], ['tatamiDB.tatami_id'], name=op.f('fk_queueDB_tatami_id_tatamiDB')),
    sa.PrimaryKeyConstraint('queue_id', name=op.f('pk_queueDB'))
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('queueDB')
    op.drop_table('fightsDB')
    op.drop_table('fightcandidateDB')
    op.drop_table('backlogDB')
    op.drop_table('roundsDB')
    op.drop_table('registrationsDB')
    op.drop_table('weightcategoriesDB')
    op.drop_table('tatamiDB')
    op.drop_table('agecategoriesDB')
    op.drop_table('participantsDB')
    op.drop_table('competitionsDB')
    # ### end Alembic commands ###
