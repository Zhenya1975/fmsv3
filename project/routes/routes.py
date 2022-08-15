from flask import Blueprint, render_template, redirect, url_for, abort, request, jsonify, flash
from models.models import ParticipantsDB, FightsDB, CompetitionsDB, BacklogDB, RegistrationsDB, WeightcategoriesDB, AgecategoriesDB
from forms.forms import CompetitionForm, RegistrationeditForm, WeightCategoriesForm, AgeCategoriesForm, ParticipantForm
from extensions import extensions
from sqlalchemy import desc, asc
from flask_socketio import SocketIO, emit
from datetime import datetime
from dateutil.relativedelta import relativedelta
import math

db = extensions.db
# db.create_all()
# db.session.commit()
home = Blueprint('home', __name__, template_folder='templates')

socketio = extensions.socketio


# @socketio.event
# def my_event(message):
#     print(message)
#     emit('my_response',
#          {'data': 'datadata'})


def fight_create_func(competition_id, round_number, final_status):
    competition_id = competition_id
    round_number = round_number
    final_status = final_status
    backlog_data = BacklogDB.query.filter_by(competition_id=competition_id, round_number=round_number).all()
    red_fighter_reg_id = backlog_data[0].reg_id
    blue_fighter_reg_id = backlog_data[1].reg_id
    new_fight = FightsDB(competition_id=competition_id, round_number=round_number, red_fighter_id=red_fighter_reg_id,
                         blue_fighter_id=blue_fighter_reg_id, final_status=final_status)
    db.session.add(new_fight)

    try:
        db.session.commit()

    except Exception as e:
        print("не получилось создать новый бой. Ошибка:  ", e)
        db.session.rollback()

    return round_number

    ################################################################


def delete_backlog_records(competition_id, round_number):
    competition_id = competition_id
    round_number = round_number
    # удаляем из бэклога записи с бойцами из созданного боя
    last_created_fight = FightsDB.query.filter_by(competition_id=competition_id, round_number=round_number).order_by(
        desc(FightsDB.fight_id)).first()
    # удаляем записи из бэклога бойцов, которые зашли в бой
    backlog_record_to_delete_red = BacklogDB.query.filter_by(competition_id=competition_id, round_number=round_number,
                                                             reg_id=last_created_fight.red_fighter_id).order_by(
        desc(BacklogDB.reg_id)).first()
    if backlog_record_to_delete_red is None:
        abort(404, description="No backlog record was Found with the given ID")
    else:
        db.session.delete(backlog_record_to_delete_red)
    backlog_record_to_delete_blue = BacklogDB.query.filter_by(competition_id=competition_id, round_number=round_number,
                                                              reg_id=last_created_fight.blue_fighter_id).order_by(
        desc(BacklogDB.reg_id)).first()
    if backlog_record_to_delete_blue is None:
        abort(404, description="No backlog record was Found with the given ID")
    else:
        db.session.delete(backlog_record_to_delete_blue)
    try:
        db.session.commit()

    except Exception as e:
        print("Не удалось удалить записи из бэклога", e)
        db.session.rollback()
    ########################################################


def clear_backlog(competition_id):
    backlog_data = BacklogDB.query.filter_by(competition_id=competition_id).all()
    if len(backlog_data) > 0:
        for row in backlog_data:
            if row is None:
                abort(404, description="No backlog record was Found with the given ID")
            else:
                db.session.delete(row)
        try:
            db.session.commit()
        except Exception as e:
            print("Не удалось очистить бэклог", e)
            db.session.rollback()


@home.route('/test_ajaxfile', methods=["POST", "GET"])
def test_ajaxfile():
    if request.method == 'POST':
        data_from_button = request.form['data_from_button']
        return jsonify({'htmlresponse': render_template('response_test_modal.html', data_from_button=data_from_button)})


@home.route('/test')
def test():
    return render_template('test.html')


@home.route('/test2')
def test2():
    return render_template('test_2.html')


@home.route('/')
def home_view():
    return redirect(url_for('home.competitions'))


# Competitions list
@home.route('/competitions')
def competitions():
    competitions_data = CompetitionsDB.query.all()
    return render_template('competitions_list.html', competitions_data=competitions_data)


@home.route('/participants')
def participants():
    participants_data = ParticipantsDB.query.all()
    return render_template('participants_list.html', participants_data=participants_data)



