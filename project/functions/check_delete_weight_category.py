from models.models import WeightcategoriesDB, RegistrationsDB
from sqlalchemy import desc, asc
from extensions import extensions
db = extensions.db

def check_delete_weight_category(weight_cat_id):
    # текущая категория
    current_weight_cat_data = WeightcategoriesDB.query.filter_by(weight_cat_id=weight_cat_id).first()
    competition_id = current_weight_cat_data.competition_id
    weight_cat_id = int(weight_cat_id)
    # Все категории
    all_weight_categories_data = WeightcategoriesDB.query.filter_by(competition_id=competition_id).all()
    # количество категорий
    number_of_weight_categories = len(list(all_weight_categories_data))

    if number_of_weight_categories == 2:
        # если количество категорий равно 2, то удаляем обе при условии, что нет связанных регистраций
        # итерируемся по категориям и считаем сколько есть регистраций
        number_of_registrations = 0
        number_of_registrations_dict = {}
        text_regs_list = []
        weight_cat_name_list = []
        for weight_cat in all_weight_categories_data:
            # регистрации, связанные с регистрацией
            weight_cat_id = weight_cat.weight_cat_id
            weight_cat_name = weight_cat.weight_category_name
            weight_cat_name_list.append(weight_cat_name)
            registrations_data = RegistrationsDB.query.filter_by(weight_cat_id=weight_cat_id).all()
            regs_qty = 0
            if registrations_data:
                regs_qty = regs_qty + len(list(registrations_data))
                number_of_registrations = number_of_registrations + len(list(registrations_data))

            # записываем в словарь текущую категорию и сколько у нее регистраций
            number_of_registrations_dict[weight_cat_name] = regs_qty
        # print("number_of_registrations: ", number_of_registrations)
        if number_of_registrations > 0:
            for (key, value) in number_of_registrations_dict.items():
                text_var = ""
                if value != 0:
                    text_var = f"{key}: кол-во регистраций - {value}"
                    text_regs_list.append(text_var)

            text_regs_data = text_regs_list
            # print("text_regs_data: ", text_regs_data)
            delete_confirmation = 0
            return delete_confirmation, text_regs_data, number_of_weight_categories
        else:
            delete_confirmation = 1
            # названия удаляемых категорий
            text_regs_data = weight_cat_name_list
            return delete_confirmation, text_regs_data, number_of_weight_categories

    if number_of_weight_categories == 3:
        # Если удаляемая категория - первая
        # Определяем первую категорию
        first_weight_category_data = WeightcategoriesDB.query.filter_by(competition_id=competition_id).order_by(
            asc(WeightcategoriesDB.sort_index)).first()
        # определяем вторую категорию
        second_weight_category_data = db.session.query(WeightcategoriesDB).order_by(
            WeightcategoriesDB.sort_index.asc()).filter(
            WeightcategoriesDB.sort_index > first_weight_category_data.sort_index).first()
        second_weight_category_weight_cat_id = second_weight_category_data.weight_cat_id

        current_weight_cat_data = WeightcategoriesDB.query.get(weight_cat_id)
        current_weight_cat_name = current_weight_cat_data.weight_category_name
        first_weight_category_id = first_weight_category_data.weight_cat_id
        number_of_registrations_dict = {}
        weight_cat_name_list = []
        text_regs_list = []
        current_weight_cat_registrations_data = RegistrationsDB.query.filter_by(weight_cat_id=weight_cat_id).all()
        if weight_cat_id == first_weight_category_id:
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

        elif weight_cat_id == second_weight_category_weight_cat_id:
            if current_weight_cat_registrations_data:
                regs_qty = len(list(current_weight_cat_registrations_data))
                print("я здесь")
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




        else:
            print("что-то не так")


    else:
        print('какой-то сценарий не покрыт')
