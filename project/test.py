from models.models import FightsDB, BacklogDB, FightcandidateDB, RegistrationsDB, UserDB
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

# delete_backlogs()
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

def create_user():
    with app.app_context():
        new_user = UserDB(
            user_saved_weight_cat_id=1,
            user_saved_age_cat_id=1,
            user_saved_round_id=1
        )
        db.session.add(new_user)
        db.session.commit()
        last_created_user= UserDB.query.order_by(desc(UserDB.user_id)).first()

        print("uset id: ", last_created_user.user_id, " has been created")

# create_user()