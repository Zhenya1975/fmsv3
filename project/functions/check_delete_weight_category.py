from models.models import WeightcategoriesDB, RegistrationsDB


def check_delete_weight_category(weight_cat_id):
    # текущая категория
    current_weight_cat_data = WeightcategoriesDB.query.filter_by(weight_cat_id=weight_cat_id).first()
    competition_id = current_weight_cat_data.competition_id

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
        for weight_cat in all_weight_categories_data:
            # регистрации, связанные с регистрацией
            weight_cat_id = weight_cat.weight_cat_id
            weight_cat_name = weight_cat.weight_category_name

            registrations_data = RegistrationsDB.query.filter_by(weight_cat_id=weight_cat_id).all()
            regs_qty = 0
            if registrations_data:
                regs_qty = regs_qty + len(list(registrations_data))

            # записываем в словарь текущую категорию и сколько у нее регистраций
            number_of_registrations_dict[weight_cat_name] = regs_qty

        for (key, value) in number_of_registrations_dict.items():
            text_var = ""
            if value != 0:
                text_var = f"{key}: кол-во регистраций - {value}"
                text_regs_list.append(text_var)

        delete_confirmation = 0
        return delete_confirmation, text_regs_list



    else:
        print('какой-то сценарий не покрыт')