@home.route('/participant/<int:participant_id>/<active_tab_name>')
def participant(participant_id, active_tab_name):

  data = {'active_tab_pass': 'participant_general_info'}
  if int(active_tab_name) == 1:
      data = {'active_tab_pass': 'participant_general_info'}
  elif int(active_tab_name) == 2:
      data = {'active_tab_pass': 'participant_history_tab'}

  else:
      print("непонятно что передано вместо номера вкладки")
  participant_data = ParticipantsDB.query.get(participant_id)

  participant_form = ParticipantForm()
  
  return render_template('participant.html', participant_data=participant_data, data=data, participant_form=participant_form)



@home.route('/participant_general_info_edit/<int:participant_id>/', methods=["POST", "GET"])
def participant_general_info_edit(participant_id):
  participant_data = ParticipantsDB.query.get(participant_id)
  participant_general_info_form = ParticipantForm()
  if participant_general_info_form.validate_on_submit():
    flash('Изменения сохранены', 'alert-success')
    participant_data.participant_first_name = participant_general_info_form.participant_name_form.data
    participant_data.participant_last_name = participant_general_info_form.participant_last_name_form.data
    participant_data.fighter_image = participant_general_info_form.avatar_google_code.data
    participant_data.birthday = participant_general_info_form.birthday_form.data
    participant_data.participant_city = participant_general_info_form.participant_city.data
    db.session.commit()
    return redirect(url_for('home.participant', participant_id=participant_id, active_tab_name=1))
  else:
    flash('Форма не валидировалась', 'alert-danger')
    return redirect(url_for('home.participant', participant_id=participant_id, active_tab_name=1))

    

@home.route('/edit_comp_general/<int:competition_id>/', methods=["POST", "GET"])
def edit_comp_general(competition_id):
  competition_data=CompetitionsDB.query.get(competition_id)
  form = CompetitionForm()
  if form.validate_on_submit():
    flash('Изменения сохранены', 'alert-success')
    competition_data.competition_name = form.competition_name_form.data
    competition_data.competition_date_start = form.competition_date_start.data
    competition_data.competition_date_finish = form.competition_date_finish.data
    competition_data.competition_city = form.competition_city.data
  

    db.session.commit()
    return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=1))
  else:
    flash('Форма не валидировалась', 'alert-danger')
    return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=1))
    




@home.route('/comp2/<int:competition_id>/<active_tab_name>')
def comp2(competition_id, active_tab_name):
    competition_data = CompetitionsDB.query.get(competition_id)
    form_general_info = CompetitionForm()
    regs = RegistrationsDB.query.filter_by(competition_id=competition_id).join(
        ParticipantsDB.registration_participant).order_by(ParticipantsDB.participant_last_name.asc()).all()
    w_categories = WeightcategoriesDB.query.filter_by(competition_id=competition_id).order_by(WeightcategoriesDB.sort_index).all()
    a_categories = AgecategoriesDB.query.filter_by(competition_id=competition_id).order_by(AgecategoriesDB.sort_index).all()
    
    # список id участников уже зарегистрированных
    regs_data = RegistrationsDB.query.filter_by(competition_id=competition_id).all()
    list_of_participants_ids = []
    for registration in regs_data:
        participant_id = registration.participant_id
        list_of_participants_ids.append(participant_id)

    # print(participants_data)
    # users = db.session.query(ParticipantsDB).filter(ParticipantsDB.participant_id.notin_(list_of_participants_ids))
    result = db.session.query(ParticipantsDB).filter(ParticipantsDB.participant_id.notin_(list_of_participants_ids))
    not_registered_participants = []
    for row in result:
        not_registered_participants.append(row.participant_id)
    participants_data_for_selection = db.session.query(ParticipantsDB).filter(
        ParticipantsDB.participant_id.in_(not_registered_participants))

    data = {'active_tab_pass': 'competition_general_info'}
    if int(active_tab_name) == 1:
        data = {'active_tab_pass': 'competition_general_info'}
    elif int(active_tab_name) == 2:
        data = {'active_tab_pass': 'registrations_tab'}
    elif int(active_tab_name) == 3:
        data = {'active_tab_pass': 'competition_settings'}
    else:
        print("непонятно что передано вместо номера вкладки")

    return render_template('competition_2.html', competition_data=competition_data, data=data, form_general_info
    =form_general_info, regs=regs, participants_data_for_selection=participants_data_for_selection,
                           w_categories=w_categories, a_categories=a_categories)



# создание возрастной категории
@home.route('/comp2/<int:competition_id>/age_cat_new', methods=["POST", "GET"])
def age_category_new(competition_id):
    form = AgeCategoriesForm()
    if form.validate_on_submit():
        # print('создание весовой категории валидировалось')
        flash('Изменения сохранены', 'alert-success')


        new_age_category = AgecategoriesDB(sort_index=form.age_sort_index_form_field.data,
                                                 competition_id=competition_id,
                                                 age_category_name=form.age_category_name_form_field.data,
                                                 age_category_start=form.age_from_form_field.data,
                                                 age_category_finish=form.age_to_form_field.data)
        db.session.add(new_age_category)
        try:
            db.session.commit()
        except Exception as e:
            print(e)
            db.session.rollback()
        return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=3))



