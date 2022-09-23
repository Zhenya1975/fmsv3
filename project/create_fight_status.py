from models.models import Fight_statusDB, CompetitionsDB
from extensions import extensions
from app import app

db = extensions.db


with app.app_context():
    fight_status_dict = {0: "Не начат", 1:"Продолжается", 2:"Завершен"}
    comp_data = CompetitionsDB.query.all()
    print("comp_data: ", comp_data)
    for comp in comp_data:
        competition_id = comp.competition_id
        for key, item in fight_status_dict.items():
            new_status = Fight_statusDB(competition_id=competition_id,
            fight_status_code=key,
            fight_status_description=item)
            db.session.add(new_status)
            db.session.commit()
                


