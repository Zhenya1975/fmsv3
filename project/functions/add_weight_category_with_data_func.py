from flask import request
from sqlalchemy import desc, asc
from models.models import WeightcategoriesDB
from extensions import extensions

db = extensions.db


def add_weight_category_with_data_func(weight_cat_id):
    current_weight_category_data = WeightcategoriesDB.query.get(weight_cat_id)
    current_weight_category_from_value = current_weight_category_data.weight_category_start
    current_weight_category_to_value = current_weight_category_data.weight_category_finish
    current_weight_category_weight_cat_id = current_weight_category_data.weight_cat_id
    current_weight_category_sort_index = current_weight_category_data.sort_index
    competition_id = current_weight_category_data.competition_id

    # определяем следующую категорию

    try:
        next_weight_category_data = db.session.query(WeightcategoriesDB).order_by(
            WeightcategoriesDB.sort_index.asc()).filter(
            WeightcategoriesDB.sort_index > current_weight_category_sort_index).first()
        next_weight_category_id = next_weight_category_data.weight_cat_id
    except:
        pass

    # определяем предыдущую категорию
    try:
        previous_weight_category_data = db.session.query(WeightcategoriesDB).order_by(
            WeightcategoriesDB.sort_index.desc()).filter(
            WeightcategoriesDB.sort_index < current_weight_category_sort_index).first()
        previous_weight_category_id = previous_weight_category_data.weight_cat_id
        previous_weight_category_name = previous_weight_category_data.weight_category_name
        previous_weight_category_finish = previous_weight_category_data.weight_category_finish
    except:
        pass

    # если следующая категория существует
    if next_weight_category_data:
        next_weight_category_data_weight_cat_id = next_weight_category_data.weight_cat_id

        # определяем является ли следующая категория последней
        last_weight_category_data = WeightcategoriesDB.query.filter_by(competition_id=competition_id).order_by(
            desc(WeightcategoriesDB.sort_index)).first()
        last_weight_category_data_from_value = last_weight_category_data.weight_category_start
        last_weight_category_data_to_value = last_weight_category_data.weight_category_finish
        last_weight_category_data_weight_cat_id = last_weight_category_data.weight_cat_id

        if next_weight_category_data_weight_cat_id == last_weight_category_data_weight_cat_id:
            value_from = current_weight_category_to_value
            status_of_last_record = 1
        else:
            # print("следующая категория существует - и она НЕ последняя")
            value_from = current_weight_category_to_value
            status_of_last_record = 2
    # следующей категории нет
    else:
        value_from = current_weight_category_from_value
        status_of_last_record = 0

    # определяем ограничения для инпутов в форме
    # в поле "Вес от" ограничение - от начала предыдущей категории до текущего значения

    from_field_min = current_weight_category_to_value

    if next_weight_category_data and next_weight_category_id != last_weight_category_data_weight_cat_id:
        from_field_max = next_weight_category_data.weight_category_finish
    elif next_weight_category_data and next_weight_category_id == last_weight_category_data_weight_cat_id:
        from_field_max = next_weight_category_data.weight_category_start
    else:
        from_field_max = 1000000-1

    return competition_id, weight_cat_id, current_weight_category_data, value_from, status_of_last_record, from_field_min, from_field_max