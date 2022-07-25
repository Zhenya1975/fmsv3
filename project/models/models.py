from extensions import extensions
from datetime import datetime, date

db = extensions.db


class ParticipantsDB(db.Model):
    participant_id = db.Column(db.Integer, primary_key=True)
    participant_first_name = db.Column(db.String)
    participant_last_name = db.Column(db.String)
    registration_participant = db.relationship('RegistrationsDB', backref='registration_participant')
    fighter_image = db.Column(db.String)


class CompetitionsDB(db.Model):
    competition_id = db.Column(db.Integer, primary_key=True)
    competition_name = db.Column(db.String)
    competition_date_start = db.Column(db.Date, default=datetime.utcnow)
    competition_date_finish = db.Column(db.Date, default=datetime.utcnow)
    competition_city = db.Column(db.String)
    fights = db.relationship('FightsDB', backref='competition')
    registration_comp = db.relationship('RegistrationsDB', backref='registration_comp')


class RegistrationsDB(db.Model):
    reg_id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('participantsDB.participant_id'))
    competition_id = db.Column(db.Integer, db.ForeignKey('competitionsDB.competition_id'))
    weight = db.Column(db.Float)
    weight_cat_id = db.Column(db.Integer, db.ForeignKey('weightcategoriesDB.weight_cat_id'))
    activity_status = db.Column(db.Integer, default=1)
    red_fighter = db.relationship('FightsDB', backref='red_fighter', foreign_keys="[FightsDB.red_fighter_id]")
    blue_fighter = db.relationship('FightsDB', backref='blue_fighter', foreign_keys="[FightsDB.blue_fighter_id]")
    winner_reg = db.relationship('FightsDB', backref='winner_reg', foreign_keys="[FightsDB.fight_winner_id]")


class FightsDB(db.Model):
    fight_id = db.Column(db.Integer, primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitionsDB.competition_id'))
    round_number = db.Column(db.Integer)
    red_fighter_id = db.Column(db.Integer, db.ForeignKey('registrationsDB.reg_id'))
    blue_fighter_id = db.Column(db.Integer, db.ForeignKey('registrationsDB.reg_id'))
    fight_winner_id = db.Column(db.Integer, db.ForeignKey('registrationsDB.reg_id'))
    final_status = db.Column(db.String, default='continue')


class BacklogDB(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reg_id = db.Column(db.Integer, db.ForeignKey('registrationsDB.reg_id'))
    competition_id = db.Column(db.Integer, db.ForeignKey('competitionsDB.competition_id'))
    round_number = db.Column(db.Integer)


class WeightcategoriesDB(db.Model):
    """Модель для весовых категорий"""
    weight_cat_id = db.Column(db.Integer, primary_key=True)
    sort_index = db.Column(db.Integer)
    weight_category_name = db.Column(db.String)
    weight_category_start = db.Column(db.Integer)
    weight_category_finish = db.Column(db.Integer)
    registrations = db.relationship('RegistrationsDB', backref='registrations')