# создание весовой категории
@home.route('/comp2/<int:competition_id>/weight_cat_new', methods=["POST", "GET"])
def weight_category_new(competition_id):
    form = WeightCategoriesForm()
    if form.validate_on_submit():
        # print('создание весовой категории валидировалось')
        flash('Изменения сохранены', 'alert-success')
        new_weight_category = WeightcategoriesDB(sort_index=form.sort_index_form_field.data,
                                                 competition_id=competition_id,
                                                 weight_category_name=form.weight_category_name_form_field.data,
                                                 weight_category_start=form.weight_from_form_field.data,
                                                 weight_category_finish=form.weight_to_form_field.data)
        db.session.add(new_weight_category)
        try:
            db.session.commit()
        except Exception as e:
            print(e)
            db.session.rollback()
        return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=3))
    # return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=3))


# new registration form
# @home.route('/comp2/<int:competition_id>/registrations/new', methods=["POST", "GET"])
# def registration_new_2(competition_id):
#     if request.method == 'POST':
#         selected_fighter = request.form.get('fighter_pick')
#         new_registration = RegistrationsDB(participant_id=int(selected_fighter), competition_id=competition_id)
#         db.session.add(new_registration)
#         db.session.commit()
#         return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=2))


# competition page
# @home.route('/competitions/<int:competition_id>/<active_tab_name>', methods=["POST", "GET"])
# def competition_page(competition_id, active_tab_name):
#     competition_data = CompetitionsDB.query.get(competition_id)
#     form_general_info = CompetitionForm()
#     data = {'active_tab_pass': 'competition_general_info'}
#     regs = RegistrationsDB.query.filter_by(competition_id=competition_id).join(
#         ParticipantsDB.registration_participant).order_by(ParticipantsDB.participant_last_name.asc()).all()
#
#     if int(active_tab_name) == 1:
#         data = {'active_tab_pass': 'competition_general_info'}
#     elif int(active_tab_name) == 2:
#         data = {'active_tab_pass': 'registrations_tab'}
#     elif int(active_tab_name) == 3:
#         data = {'active_tab_pass': 'competition_settings'}
#     else:
#         print("непонятно что передано вместо номера вкладки")
#
#     if form_general_info.validate_on_submit():
#         flash('Изменения сохранены', 'alert-success')
#         competition_data.competition_name = form_general_info.competition_name_form.data
#         competition_data.competition_date_start = form_general_info.competition_date_start.data
#         competition_data.competition_date_finish = form_general_info.competition_date_finish.data
#         competition_data.competition_city = form_general_info.competition_city.data
#         try:
#             db.session.commit()
#         except Exception as e:
#             print(e)
#             db.session.rollback()
#
#         data = {'active_tab_pass': 'competition_general_info'}
#
#         return render_template('competition.html', competition_data=competition_data,
#                                form_general_info=form_general_info, data=data, regs=regs)
#     return render_template('competition.html', competition_data=competition_data, form_general_info=form_general_info,
#                            data=data, regs=regs)


# competition delete
@home.route('/competitions/<int:competition_id>/delete/')
def competition_delete(competition_id):
    form_general_info = CompetitionForm()
    competition_data = CompetitionsDB.query.get(competition_id)
    registration_data = RegistrationsDB.query.filter_by(competition_id=competition_id).all()
    number_of_comp_regs = len(list(registration_data))
    # print(number_of_comp_regs)
    data = {'active_tab_pass': 'competition_settings'}
    if number_of_comp_regs > 0:
        flash(f"Количество связанных регистраций: {number_of_comp_regs}. Сначала удалите связанные регистрации.",
              'alert-danger')
        regs = RegistrationsDB.query.filter_by(competition_id=competition_id).join(ParticipantsDB).order_by(
            asc(ParticipantsDB.participant_last_name)).all()
        return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=3))
    else:
        db.session.delete(competition_data)
        try:
            db.session.commit()
            flash(f'Соревнование "{competition_data.competition_name}" удалено', 'alert-success')
            return redirect(url_for('home.competitions'))
        except Exception as e:
            print(e)
            flash(f'Что-то пошло не так. Ошибка: {e}', 'alert-danger')
            db.session.rollback()
    return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=3))


@home.route('/competition_start/')
def competition_start():
    return render_template('competition_start.html')


