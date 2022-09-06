from models.models import RoundsDB
from sqlalchemy import desc, asc
from extensions import extensions

db = extensions.db

def new_round_name_func(competition_id, weight_cat_id, age_cat_id):
  """Вычисление наименования создаваемого круга"""
  # данные созданнных кругов
  rounds_data = RoundsDB.query.filter_by(competition_id=competition_id, weight_cat_id=weight_cat_id, age_cat_id=age_cat_id).all()
  rounds_qty = len(list(rounds_data))
  next_round_number = rounds_qty +1 
  new_round_name = f"Круг {next_round_number}"
  return new_round_name