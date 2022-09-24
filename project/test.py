from models.models import FightsDB, BacklogDB, FightcandidateDB, RegistrationsDB
from sqlalchemy import desc, asc
from extensions import extensions
from app import app
db = extensions.db

def delete_backlogs():

    with app.app_context():
        backlog_data = BacklogDB.query.all()
        for backlog in backlog_data:
            db.session.delete(backlog)
            db.session.commit()

delete_backlogs()
def delete_rounds():
    with app.app_context():
        rounds_data = RoundsDB.query.all()
        for round in rounds_data:
            db.session.delete(round)
            db.session.commit()
# delete_rounds()

def delete_fights():
    with app.app_context():
        fights_data = FightsDB.query.all()
        for fight in fights_data:
            db.session.delete(fight)
            db.session.commit()

# delete_fights()