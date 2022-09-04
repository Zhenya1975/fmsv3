from models.models import FightsDB, BacklogDB, FightcandidateDB
from sqlalchemy import desc, asc
from extensions import extensions

db = extensions.db


def create_backlog_record(competition_id, reg_id, round_id):
    """Создание новой записи в бэклоге"""
    # Проверяем есть ли регистрация в кандидатах или созданных боях
    fights_red_data = FightsDB.query.filter_by(competition_id=competition_id, red_fighter_id=reg_id,
                                               round_number=round_id).all()
    fights_red_qty = len(list(fights_red_data))
    fights_blue_data = FightsDB.query.filter_by(competition_id=competition_id, blue_fighter_id=reg_id,
                                                round_number=round_id).all()
    fights_blue_qty = len(list(fights_blue_data))
    fights_qty = fights_red_qty + fights_blue_qty
    if fights_qty == 0:
        # если связанных боев нет, то проверяем есть ли связанная запись в бэклоге и в кандидатах
        backlog_data = BacklogDB.query.filter_by(competition_id=competition_id, reg_id=reg_id, round_id=round_id).all()
        # Если связанные регистрации есть, то удаляем их
        backlog_qty = len(list(backlog_data))
        if backlog_qty > 0:
            for backlog in backlog_data:
                db.session.delete(backlog)
                try:
                    db.session.commit()
                except Exception as e:
                    print("Не удалось удалить запись в бэклоге в check_delete_weight_category.py", e)
                    db.session.rollback()

        # Проверяем есть ли кандидаты
        candidates_red_data = FightcandidateDB.query.filter_by(round_id=round_id, red_candidate_reg_id=reg_id).first()
        candidates_red_qty = 0
        if candidates_red_data:
            db.session.delete(candidates_red_data)
            try:
                db.session.commit()
            except Exception as e:
                print("Не удалось удалить запись в красном кандидате check_delete_weight_category.py", e)
                db.session.rollback()

        candidates_blue_data = FightcandidateDB.query.filter_by(round_id=round_id, blue_candidate_reg_id=reg_id).first()

        if candidates_blue_data:
            db.session.delete(candidates_blue_data)
            try:
                db.session.commit()
            except Exception as e:
                print("Не удалось удалить запись в синем кандидате check_delete_weight_category.py", e)
                db.session.rollback()

        # создаем запись в бэклоге
        new_backlog_record = BacklogDB(
            reg_id=reg_id,
            competition_id=competition_id,
            round_id=round_id
        )
        db.session.add(new_backlog_record)
        try:
            db.session.commit()
        except Exception as e:
            print("Не удалось добавить запись в бэклог в check_delete_weight_category.py", e)
            db.session.rollback()

    return fights_qty