@home.route('/competition_create_new/', methods=["POST", "GET"])
def competition_create_new():
    form = CompetitionForm()
    if form.validate_on_submit():
        new_competition = CompetitionsDB(competition_name=form.competition_name_form.data,
                                         competition_date_start=form.competition_date_start.data,
                                         competition_date_finish=form.competition_date_finish.data,
                                         competition_city=form.competition_city.data,
                                         )
        db.session.add(new_competition)
        db.session.commit()
        created_competition_data = CompetitionsDB.query.order_by(desc(CompetitionsDB.competition_id)).first()
        competition_id = created_competition_data.competition_id
        regs = RegistrationsDB.query.filter_by(competition_id=competition_id).join(ParticipantsDB).order_by(
            asc(ParticipantsDB.participant_last_name)).all()
        return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=1))


# registration list
@home.route('/competitions/<int:competition_id>/registrations')
def registration_list(competition_id):
    competition_data = CompetitionsDB.query.get(competition_id)
    regs = RegistrationsDB.query.filter_by(competition_id=competition_id).first()
    return redirect(url_for('home.competition_page', competition_id=competition_id, active_tab_name=2))


@home.route('/registration_new/<int:competition_id>/<int:participant_id>', methods=["POST", "GET"])
def registration_new(competition_id, participant_id):
    form = RegistrationeditForm()
    if form.validate_on_submit():
        new_reg = RegistrationsDB(
            weight_value=form.reg_weight.data,
            competition_id=competition_id,
            participant_id=participant_id
        )
        db.session.add(new_reg)
        db.session.commit()
        new_reg_data = RegistrationsDB.query.filter_by(competition_id=competition_id).order_by(
            RegistrationsDB.reg_id.desc()).first()

        last_name = new_reg_data.registration_participant.participant_last_name
        first_name = new_reg_data.registration_participant.participant_first_name
        flash(f"Создана новая регистрация {last_name} {first_name}", 'alert-success')

        return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=2))
    else:
        flash(f"Что-то пошло не так с созданием новой регистрации", 'alert-danger')
        return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=2))



@home.route('/age_category_edit/<int:age_cat_id>/', methods=["POST", "GET"])
def age_category_edit(age_cat_id):
    age_category_data = AgecategoriesDB.query.filter_by(age_cat_id=age_cat_id).first()
    form = AgeCategoriesForm()
    competition_id = age_category_data.competition_id
    if form.validate_on_submit():
        age_category_data.age_category_name = form.age_category_name_form_field.data
        age_category_data.sort_index = form.age_sort_index_form_field.data
        age_category_data.age_category_start = form.age_from_form_field.data
        age_category_data.age_category_finish = form.age_to_form_field.data


        db.session.commit()
        flash(f"Изменения сохранены", 'alert-success')
        return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=3))
    else:
        flash(f"Форма не валидировалась", 'alert-danger')
        return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=3))



@home.route('/weight_category_edit/<int:weight_cat_id>/', methods=["POST", "GET"])
def weight_category_edit(weight_cat_id):
    weight_category_data = WeightcategoriesDB.query.filter_by(weight_cat_id=weight_cat_id).first()
    form = WeightCategoriesForm()
    competition_id = weight_category_data.competition_id
    if form.validate_on_submit():
        weight_category_data.weight_category_name = form.weight_category_name_form_field.data
        weight_category_data.sort_index = form.sort_index_form_field.data
        weight_category_data.weight_category_start = form.weight_from_form_field.data
        weight_category_data.weight_category_finish = form.weight_to_form_field.data


        db.session.commit()
        flash(f"Изменения сохранены", 'alert-success')
        return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=3))
    else:
        flash(f"Форма не валидировалась", 'alert-danger')
        return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=3))
    # return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=3))



@home.route('/registration_edit/<int:reg_id>/', methods=["POST", "GET"])
def registration_edit(reg_id):
    reg_data = RegistrationsDB.query.filter_by(reg_id=reg_id).first()
    competition_id = reg_data.competition_id
    # form = RegistrationeditForm()
    # if form.validate_on_submit():
    if request.method == 'POST':
        weight_value_from_form = request.form.get('weight_input')
        weight_cat_select_id = int(request.form.get('weight_catagory_selector'))

        reg_data.weight_value = weight_value_from_form
        reg_data.weight_cat_id = weight_cat_select_id
        db.session.commit()
        flash(f"Изменения сохранены", 'alert-success')
        # print("weight_cat_id с формы: ", weight_cat_id)
        # print("weight_cat_select_id с формы: ", weight_cat_select_id)
        return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=2))
    return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=2))



