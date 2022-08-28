from models.models import WeightcategoriesDB, RegistrationsDB
from sqlalchemy import desc, asc
from extensions import extensions
db = extensions.db

def check_delete_weight_category(weight_cat_id):
    # текущая категория
    current_weight_cat_data = WeightcategoriesDB.query.get(weight_cat_id)
    current_weight_cat_name = current_weight_cat_data.weight_category_name
    competition_id = current_weight_cat_data.competition_id
    weight_cat_id = int(weight_cat_id)
    # Все категории
    all_weight_categories_data = WeightcategoriesDB.query.filter_by(competition_id=competition_id).all()
    # количество категорий
    number_of_weight_categories = len(list(all_weight_categories_data))

    # Определяем первую категорию
    first_weight_category_data = WeightcategoriesDB.query.filter_by(competition_id=competition_id).order_by(
        asc(WeightcategoriesDB.sort_index)).first()
    first_weight_category_id = first_weight_category_data.weight_cat_id

    # определяем вторую категорию
    second_weight_category_data = db.session.query(WeightcategoriesDB).order_by(
        WeightcategoriesDB.sort_index.asc()).filter(
        WeightcategoriesDB.sort_index > first_weight_category_data.sort_index).first()
    second_weight_category_weight_cat_id = second_weight_category_data.weight_cat_id

    # Определяем последнюю категорию
    last_weight_category_data = WeightcategoriesDB.query.filter_by(competition_id=competition_id).order_by(
        desc(WeightcategoriesDB.sort_index)).first()
    last_weight_category_id = last_weight_category_data.weight_cat_id
    last_weight_category_sort_index = last_weight_category_data.sort_index

    # Определяем предпоследнюю категорию
    before_last_weight_category_data = db.session.query(WeightcategoriesDB).order_by(
        WeightcategoriesDB.sort_index.desc()).filter(
        WeightcategoriesDB.sort_index < last_weight_category_sort_index).first()
    before_last_weight_category_name = before_last_weight_category_data.weight_category_name
    before_last_weight_category_id = before_last_weight_category_data.weight_cat_id

    number_of_registrations_dict = {}
    weight_cat_name_list = []
    text_regs_list = []
    current_weight_cat_registrations_data = RegistrationsDB.query.filter_by(weight_cat_id=weight_cat_id).all()

    if current_weight_cat_registrations_data:
        regs_qty = len(list(current_weight_cat_registrations_data))
        number_of_registrations_dict[current_weight_cat_name] = regs_qty
        for (key, value) in number_of_registrations_dict.items():
            text_var = ""
            if value != 0:
                text_var = f"{key}: кол-во регистраций - {value}"
                text_regs_list.append(text_var)

        text_regs_data = text_regs_list
        delete_confirmation = 0
        return delete_confirmation, text_regs_data, number_of_weight_categories
    else:
        delete_confirmation = 1
        # названия удаляемых категорий
        weight_cat_name_list.append(current_weight_cat_name)
        text_regs_data = weight_cat_name_list
        return delete_confirmation, text_regs_data, number_of_weight_categories, weight_cat_id

