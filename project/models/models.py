from extensions import extensions
from datetime import datetime, date

db = extensions.db


class ParticipantsDB(db.Model):
    participant_id = db.Column(db.Integer, primary_key=True)
    participant_first_name = db.Column(db.String)
    participant_last_name = db.Column(db.String)
    registration_participant = db.relationship('RegistrationsDB', backref='registration_participant')
    fighter_image = db.Column(db.String)
    birthday = db.Column(db.Date, default=datetime.utcnow)
    participant_city = db.Column(db.String)
    active_status = db.Column(db.Boolean, default=False)


class CompetitionsDB(db.Model):
    competition_id = db.Column(db.Integer, primary_key=True)
    competition_name = db.Column(db.String)
    competition_date_start = db.Column(db.Date, default=datetime.utcnow)
    competition_date_finish = db.Column(db.Date, default=datetime.utcnow)
    competition_city = db.Column(db.String)
    fight_duration = db.Column(db.Integer, default=120)
    added_time = db.Column(db.Integer, default=60)
    fights = db.relationship('FightsDB', backref='competition')
    registration_comp = db.relationship('RegistrationsDB', backref='registration_comp')


class RegistrationsDB(db.Model):
    reg_id = db.Column(db.Integer, primary_key=True)
    weight_value = db.Column(db.Float)
    participant_id = db.Column(db.Integer, db.ForeignKey('participantsDB.participant_id'))
    competition_id = db.Column(db.Integer, db.ForeignKey('competitionsDB.competition_id'))
    weight_cat_id = db.Column(db.Integer, db.ForeignKey('weightcategoriesDB.weight_cat_id'))
    age_value = db.Column(db.Float)
    age_cat_id = db.Column(db.Integer, db.ForeignKey('agecategoriesDB.age_cat_id'))
    activity_status = db.Column(db.Integer, default=1)
    red_fighter = db.relationship('FightsDB', backref='red_fighter', foreign_keys="[FightsDB.red_fighter_id]")
    blue_fighter = db.relationship('FightsDB', backref='blue_fighter', foreign_keys="[FightsDB.blue_fighter_id]")
    winner_reg = db.relationship('FightsDB', backref='winner_reg', foreign_keys="[FightsDB.fight_winner_id]")
    backlog_reg = db.relationship('BacklogDB', backref='backlog_reg')
    red_candidate = db.relationship('FightcandidateDB', backref='red_candidate', foreign_keys="[FightcandidateDB.red_candidate_reg_id]")
    blue_candidate = db.relationship('FightcandidateDB', backref='blue_candidate', foreign_keys="[FightcandidateDB.blue_candidate_reg_id]")



class FightsDB(db.Model):
    fight_id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitionsDB.competition_id'))
    round_number = db.Column(db.Integer, db.ForeignKey('roundsDB.round_id'))
    red_fighter_id = db.Column(db.Integer, db.ForeignKey('registrationsDB.reg_id'))
    blue_fighter_id = db.Column(db.Integer, db.ForeignKey('registrationsDB.reg_id'))
    fight_winner_id = db.Column(db.Integer, db.ForeignKey('registrationsDB.reg_id'))
    tatami_id = db.Column(db.Integer, db.ForeignKey('tatamiDB.tatami_id'))
    fight_status = db.Column(db.Integer, default=0)  # 0 - не начат, 1 - в процессе, 2 - завершен
    final_status = db.Column(db.String, default='continue')
    queue_fight = db.relationship('QueueDB', backref='queue_fight')


class BacklogDB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reg_id = db.Column(db.Integer, db.ForeignKey('registrationsDB.reg_id'))
    competition_id = db.Column(db.Integer, db.ForeignKey('competitionsDB.competition_id'))
    round_id = db.Column(db.Integer, db.ForeignKey('roundsDB.round_id'))


class WeightcategoriesDB(db.Model):
    """Модель для весовых категорий"""
    weight_cat_id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitionsDB.competition_id'))
    sort_index = db.Column(db.Integer)
    weight_category_name = db.Column(db.String)
    weight_category_start = db.Column(db.Integer)
    weight_category_finish = db.Column(db.Integer)
    registration = db.relationship('RegistrationsDB', backref='registration')


class AgecategoriesDB(db.Model):
    """Модель для возрастных категорий"""
    age_cat_id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitionsDB.competition_id'))
    sort_index = db.Column(db.Integer)
    age_category_name = db.Column(db.String)
    age_category_start = db.Column(db.Integer)
    age_category_finish = db.Column(db.Integer)
    registration_age_cat = db.relationship('RegistrationsDB', backref='registration_age_cat')
    # fights = db.relationship('FightsDB', backref = 'age_category_backref')


class RoundsDB(db.Model):
    """Модель для кругов"""
    round_id = db.Column(db.Integer, primary_key=True)
    round_name = db.Column(db.String)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitionsDB.competition_id'))
    weight_cat_id = db.Column(db.Integer, db.ForeignKey('weightcategoriesDB.weight_cat_id'))
    age_cat_id = db.Column(db.Integer, db.ForeignKey('agecategoriesDB.age_cat_id'))



class FightcandidateDB(db.Model):
    """Модель для кругов"""
    id = db.Column(db.Integer, primary_key=True)
    round_id = db.Column(db.Integer, db.ForeignKey('roundsDB.round_id'))
    red_candidate_reg_id = db.Column(db.Integer, db.ForeignKey('registrationsDB.reg_id'))
    blue_candidate_reg_id = db.Column(db.Integer, db.ForeignKey('registrationsDB.reg_id'))
    

class TatamiDB(db.Model):
    """Модель для татами"""
    tatami_id = db.Column(db.Integer, primary_key=True)
    tatami_name = db.Column(db.String)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitionsDB.competition_id'))
    fight_tatami = db.relationship('FightsDB', backref='fight_tatami')

class QueueDB(db.Model):
    """Модель для очередей"""
    queue_id = db.Column(db.Integer, primary_key=True)
    tatami_id = db.Column(db.Integer, db.ForeignKey('tatamiDB.tatami_id'))
    fight_id = db.Column(db.Integer, db.ForeignKey('fightsDB.fight_id'))
    queue_sort_index = db.Column(db.Integer)