@home.route('/age_cat_delete/<int:age_cat_id>/', methods=["POST", "GET"])
def age_cat_delete(age_cat_id):

    age_cat_data = AgecategoriesDB.query.filter_by(age_cat_id=age_cat_id).first()
    competition_id = age_cat_data.competition_id
    regs_data = RegistrationsDB.query.filter_by(age_cat_id=age_cat_id).all()
    number_of_age_cat_regs = len(list(regs_data))

    if number_of_age_cat_regs > 0:
        flash(f"Количество связанных регистраций: {number_of_age_cat_regs}. Сначала удалите связанные регистрации.",
              'alert-danger')
    else:
        db.session.delete(age_cat_data)
        try:
            db.session.commit()
            flash(f'Возрастная категория удалена', 'alert-success')

        except Exception as e:
            print(e)
            flash(f'Что-то пошло не так. Ошибка: {e}', 'alert-danger')
            db.session.rollback()

    return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=3))



@home.route('/weight_cat_delete/<int:weight_cat_id>/', methods=["POST", "GET"])
def weight_cat_delete(weight_cat_id):
    weight_cat_data = WeightcategoriesDB.query.filter_by(weight_cat_id=weight_cat_id).first()
    competition_id = weight_cat_data.competition_id
    regs_data = RegistrationsDB.query.filter_by(weight_cat_id=weight_cat_id).all()
    number_of_weight_cat_regs = len(list(regs_data))

    if number_of_weight_cat_regs > 0:
        flash(f"Количество связанных регистраций: {number_of_weight_cat_regs}. Сначала удалите связанные регистрации.",
              'alert-danger')
    else:
        db.session.delete(weight_cat_data)
        try:
            db.session.commit()
            flash(f'Весовая категория удалена', 'alert-success')

        except Exception as e:
            print(e)
            flash(f'Что-то пошло не так. Ошибка: {e}', 'alert-danger')
            db.session.rollback()

    return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=3))


@home.route('/registration_delete/<int:reg_id>/', methods=["POST", "GET"])
def registration_delete(reg_id):
    reg_data = RegistrationsDB.query.filter_by(reg_id=reg_id).first()
    reg_id = reg_data.reg_id
    competition_id = reg_data.competition_id
    fights_data_red = FightsDB.query.filter_by(red_fighter_id=reg_id).all()
    fights_data_blue = FightsDB.query.filter_by(blue_fighter_id=reg_id).all()
    number_of_fights = len(list(fights_data_red)) + len(list(fights_data_blue))
    # print(number_of_comp_regs)
    if number_of_fights > 0:
        flash(f"Количество связанных поединков: {number_of_fights}. Сначала удалите связанные поединки.",
              'alert-danger')
    else:
        db.session.delete(reg_data)
        try:
            db.session.commit()
            flash(f'Регистрация удалена', 'alert-success')

        except Exception as e:
            print(e)
            flash(f'Что-то пошло не так. Ошибка: {e}', 'alert-danger')
            db.session.rollback()

    return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=2))



@home.route('/edit_age_cat_ajaxfile', methods=["POST", "GET"])
def edit_age_cat_ajaxfile():
    if request.method == 'POST':
        age_cat_id = int(request.form['age_cat_id'])
        form = AgeCategoriesForm()
        age_category_data = AgecategoriesDB.query.filter_by(age_cat_id=age_cat_id).first()
        return jsonify({'htmlresponse': render_template('response_edit_age_category.html',
                                                        age_category_data=age_category_data, form=form)})






@home.route('/edit_weight_cat_ajaxfile', methods=["POST", "GET"])
def edit_weight_cat_ajaxfile():
    if request.method == 'POST':
        weight_cat_id = int(request.form['weight_cat_id'])
        form = WeightCategoriesForm()
        weight_cat_data = WeightcategoriesDB.query.filter_by(weight_cat_id=weight_cat_id).first()
        return jsonify({'htmlresponse': render_template('response_edit_weight_category.html',
                                                        weight_cat_data=weight_cat_data, form=form)})




@home.route('/create_age_category_ajaxfile', methods=["POST", "GET"])
def create_age_category_ajaxfile():
    if request.method == 'POST':
        competition_id = int(request.form['competition_id'])
        form = AgeCategoriesForm()
        return jsonify({'htmlresponse': render_template('response_new_age_category.html',
                                                        competition_id=competition_id, form=form)})


@home.route('/create_weight_category_ajaxfile', methods=["POST", "GET"])
def create_weight_category_ajaxfile():
    if request.method == 'POST':
        competition_id = int(request.form['competition_id'])
        form = WeightCategoriesForm()
        return jsonify({'htmlresponse': render_template('response_new_weight_category.html',
                                                        competition_id=competition_id, form=form)})


# генерация отображения формы создания соревнования
@home.route('/new_comp_ajaxfile', methods=["POST", "GET"])
def new_comp_ajaxfile():
    if request.method == 'POST':
        form = CompetitionForm()
        return jsonify({'htmlresponse': render_template('response_competition_create.html', form=form)})


@home.route('/new_reg_ajaxfile', methods=["POST", "GET"])
def new_reg_ajaxfile():
    if request.method == 'POST':
        competition_id = int(request.form['competition_id'])
        participant_id = int(request.form['participant_id'])
        # new_reg_data = RegistrationsDB(competition_id=competition_id, participant_id=participant_id)
        # db.session.add(new_reg_data)
        # db.session.commit()
        # new_reg_data = RegistrationsDB.query.filter_by(competition_id=competition_id).order_by(RegistrationsDB.reg_id.desc()).first()

        participant_data = ParticipantsDB.query.filter_by(participant_id=participant_id).first()
        last_name = participant_data.participant_last_name

        # print("Добавился ", last_name)
        first_name = participant_data.participant_first_name
        # flash(f"Создана новая регистрация {last_name} {first_name}", 'alert-success')
        # print(reg_data)
        reg_form = RegistrationeditForm()
        return jsonify(
            {'htmlresponse': render_template('response_reg_new.html', form=reg_form, competition_id=competition_id,
                                             participant_data=participant_data)})

@home.route('/delete_age_cat_ajaxfile', methods=["POST", "GET"])
def delete_age_cat_ajaxfile():
    if request.method == 'POST':
        age_cat_id = request.form['age_cat_id']
        age_cat_data = AgecategoriesDB.query.filter_by(age_cat_id=age_cat_id).first()
        return jsonify(
            {'htmlresponse': render_template('response_age_cat_delete.html', age_cat_data=age_cat_data)})



@home.route('/delete_weight_cat_ajaxfile', methods=["POST", "GET"])
def delete_weight_cat_ajaxfile():
    if request.method == 'POST':
        weight_cat_id = request.form['weight_cat_id']
        weight_cat_data = WeightcategoriesDB.query.filter_by(weight_cat_id=weight_cat_id).first()
        return jsonify(
            {'htmlresponse': render_template('response_weight_cat_delete.html', weight_cat_data=weight_cat_data)})


@home.route('/delete_reg_ajaxfile', methods=["POST", "GET"])
def delete_reg_ajaxfile():
    if request.method == 'POST':
        reg_id = request.form['reg_id']
        reg_data = RegistrationsDB.query.filter_by(reg_id=reg_id).first()
        return jsonify({'htmlresponse': render_template('response_reg_delete.html', reg_data=reg_data)})


@home.route('/edit_reg_ajaxfile', methods=["POST", "GET"])
def edit_reg_ajaxfile():
    if request.method == 'POST':
        reg_id = request.form['reg_id']
        reg_data = RegistrationsDB.query.filter_by(reg_id=reg_id).first()
        reg_form = RegistrationeditForm()
        competition_id = reg_data.competition_id
        weight_categories_data = WeightcategoriesDB.query.filter_by(competition_id=competition_id).order_by(WeightcategoriesDB.sort_index).all()
        age_catagories_data = AgecategoriesDB.query.filter_by(competition_id=competition_id).order_by(AgecategoriesDB.sort_index).all()

        # считаем количество полных лет на дату соревнования
        # дата соревнования
        competition_date = reg_data.registration_comp.competition_date_start
        # дата рождения бойца
        birthday_date = reg_data.registration_participant.birthday
        date_diff = (competition_date - birthday_date).total_seconds()
        age_years_float = date_diff/(60*60*24*365.25)
        age_eyars = math.floor(age_years_float)

        return jsonify({'htmlresponse': render_template('response_reg_edit.html', form=reg_form, reg_data=reg_data, weight_categories_data=weight_categories_data, age_catagories_data=age_catagories_data, competition_id=competition_id, age_eyars=age_eyars)})


# Handler for a message received over 'connect' channel
@socketio.on('connect')
def test_connect():
    emit('after connect', {'data': 'Lets dance'})

values = {}


@socketio.on('age_value_changed')
def age_value_changed(received_message):
    values['competition_date_value'] = received_message['competition_date_value']
    values['competition_id'] = received_message['competition_id']
    values['participant_id'] = received_message['participant_id']
    participant_id = values['participant_id']
    competition_date_value = values['competition_date_value']
    competition_id = values['competition_id']
    competition_id = int(competition_id)
    competition_date_value = datetime.strptime(competition_date_value, '%Y-%m-%d').date()
    participant_data = ParticipantsDB.query.get(participant_id)
    birthday_date = participant_data.birthday
    date_diff = (competition_date_value - birthday_date).total_seconds()
    age_years_float = date_diff / (60 * 60 * 24 * 365.25)
    age_years = math.floor(age_years_float)

    age_category_data = AgecategoriesDB.query.filter_by(competition_id=competition_id).all()

    availible_age_cats_ids = []
    for age_category in age_category_data:
        availible_age_cats_ids.append(age_category.age_cat_id)
    age_category_id = availible_age_cats_ids[0]
    weight_category_name = AgecategoriesDB.query.filter_by(age_cat_id=age_category_id).first().age_category_name

    updated_age_cat = {}

    for age_category in age_category_data:
        age_cat_id = age_category.age_cat_id
        age_category_name = age_category.age_category_name
        age_category_start = age_category.age_category_start
        age_category_finish = age_category.age_category_finish
        if age_years >= age_category_start and age_years < age_category_finish:
            updated_age_cat['age_cat_id']  = age_cat_id
            updated_age_cat['age_category_name'] = age_category_name
        else:
            updated_age_cat['age_cat_id'] = age_category_id
    age_cat_id = updated_age_cat['age_cat_id']

    emit('update_age_category_select_value', {'age_cat_id': age_cat_id, 'age_years':age_years}, broadcast=True)






@socketio.on('weight_value_changed')
def weight_value_changed(received_message):
    values['weight_new_value'] = received_message['weight_new_value']
    values['competition_id'] = received_message['competition_id']
    new_weight_value = values['weight_new_value']
    new_weight_value = float(new_weight_value)
    competition_id = values['competition_id']
    competition_id = int(competition_id)
    # надо получить данные с актуальных весовых категория

    # print("new_weight_value: ", new_weight_value, type(new_weight_value), "competition_id: ", competition_id, type(competition_id))
    weight_category_data = WeightcategoriesDB.query.filter_by(competition_id=competition_id).all()

    availible_weight_cats_ids = []
    for weight_category in weight_category_data:
        availible_weight_cats_ids.append(weight_category.weight_cat_id)
    weight_category_id = availible_weight_cats_ids[0]
    weight_category_name = WeightcategoriesDB.query.filter_by(weight_cat_id=weight_category_id).first().weight_category_name
    # print("default_weight_category: ",new_weight_category)
    updated_weight_cat = {}

    for weight_category in weight_category_data:
        weight_cat_id = weight_category.weight_cat_id
        weight_category_name = weight_category.weight_category_name
        weight_category_start = weight_category.weight_category_start
        weight_category_finish = weight_category.weight_category_finish
        if new_weight_value >= weight_category_start and new_weight_value <= weight_category_finish:
            updated_weight_cat['weight_cat_id']  = weight_cat_id
            updated_weight_cat['weight_category_name'] = weight_category_name
        else:
            updated_weight_cat['weight_cat_id'] = weight_category_id
    weight_cat_id = updated_weight_cat['weight_cat_id']
    # emit('update_timer_value', timer_message, broadcast=True)
    emit('update_weight_category_select_value', {'data': weight_cat_id}, broadcast=True)

# emit('after connect', {'data': 'Lets dance'})

# @home.route('/competition/<int:competition_id>', methods=["POST", "GET"])
# def competition_view(competition_id):
#     competition_id = competition_id
#     # round_number = fight_create_func(round_number_prev)
#     last_created_fight = FightsDB.query.filter_by(competition_id=competition_id).order_by(
#         desc(FightsDB.fight_id)).first()
#
#     return render_template("competition.html", fight_data=last_created_fight)


@home.route('/ajaxfile', methods=["POST", "GET"])
def ajaxfile():
    final_status = "continue"
    if request.method == 'POST':
        fight_id = request.form['fight_id']
        winner_color = request.form['winner_color']
        current_fight_data = FightsDB.query.get(fight_id)
        competition_id = current_fight_data.competition_id
        current_round_number = current_fight_data.round_number

        # обновляем данные о победителе и проигравшем
        if winner_color == "red":
            current_fight_data.blue_fighter.activity_status = 0
            current_fight_data.fight_winner_id = current_fight_data.red_fighter_id
        else:
            current_fight_data.red_fighter.activity_status = 0
            current_fight_data.fight_winner_id = current_fight_data.blue_fighter_id
        try:
            db.session.commit()
        except Exception as e:
            print("Не удалось вывести из игры синего бойца", e)
            db.session.rollback()
        # добавляем в бэклог в следующий круг новую запись с победившим
        if winner_color == "red":
            new_backlog_record = BacklogDB(reg_id=current_fight_data.red_fighter_id, competition_id=competition_id,
                                           round_number=current_round_number + 1)
        else:
            new_backlog_record = BacklogDB(reg_id=current_fight_data.blue_fighter_id, competition_id=competition_id,
                                           round_number=current_round_number + 1)
        db.session.add(new_backlog_record)
        try:
            db.session.commit()

        except Exception as e:
            print("не удалось добавить запись с победившим в бэклог", e)
            db.session.rollback()

        # проверяем ситуацию в бэклоге в текущем и следующем раунде
        next_round_backlog_data = BacklogDB.query.filter_by(competition_id=competition_id,
                                                            round_number=current_round_number + 1).all()

        current_backlog_data = BacklogDB.query.filter_by(competition_id=competition_id,
                                                         round_number=current_round_number).all()

        # print("len(current_backlog_data): ", len(current_backlog_data), "len(next_round_backlog_data): ", len(next_round_backlog_data))
        if len(current_backlog_data) == 1 and len(next_round_backlog_data) == 1:

            final_status = 'continue'
            next_round_fighter_data = BacklogDB.query.filter_by(competition_id=competition_id,
                                                                round_number=current_round_number + 1).first()

            current_round_fighter_data = BacklogDB.query.filter_by(competition_id=competition_id,
                                                                   round_number=current_round_number).first()

            if next_round_fighter_data.fighter_id != current_round_fighter_data.fighter_id:
                current_round_fighter_data.round_number = current_round_number + 1
                current_round_number = current_round_number + 1
                try:
                    db.session.commit()

                except Exception as e:
                    print("не удалось переписать номер круга в записи бойца из следующего круга", e)
                    db.session.rollback()

                fight_create_func(competition_id, current_round_number, final_status)
                # удаляем из бэклога записи с бойцами
                delete_backlog_records(competition_id, current_round_number)

        elif len(current_backlog_data) == 0 and len(next_round_backlog_data) == 1:
            final_status = 'finish'

            clear_backlog(competition_id)

            return jsonify(
                {
                    'final_status': final_status,
                    'fight_id': fight_id,
                })

        elif len(current_backlog_data) == 0 and len(next_round_backlog_data) == 0:
            final_status = 'finish'

            return jsonify(
                {
                    'final_status': final_status,
                    'fight_id': fight_id,
                })

        # если в след раунде два бойца, а в текущем ни одного
        elif len(current_backlog_data) == 0 and len(next_round_backlog_data) > 1:
            current_round_number = current_round_number + 1
            final_status = 'continue'
            fight_create_func(competition_id, current_round_number, final_status)
            delete_backlog_records(competition_id, current_round_number)

        elif len(current_backlog_data) == 1 and len(next_round_backlog_data) > 1:
            current_round_fighter_data = BacklogDB.query.filter_by(competition_id=competition_id,
                                                                   round_number=current_round_number).first()
            current_round_fighter_data.round_number = current_round_number + 1
            try:
                db.session.commit()
            except Exception as e:
                print("не удалось перекинуть бойца в бэклог следующего круга", e)
                db.session.rollback()
            current_round_number = current_round_number + 1
            final_status = 'continue'
            fight_create_func(competition_id, current_round_number, final_status)
            # удаляем из бэклога записи с бойцами
            delete_backlog_records(competition_id, current_round_number)

        elif len(current_backlog_data) > 1:
            print("len(current_backlog_data) > 1")
            fight_create_func(competition_id, current_round_number, 'continue')
            delete_backlog_records(competition_id, current_round_number)
        else:
            print("что-то непонятное")

        last_created_fight = FightsDB.query.filter_by(competition_id=competition_id,
                                                      round_number=current_round_number).order_by(
            desc(FightsDB.fight_id)).first()

        return jsonify(
            {'htmlresponsered': render_template('response_red_fighter_div.html', fight_data=last_created_fight),
             'htmlresponseblue': render_template('response_blue_fighter_div.html', fight_data=last_created_fight),
             'htmlresponsetitle': render_template('response_title_div.html', fight_data=last_created_fight),
             'final_status': final_status,
             'fight_id': last_created_fight.fight_id
             })


@home.route('/competition_finish/<int:fight_id>')
def finish(fight_id):
    fight_data = FightsDB.query.get(fight_id)
    winner_reg_id = fight_data.fight_winner_id
    competition_id = fight_data.competition_id
    registration_data = RegistrationsDB.query.get(winner_reg_id)
    participant_id = registration_data.participant_id
    winner_data = ParticipantsDB.query.get(participant_id)
    fights_data = FightsDB.query.filter_by(competition_id=competition_id).all()
    return render_template("finish.html", winner_data=winner_data, fights_data=fights_data)
