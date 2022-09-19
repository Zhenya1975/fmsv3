from flask import Blueprint, render_template, redirect, url_for, abort, request, jsonify, flash
from models.models import ParticipantsDB, FightsDB, CompetitionsDB, BacklogDB, RegistrationsDB, WeightcategoriesDB, \
    AgecategoriesDB, RoundsDB, FightcandidateDB, TatamiDB, QueueDB
from forms.forms import CompetitionForm, RegistrationeditForm, WeightCategoriesForm, AgeCategoriesForm, ParticipantForm, \
    ParticipantNewForm
from functions import check_delete_weight_category, create_backlog_record, new_round_name
from extensions import extensions
from sqlalchemy import desc, asc, func
from sqlalchemy import and_, or_
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


@home.route('/fight/<int:fight_id>')
def fight(fight_id):
    fight_data = FightsDB.query.get(fight_id)
    round_id = fight_data.round_number
    round_data = RoundsDB.query.get(round_id)
    round_name = round_data.round_name
    competition_id = round_data.competition_id
    competition_data = CompetitionsDB.query.get(competition_id)
    fight_duration = competition_data.fight_duration
    added_time = competition_data.added_time
    return render_template("fight.html", fight_data=fight_data, round_name=round_name, fight_duration=fight_duration,
                           added_time=added_time)


@home.route('/fights/<int:competition_id>/')
def fights(competition_id):
    competition_data = CompetitionsDB.query.get(competition_id)
    age_catagories_data = AgecategoriesDB.query.filter_by(competition_id=competition_id).order_by(
        AgecategoriesDB.sort_index.asc()).all()
    weight_categories_data = WeightcategoriesDB.query.filter_by(competition_id=competition_id).order_by(
        WeightcategoriesDB.sort_index.asc()).all()
    tatami_data = TatamiDB.query.filter_by(competition_id=competition_id).all()

    return render_template("fights.html",
                           competition_data=competition_data,
                           age_catagories_data=age_catagories_data,
                           weight_categories_data=weight_categories_data,
                           tatami_data=tatami_data
                           )


@home.route('/participant/<int:participant_id>/<active_tab_name>')
def participant(participant_id, active_tab_name):
    data = {'active_tab_pass': 'participant_general_info'}
    if int(active_tab_name) == 1:
        data = {'active_tab_pass': 'participant_general_info'}
    elif int(active_tab_name) == 2:
        data = {'active_tab_pass': 'participant_history_tab'}
    elif int(active_tab_name) == 3:
        data = {'active_tab_pass': 'participant_settings_tab'}


    else:
        print("непонятно что передано вместо номера вкладки")
    participant_data = ParticipantsDB.query.get(participant_id)

    participant_form = ParticipantForm()
    active_status = participant_data.active_status
    if active_status == True:
        active_status = 1
    else:
        active_status = 0

    return render_template('participant.html', participant_data=participant_data, data=data,
                           participant_form=participant_form, active_status=active_status)


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
        participant_data.active_status = participant_general_info_form.active_status.data

        db.session.commit()
        return redirect(url_for('home.participant', participant_id=participant_id, active_tab_name=1))
    else:
        flash('Форма не валидировалась', 'alert-danger')
        return redirect(url_for('home.participant', participant_id=participant_id, active_tab_name=1))


@home.route('/edit_comp_general/<int:competition_id>/', methods=["POST", "GET"])
def edit_comp_general(competition_id):
    competition_data = CompetitionsDB.query.get(competition_id)
    form = CompetitionForm()
    if form.validate_on_submit():
        flash('Изменения сохранены', 'alert-success')
        competition_data.competition_name = form.competition_name_form.data
        competition_data.competition_date_start = form.competition_date_start.data
        competition_data.competition_date_finish = form.competition_date_finish.data
        competition_data.competition_city = form.competition_city.data
        competition_data.fight_duration = form.fight_duration.data
        competition_data.added_time = form.added_time.data

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
    w_categories = WeightcategoriesDB.query.filter_by(competition_id=competition_id).order_by(
        WeightcategoriesDB.sort_index).all()
    a_categories = AgecategoriesDB.query.filter_by(competition_id=competition_id).order_by(
        AgecategoriesDB.sort_index).all()

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
        data = {'active_tab_pass': 'schedule_tab'}
    elif int(active_tab_name) == 4:
        data = {'active_tab_pass': 'competition_settings'}
    else:
        print("непонятно что передано вместо номера вкладки")

    # определяем количество строк весовых категорий
    number_of_weight_categories = len(list(w_categories))

    tatami_data = TatamiDB.query.filter_by(competition_id=competition_id).all()
    tatami_list = []
    for tatami in tatami_data:
        tatami_id = tatami.tatami_id
        tatami_list.append(tatami_id)

    # queue_data = db.session.query(QueueDB).filter(QueueDB.tatami_id.in_(tatami_list)).all()
    # queue_data = QueueDB.query.filter_by(competition_id=competition_id).order_by(asc(QueueDB.queue_sort_index)).all()
    
    queue_data = FightsDB.query.filter_by(competition_id=competition_id).order_by(and_(FightsDB.queue_catagory_sort_index, FightsDB.queue_sort_index)).all()
    # print("queue_data: ", queue_data)
    
    # print("queue_data: ", queue_data)
    return render_template('competition_2.html', competition_data=competition_data, data=data, form_general_info
    =form_general_info, regs=regs, participants_data_for_selection=participants_data_for_selection,
                           w_categories=w_categories, a_categories=a_categories,
                           number_of_weight_categories=number_of_weight_categories, tatami_data=tatami_data,
                           queue_data=queue_data)

 
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
        return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))


# добавление весовой категории из непустой
@home.route('/comp2/<int:competition_id>/<int:weight_cat_id>/<int:status_of_last_record>/weight_cat_add_data_row',
            methods=["POST", "GET"])
def add_weight_category_with_data(competition_id, weight_cat_id, status_of_last_record):
    if request.method == 'POST':

        weight_value_from_form = int(request.form.get('from'))
        if weight_value_from_form:
            weight_value_from_form = int(request.form.get('from'))
        else:
            flash('Изменения не сохранены. Значение границы весовой категории некорректно', 'alert-danger')
            return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))

        weight_value_to_form = int(request.form.get('to'))
        if weight_value_to_form:
            weight_value_to_form = int(request.form.get('to'))
        else:
            flash('Изменения не сохранены. Значение границы весовой категории некорректно', 'alert-danger')
            return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))

        current_weight_category_data = WeightcategoriesDB.query.get(weight_cat_id)
        current_weight_category_from_value = current_weight_category_data.weight_category_start
        current_weight_category_to_value = current_weight_category_data.weight_category_finish
        current_weight_category_sort_index = current_weight_category_data.sort_index

        # Если следующая запись есть и она не последняя
        if status_of_last_record == 2:
            next_weight_category_data = db.session.query(WeightcategoriesDB).order_by(
                WeightcategoriesDB.sort_index.asc()).filter(
                WeightcategoriesDB.sort_index > current_weight_category_sort_index).first()

            next_weight_category_data_from_value = next_weight_category_data.weight_category_start
            next_weight_category_data_to_value = next_weight_category_data.weight_category_finish
            next_weight_category_data_sort_index = next_weight_category_data.sort_index

            if weight_value_from_form >= current_weight_category_from_value and weight_value_to_form <= next_weight_category_data_to_value and weight_value_to_form > weight_value_from_form:
                # редактируем текущую категорию
                current_weight_category_data.weight_category_finish = weight_value_from_form
                current_weight_category_data.weight_category_name = f"От {current_weight_category_from_value} до {weight_value_from_form} кг"
                # создаем новую весовую категорию
                sort_index = (
                                     next_weight_category_data_sort_index - current_weight_category_sort_index) / 2 + current_weight_category_sort_index
                new_weight_category_sort_index = int(round(sort_index, 0))
                new_weight_category_start = weight_value_from_form
                new_weight_category_finish = weight_value_to_form
                new_weight_category_name = f"От {weight_value_from_form} до {weight_value_to_form} кг"
                new_weight_category = WeightcategoriesDB(sort_index=new_weight_category_sort_index,
                                                         competition_id=competition_id,
                                                         weight_category_name=new_weight_category_name,
                                                         weight_category_start=new_weight_category_start,
                                                         weight_category_finish=new_weight_category_finish)

                db.session.add(new_weight_category)

                # Редактируем следующую после созданной
                next_weight_category_data.weight_category_start = weight_value_to_form
                next_weight_category_data.weight_category_name = f"От {weight_value_to_form} до {next_weight_category_data_to_value} кг"
                db.session.commit()
                flash('Изменения сохранены', 'alert-success')
                return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))

            else:
                flash('Изменения не сохранены. Значение границы весовой категории некорректно', 'alert-danger')
                return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))

        # Если следующая запись есть и она последняя
        elif status_of_last_record == 1:
            next_weight_category_data = db.session.query(WeightcategoriesDB).order_by(
                WeightcategoriesDB.sort_index.asc()).filter(
                WeightcategoriesDB.sort_index > current_weight_category_sort_index).first()

            next_weight_category_data_from_value = next_weight_category_data.weight_category_start
            next_weight_category_data_to_value = next_weight_category_data.weight_category_finish
            next_weight_category_data_sort_index = next_weight_category_data.sort_index

            if weight_value_from_form >= current_weight_category_from_value and weight_value_to_form <= next_weight_category_data_to_value and weight_value_to_form > weight_value_from_form:
                # редактируем текущую категорию
                current_weight_category_data.weight_category_finish = weight_value_from_form
                current_weight_category_data.weight_category_name = f"От {current_weight_category_from_value} до {weight_value_from_form} кг"

                # создаем новую весовую категорию
                sort_index = (
                                     next_weight_category_data_sort_index - current_weight_category_sort_index) / 2 + current_weight_category_sort_index
                new_weight_category_sort_index = int(round(sort_index, 0))
                new_weight_category_start = weight_value_from_form
                new_weight_category_finish = weight_value_to_form
                new_weight_category_name = f"От {weight_value_from_form} до {weight_value_to_form} кг"
                new_weight_category = WeightcategoriesDB(sort_index=new_weight_category_sort_index,
                                                         competition_id=competition_id,
                                                         weight_category_name=new_weight_category_name,
                                                         weight_category_start=new_weight_category_start,
                                                         weight_category_finish=new_weight_category_finish)

                db.session.add(new_weight_category)

                # Редактируем следующую после созданной
                next_weight_category_data.weight_category_start = weight_value_to_form
                next_weight_category_data.weight_category_name = f"Свыше {weight_value_to_form} кг"

                db.session.commit()
                flash('Изменения сохранены', 'alert-success')
                return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))


            else:
                flash('Изменения не сохранены. Значение границы весовой категории некорректно', 'alert-danger')
                return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))

        # Если следующая записи нет
        elif status_of_last_record == 0:
            if weight_value_from_form >= current_weight_category_from_value and weight_value_to_form > weight_value_from_form:
                # редактируем текущую категорию
                current_weight_category_data.weight_category_finish = weight_value_to_form
                current_weight_category_data.weight_category_name = f"От {current_weight_category_from_value} до {weight_value_to_form} кг"

                # создаем новую весовую категорию
                new_weight_category_sort_index = current_weight_category_sort_index + 10000
                new_weight_category_start = weight_value_to_form
                new_weight_category_finish = 1000000
                new_weight_category_name = f"Свыше {weight_value_to_form} кг"
                new_weight_category = WeightcategoriesDB(sort_index=new_weight_category_sort_index,
                                                         competition_id=competition_id,
                                                         weight_category_name=new_weight_category_name,
                                                         weight_category_start=new_weight_category_start,
                                                         weight_category_finish=new_weight_category_finish)

                db.session.add(new_weight_category)

                db.session.commit()
                flash('Изменения сохранены', 'alert-success')
                return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))




            else:
                flash('Изменения не сохранены. Значение границы весовой категории некорректно', 'alert-danger')
                return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))


        else:
            flash('Изменения не сохранены. Что-то пошло не так', 'alert-danger')
            return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))


# добавление весовой категории из пустой
@home.route('/comp2/<int:competition_id>/weight_cat_add', methods=["POST", "GET"])
def add_empty_weight_category_new(competition_id):
    if request.method == 'POST':
        weight_value_from_form = 0
        weight_value_to_form = int(request.form.get('to'))
        if weight_value_to_form > 0:
            flash('Изменения сохранены', 'alert-success')

            # Создаем первую категорию
            sort_index = 10000
            weight_category_name = f"До {weight_value_to_form} кг"
            first_weight_category = WeightcategoriesDB(sort_index=sort_index, competition_id=competition_id,
                                                       weight_category_name=weight_category_name,
                                                       weight_category_start=0,
                                                       weight_category_finish=weight_value_to_form)
            db.session.add(first_weight_category)
            try:
                db.session.commit()
            except Exception as e:
                print(e)
                db.session.rollback()
            # добавляем вторую категорию
            weight_category_name = f"Свыше {weight_value_to_form} кг"
            sort_index = 100000
            last_weight_category = WeightcategoriesDB(sort_index=sort_index, competition_id=competition_id,
                                                      weight_category_name=weight_category_name,
                                                      weight_category_start=weight_value_to_form,
                                                      weight_category_finish=1000000)
            db.session.add(last_weight_category)
            try:
                db.session.commit()
            except Exception as e:
                print(e)
                db.session.rollback()

            return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))
        else:
            flash('Изменения не сохранены. Значение границы весовой категории некорректно', 'alert-danger')
            return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))


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
        return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))
    # return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))


@home.route('/participantdelete/<int:participant_id>/delete/')
def participant_delete(participant_id):
    participant_data = ParticipantsDB.query.get(participant_id)
    registration_data = RegistrationsDB.query.filter_by(participant_id=participant_id).all()
    number_of_participant_regs = len(list(registration_data))
    if number_of_participant_regs > 0:
        flash(f"Количество связанных регистраций: {number_of_participant_regs}. Сначала удалите связанные регистрации.",
              'alert-danger')
        return redirect(url_for('home.participant', participant_id=participant_id, active_tab_name=4))
    else:
        db.session.delete(participant_data)
        try:
            db.session.commit()
            flash(
                f'Карточка спортсмена {participant_data.participant_first_name} {participant_data.participant_last_name} удалено',
                'alert-success')
            return redirect(url_for('home.participants'))
        except Exception as e:
            print(e)
            flash(f'Что-то пошло не так. Ошибка: {e}', 'alert-danger')
            db.session.rollback()


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
        return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))
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
    return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))


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


# @home.route('/participant_new', methods=["POST", "GET"])
# def participant_new():
#   form = ParticipantNewForm()
#   if form.validate_on_submit():
#     participant_first_name = form.participant_name_form.data
#     participant_last_name = form.participant_last_name_form.data
#
#     new_participant = ParticipantsDB(participant_first_name=participant_first_name, participant_last_name=participant_last_name)
#
#     db.session.add(new_participant)
#     try:
#       db.session.commit()
#     except Exception as e:
#       print("Исключение: ", e)
#
#     new_participant_data = ParticipantsDB.query.order_by(ParticipantsDB.participant_id.desc()).first()
#     # print(new_participant_data)
#     participant_id = new_participant_data.participant_id
#
#
#     return redirect(url_for('home.participant', participant_id=participant_id, active_tab_name=1))
#   else:
#     flash(f"Что-то пошло не так с созданием нового спортсмена", 'alert-danger')
#     return redirect(url_for('home.participant', participant_id=participant_id, active_tab_name=1))


@home.route('/new_tatami_create/<int:competition_id>', methods=["POST", "GET"])
def new_tatami_create(competition_id):
    if request.method == 'POST':
        tatami_name = request.form.get('tatami_name')
        competition_id = int(competition_id)
        new_tatami = TatamiDB(tatami_name=tatami_name, competition_id=competition_id)
        db.session.add(new_tatami)
        try:
            db.session.commit()
            flash(f"Изменения сохранены", 'alert-success')

        except Exception as e:
            print(e)
            flash(f'Изменения не сохранены. Ошибка: {e}', 'alert-danger')
            db.session.rollback()
        return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=3))


@home.route('/new_round_create/<int:competition_id>/<int:weight_cat_id>/<int:age_cat_id>', methods=["POST", "GET"])
def new_round_create(competition_id, weight_cat_id, age_cat_id):
    if request.method == 'POST':
        round_name = request.form.get('round_name')
        # print("я здесь")
        new_round = RoundsDB(round_name=round_name, competition_id=competition_id, weight_cat_id=weight_cat_id,
                             age_cat_id=age_cat_id)
        db.session.add(new_round)
        try:
            db.session.commit()
            flash(f"Изменения сохранены", 'alert-success')

        except Exception as e:
            print(e)
            flash(f'Изменения не сохранены. Ошибка: {e}', 'alert-danger')
            db.session.rollback()
        # последний созданный раунд
        last_round_data = RoundsDB.query.order_by(desc(RoundsDB.round_id)).first()
        last_round_id = last_round_data.round_id
        # получаем список id в текущем бэклоге
        backlogs_data = BacklogDB.query.filter_by(competition_id=competition_id, round_id=last_round_id).all()
        backlogs_data_id_list = []
        try:
            for backlog in backlogs_data:
                backlog_id = backlog.id
                backlogs_data_id_list.append(backlog_id)
        except:
            pass

        potencial_backlog_data = RegistrationsDB.query.filter_by(competition_id=competition_id,
                                                                 weight_cat_id=weight_cat_id, age_cat_id=age_cat_id,
                                                                 activity_status=1).all()
        try:
            for reg_data in potencial_backlog_data:
                reg_id = reg_data.reg_id
                if reg_id not in backlogs_data_id_list:
                    new_backlog = BacklogDB(reg_id=reg_data.reg_id, competition_id=reg_data.competition_id,
                                            round_id=last_round_id)
                    db.session.add(new_backlog)
                    db.session.commit()
        except:
            pass
        return redirect(url_for('home.fights', competition_id=competition_id))

    flash(f'Изменения не сохранены')
    competition_data = CompetitionsDB.query.get(competition_id)
    weight_categories_data = WeightcategoriesDB.query.get(weight_cat_id)
    age_catagories_data = AgecategoriesDB.query.get(age_cat_id)
    return redirect(url_for('home.fights', competition_data=competition_data, age_catagories_data=age_catagories_data,
                            weight_categories_data=weight_categories_data))


@home.route('/registration_new/<int:competition_id>/<int:participant_id>', methods=["POST", "GET"])
def registration_new(competition_id, participant_id):
    if request.method == 'POST':
        weight_value_from_form = request.form.get('weight_input')
        weight_cat_id = 0
        try:
            weight_cat_select_id = int(request.form.get('weight_catagory_selector'))
            weight_cat_id = weight_cat_select_id
        except:
            weight_cat_select_id = 0
        # Если поле с весовой категорией приехало пустым, то делаем расчет и записываем
        if weight_cat_select_id == 0:
            weight_category_data = WeightcategoriesDB.query.filter_by(competition_id=competition_id).all()
            updated_weight_cat = {}
            for weight_category in weight_category_data:
                weight_cat_id = weight_category.weight_cat_id
                weight_category_name = weight_category.weight_category_name
                weight_category_start = weight_category.weight_category_start
                weight_category_finish = weight_category.weight_category_finish

                if weight_category_start <= int(weight_value_from_form) <= weight_category_finish:
                    updated_weight_cat['weight_cat_id'] = weight_cat_id
                    updated_weight_cat['weight_category_name'] = weight_category_name
                    # print("weight_category_start: ", weight_category_start, "weight_value_from_form: ", weight_value_from_form, "weight_category_finish: ", weight_category_finish)
                    # print("updated_weight_cat: ", updated_weight_cat)
            weight_cat_id = updated_weight_cat['weight_cat_id']

        age_cat_id = 0
        age_value = 0
        try:
            age_value = int(request.form.get('age_input'))
            age_cat_select_id = int(request.form.get('age_catagory_selector'))
            age_cat_id = age_cat_select_id
        except:
            age_cat_select_id = 0

        new_reg = RegistrationsDB(
            weight_value=weight_value_from_form,
            competition_id=competition_id,
            participant_id=participant_id,
            weight_cat_id=weight_cat_id,
            age_value=age_value,
            age_cat_id=age_cat_id,
            activity_status=1
        )

        db.session.add(new_reg)
        try:
            db.session.commit()
            flash(f"Изменения сохранены", 'alert-success')

        except Exception as e:
            print(e)
            flash(f'Изменения не сохранены. Ошибка: {e}', 'alert-danger')
            db.session.rollback()

        # получаем id созданной регистрации
        last_reg_data = RegistrationsDB.query.filter_by(competition_id=competition_id).order_by(
            desc(RegistrationsDB.reg_id)).first()
        reg_id = last_reg_data.reg_id
        # проверяем есть ли хотя бы хотя бы один раунд в весовой и возрастной категории
        weight_cat_data = WeightcategoriesDB.query.get(weight_cat_id)
        age_cat_data = AgecategoriesDB.query.get(age_cat_id)
        rounds_data = RoundsDB.query.filter_by(competition_id=competition_id, weight_cat_id=weight_cat_id,
                                               age_cat_id=age_cat_id).all()

        # print("last_reg_data", last_reg_data, "rounds_data: ", rounds_data)

        # Если есть раунды, то вписываем в бэклоги этих раундов зарегистрированного бойца
        rounds_data_qty = len(list(rounds_data))
        round_id = 0
        if rounds_data_qty > 0:
            for round_data in rounds_data:
                round_id = round_data.round_id
                # запускаем функцию созданяи записи в бэклоге, передавая в нее параметры
                create_backlog_record.create_backlog_record(competition_id, reg_id, round_id)
            # print("созданы записи в бэклоге")

        # если раунда нет, то сначала создаем раунд и затем получаем ее id
        else:
            new_round = RoundsDB(
                round_name="Круг 1",
                competition_id=competition_id,
                weight_cat_id=weight_cat_id,
                age_cat_id=age_cat_id
            )
            db.session.add(new_round)
            # данные созданного раунда
            last_round_data = RoundsDB.query.filter_by(competition_id=competition_id, weight_cat_id=weight_cat_id,
                                                       age_cat_id=age_cat_id).order_by(desc(RoundsDB.round_id)).first()

            round_id = last_round_data.round_id

        # создаем запись в бэклоге
        create_backlog_record.create_backlog_record(competition_id, reg_id, round_id)

        return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=2))
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
        return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))
    else:
        flash(f"Форма не валидировалась", 'alert-danger')
        return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))


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
        return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))
    else:
        flash(f"Форма не валидировалась", 'alert-danger')
        return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))
    # return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))


@home.route('/registration_edit/<int:reg_id>/', methods=["POST", "GET"])
def registration_edit(reg_id):
    reg_data = RegistrationsDB.query.filter_by(reg_id=reg_id).first()
    competition_id = reg_data.competition_id
    # Проверяем есть ли связанные бои с данной регистрацией
    fights_red_data = FightsDB.query.filter_by(competition_id=competition_id, red_fighter_id=reg_id).all()
    fights_red_qty = len(list(fights_red_data))
    fights_blue_data = FightsDB.query.filter_by(competition_id=competition_id, blue_fighter_id=reg_id).all()
    fights_blue_qty = len(list(fights_blue_data))
    fights_qty = fights_red_qty + fights_blue_qty
    if fights_qty > 0:
        flash(f"Изменения не сохранены. Есть связанные поединки", 'alert-danger')
        return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=2))

    if request.method == 'POST':
        weight_value_from_form = request.form.get('weight_input')
        weight_cat_select_id = int(request.form.get('weight_catagory_selector'))
        age_value = int(request.form.get('age_input'))
        age_cat_id = int(request.form.get('age_catagory_selector'))

        reg_data.weight_value = weight_value_from_form
        reg_data.weight_cat_id = weight_cat_select_id
        reg_data.age_value = age_value
        reg_data.age_cat_id = age_cat_id

        db.session.commit()
        flash(f"Изменения сохранены", 'alert-success')

        # удаляем бэклог записи, если они есть и создаем новые
        # получаем данные в каких раундах участвует данная регистрация
        rounds_data = RoundsDB.query.filter_by(competition_id=competition_id,
                                               weight_cat_id=reg_data.weight_cat_id,
                                               age_cat_id=age_cat_id).all()
        try:
            for round in rounds_data:
                round_id = round.round_id
                create_backlog_record.create_backlog_record(competition_id, reg_id, round_id)
        except:
            pass

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

    return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))


@home.route('/weight_1_cat_delete/<int:competition_id>/<int:weight_cat_id>', methods=["POST", "GET"])
def weight_1_cat_delete(competition_id, weight_cat_id):
    """Удаление одной весовой категории"""
    weight_categories_data = WeightcategoriesDB.query.filter_by(competition_id=competition_id).all()
    number_of_weight_categories = len(list(weight_categories_data))
    # Проверяем является ли категория первой
    first_weight_category_data = WeightcategoriesDB.query.filter_by(competition_id=competition_id).order_by(
        asc(WeightcategoriesDB.sort_index)).first()
    first_weight_category_id = first_weight_category_data.weight_cat_id
    first_weight_category_sort_index = first_weight_category_data.sort_index
    first_weight_category_finish = first_weight_category_data.weight_category_finish
    current_weight_cat_id = int(weight_cat_id)
    current_weight_cat_data = WeightcategoriesDB.query.get(current_weight_cat_id)
    current_weight_cat_sort_index = current_weight_cat_data.sort_index

    # следующая весовая категория
    try:
        next_weight_category_data = db.session.query(WeightcategoriesDB).order_by(
            WeightcategoriesDB.sort_index.asc()).filter(
            WeightcategoriesDB.sort_index > current_weight_cat_sort_index).first()
        next_weight_category_weight_category_finish = next_weight_category_data.weight_category_finish
        next_weight_category_id = next_weight_category_data.weight_cat_id
    except:
        pass

    # предыдущая весовая категория
    try:
        previous_weight_category_data = db.session.query(WeightcategoriesDB).order_by(
            WeightcategoriesDB.sort_index.desc()).filter(
            WeightcategoriesDB.sort_index < current_weight_cat_sort_index).first()
        previous_weight_category_id = previous_weight_category_data.weight_cat_id
        previous_weight_category_name = previous_weight_category_data.weight_category_name
        previous_weight_category_finish = previous_weight_category_data.weight_category_finish


    except:
        pass

    # вторая весовая категория
    second_weight_category_data = db.session.query(WeightcategoriesDB).order_by(
        WeightcategoriesDB.sort_index.asc()).filter(
        WeightcategoriesDB.sort_index > first_weight_category_sort_index).first()
    second_weight_category_id = second_weight_category_data.weight_cat_id

    # последняя весовая категория
    last_weight_category_data = WeightcategoriesDB.query.filter_by(competition_id=competition_id).order_by(
        desc(WeightcategoriesDB.sort_index)).first()
    last_weight_category_id = last_weight_category_data.weight_cat_id
    last_weight_category_start = last_weight_category_data.weight_category_start
    last_weight_category_sort_index = last_weight_category_data.sort_index

    # предпоследняя весовая категория
    before_last_weight_category_data = db.session.query(WeightcategoriesDB).order_by(
        WeightcategoriesDB.sort_index.desc()).filter(
        WeightcategoriesDB.sort_index < last_weight_category_sort_index).first()
    before_last_weight_category_finish = before_last_weight_category_data.weight_category_finish
    before_last_weight_category_start = before_last_weight_category_data.weight_category_start
    before_last_weight_category_id = before_last_weight_category_data.weight_cat_id

    if current_weight_cat_id == first_weight_category_id:
        # редактируем вторую категорию
        next_weight_category_data.weight_category_name = f"До {next_weight_category_weight_category_finish} кг"
        next_weight_category_data.weight_category_start = 0
        # удаляем текущую категорию
        db.session.delete(current_weight_cat_data)

    elif current_weight_cat_id == second_weight_category_id and number_of_weight_categories == 3:
        # редактируем третью категорию
        last_weight_category_data.weight_category_name = f"Свыше {first_weight_category_finish} кг"
        last_weight_category_data.weight_category_start = first_weight_category_finish

        # Удаляем текущую категорию
        db.session.delete(current_weight_cat_data)



    elif current_weight_cat_id == second_weight_category_id and number_of_weight_categories >= 4:
        # редактируем третью категорию
        next_weight_category_data.weight_category_name = f"От {first_weight_category_finish} до {next_weight_category_data.weight_category_finish} кг"
        next_weight_category_data.weight_category_start = first_weight_category_finish

        # Удаляем текущую категорию
        db.session.delete(current_weight_cat_data)

    elif current_weight_cat_id == before_last_weight_category_id and number_of_weight_categories >= 4:
        # редактируем последнюю категорию
        last_weight_category_data.weight_category_name = f"Свыше {previous_weight_category_finish} кг"
        last_weight_category_data.weight_category_start = previous_weight_category_finish

        # Удаляем текущую категорию
        db.session.delete(current_weight_cat_data)

    elif current_weight_cat_id == last_weight_category_id:
        # редактируем предпоследнюю категорию
        before_last_weight_category_data.weight_category_name = f"Свыше {before_last_weight_category_start} кг"
        before_last_weight_category_data.weight_category_finish = 1000000
        # Удаляем текущую категорию
        db.session.delete(current_weight_cat_data)


    else:
        # удаляем категорию в середине - не первую, не вторую, не последнюю, ни предпоследнюю
        previous_weight_category_data.weight_category_name = f"От {previous_weight_category_data.weight_category_start} до {next_weight_category_data.weight_category_start} кг"
        previous_weight_category_data.weight_category_finish = next_weight_category_data.weight_category_start
        # Удаляем текущую категорию
        db.session.delete(current_weight_cat_data)

    try:
        db.session.commit()
        flash(f'Весовая категория удалена', 'alert-success')

    except Exception as e:
        print(e)
        flash(f'Что-то пошло не так. Ошибка: {e}', 'alert-danger')
        db.session.rollback()

    return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))


@home.route('/weight_2_cat_delete/<int:competition_id>/', methods=["POST", "GET"])
def weight_2_cat_delete(competition_id):
    """удаление двух первых весовых категорий"""
    weight_categories_data = WeightcategoriesDB.query.filter_by(competition_id=competition_id).all()
    for weight_cat_data in weight_categories_data:
        db.session.delete(weight_cat_data)
    try:
        db.session.commit()
        flash(f'Весовые категории удалены', 'alert-success')

    except Exception as e:
        print(e)
        flash(f'Что-то пошло не так. Ошибка: {e}', 'alert-danger')
        db.session.rollback()

    return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))


@home.route('/weight_cat_delete/<int:weight_cat_id>/', methods=["POST", "GET"])
def weight_cat_delete(weight_cat_id):
    weight_cat_data = WeightcategoriesDB.query.filter_by(weight_cat_id=weight_cat_id).first()
    current_weight_category_sort_index = weight_cat_data.sort_index
    current_weight_category_id = weight_cat_data.weight_cat_id
    competition_id = weight_cat_data.competition_id
    all_weight_category_data = WeightcategoriesDB.query.filter_by(competition_id=competition_id).all()
    number_of_weight_categories = len(list(all_weight_category_data))
    # определяем первую категорию

    first_weight_category_data = WeightcategoriesDB.query.filter_by(competition_id=competition_id).order_by(
        asc(WeightcategoriesDB.sort_index)).first()
    first_weight_category_id = first_weight_category_data.weight_cat_id

    last_weight_category_data = WeightcategoriesDB.query.filter_by(competition_id=competition_id).order_by(
        desc(WeightcategoriesDB.sort_index)).first()
    last_weight_category_id = first_weight_category_data.weight_cat_id

    competition_id = weight_cat_data.competition_id
    regs_data = RegistrationsDB.query.filter_by(weight_cat_id=weight_cat_id).all()
    number_of_weight_cat_regs = len(list(regs_data))
    # предыдущая категория
    prev_weight_category_data = db.session.query(WeightcategoriesDB).order_by(
        WeightcategoriesDB.sort_index.desc()).filter(
        WeightcategoriesDB.sort_index < current_weight_category_sort_index).first()

    # следующая категория
    next_weight_category_data = db.session.query(WeightcategoriesDB).order_by(
        WeightcategoriesDB.sort_index.asc()).filter(
        WeightcategoriesDB.sort_index > current_weight_category_sort_index).first()

    # ВАРИАНТ 1: категория является первой
    if current_weight_category_id == first_weight_category_id:
        # нужно проверить какое количество категорий.
        # две или три
        if number_of_weight_categories == 2:
            # нужно проверить есть ли в последней категории регистрации. И если есть, то тогда отменить удаление
            # потому что удалять надо обе сразу
            # количество регистраций в текущей категории
            print("две категории ")

            # next_weight_category_data.weight_category_name = f"Свыше {weight_value_to_form} кг"

    if next_weight_category_data:
        print("next_weight_category_data.weight_category_name: ", next_weight_category_data.weight_category_name)

    if prev_weight_category_data:
        # проверяем является ли предыдущая категория первой

        print(prev_weight_category_data.weight_category_name)
    else:
        print("нет предыдущей")

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

    return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=4))


@home.route('/registration_delete/<int:reg_id>/', methods=["POST", "GET"])
def registration_delete(reg_id):
    reg_data = RegistrationsDB.query.filter_by(reg_id=reg_id).first()
    reg_id = reg_data.reg_id
    competition_id = reg_data.competition_id
    fights_data_red = FightsDB.query.filter_by(red_fighter_id=reg_id).all()
    fights_data_blue = FightsDB.query.filter_by(blue_fighter_id=reg_id).all()
    number_of_fights = len(list(fights_data_red)) + len(list(fights_data_blue))

    if number_of_fights > 0:
        flash(f"Количество связанных поединков: {number_of_fights}. Сначала удалите связанные поединки.",
              'alert-danger')
    else:
        # удаление бэклогов, связанных с регистрацией
        backlogs_data = BacklogDB.query.filter_by(reg_id=reg_id).all()
        try:
            for backlog in backlogs_data:
                db.session.delete(backlog)
                db.session.commit()
        except:
            pass

        # удаление кандидатов, связанных с регистрацией
        candidates_data = FightcandidateDB.query.filter_by(red_candidate_reg_id=reg_id).all()
        try:
            for candidate in candidates_data:
                db.session.delete(candidate)
                db.session.commit()
        except:
            pass
        candidates_data = FightcandidateDB.query.filter_by(blue_candidate_reg_id=reg_id).all()
        try:
            for candidate in candidates_data:
                db.session.delete(candidate)
                db.session.commit()
        except:
            pass

        db.session.delete(reg_data)
        try:
            db.session.commit()
            flash(f'Регистрация удалена', 'alert-success')

        except Exception as e:
            print(e)
            flash(f'Что-то пошло не так. Ошибка: {e}', 'alert-danger')
            db.session.rollback()

    return redirect(url_for('home.comp2', competition_id=competition_id, active_tab_name=2))


@home.route('/rounds_edit/<int:competition_id>/<int:weight_cat_id>//<int:age_cat_id>', methods=["POST", "GET"])
def rounds_edit(competition_id, weight_cat_id, age_cat_id):
    if request.method == 'POST':

        all_round_data = RoundsDB.query.filter_by(competition_id=competition_id, weight_cat_id=weight_cat_id,
                                                  age_cat_id=age_cat_id).all()

        # получаем список id раундов
        round_id_list = []
        for round_data in all_round_data:
            round_id = round_data.round_id
            round_id_list.append(round_id)
        # итерируемся по списку id

        for round_id in round_id_list:
            round_data = RoundsDB.query.get(round_id)
            round_id_from_form = str(round_id)
            round_name = (request.form[round_id_from_form])
            round_data.round_name = round_name
            try:
                db.session.commit()
            except Exception as e:
                print(e)
                db.session.rollback()

        return redirect(url_for('home.fights', competition_id=competition_id))


@home.route('/delete_round_ajaxfile', methods=["POST", "GET"])
def delete_round_ajaxfile():
    if request.method == 'POST':
        round_id = int(request.form['round_id'])
        competition_id = int(request.form['competition_id'])
        weight_cat_id = int(request.form['weight_cat_id'])
        age_cat_id = int(request.form['age_cat_id'])
        # проверяем есть ли созданные поединки в данном круге
        fights_data_in_round = FightsDB.query.filter_by(round_number=round_id).all()
        number_of_fights_data_in_round = len(list(fights_data_in_round))
        # print("number_of_fights_data_in_round: ", number_of_fights_data_in_round)
        # Проверяем, чтобы остался хотя бы один раунд
        # Коичество раундов
        rounds_data = RoundsDB.query.filter_by(competition_id=competition_id, weight_cat_id=weight_cat_id,
                                               age_cat_id=age_cat_id).all()
        number_of_rounds_data = len(list(rounds_data))
        if number_of_rounds_data > 1:
            if number_of_fights_data_in_round > 0:
                alert_trigger = 1
            else:
                alert_trigger = 0
                # записи в бэклоге в удаляемом раунде
                backlog_data = BacklogDB.query.filter_by(round_id=round_id).all()
                try:
                    for backlog in backlog_data:
                        db.session.delete(backlog)
                        db.session.commit()
                except:
                    pass
                # записи кандидатов на удаление в удаляемом раунде
                candidates_data = FightcandidateDB.query.filter_by(round_id=round_id).all()
                try:
                    for candidate in candidates_data:
                        db.session.delete(candidate)
                        db.session.commit()
                except:
                    pass
                round_to_delete = RoundsDB.query.get(round_id)

                try:
                    db.session.delete(round_to_delete)
                    db.session.commit()
                except Exception as e:
                    print(f'Круг не удалился. Ошибка: {e}')
                    db.session.rollback()
        else:
            alert_trigger = 2  # если alert_trigger =2 значит показываем сообщение на странице, что последний круг удалять нельзя

        rounds_data = RoundsDB.query.filter_by(competition_id=competition_id, weight_cat_id=weight_cat_id,
                                               age_cat_id=age_cat_id).all()

        rounds_selector_data = {}
        for round_data in rounds_data:
            rounds_selector_data[round_data.round_name] = round_data.round_id
        # print("rounds_selector_data: ", rounds_selector_data)

        return jsonify({'htmlresponse': render_template('response_rounds_data.html', competition_id=competition_id,
                                                        weight_cat_id=weight_cat_id, age_cat_id=age_cat_id,
                                                        rounds_data=rounds_data), 'weight_cat_id': weight_cat_id,
                        'age_cat_id': age_cat_id, 'alert_trigger': alert_trigger})


@home.route('/add_rounds_ajaxfile', methods=["POST", "GET"])
def add_rounds_ajaxfile():
    if request.method == 'POST':
        competition_id = int(request.form['competition_id'])
        weight_cat_id = int(request.form['weight_cat_id'])
        age_cat_id = int(request.form['age_cat_id'])
        new_round_value = request.form['new_round_value']
        # print("new_round_value: ", new_round_value)

        new_round = RoundsDB(round_name=new_round_value,
                             competition_id=competition_id,
                             weight_cat_id=weight_cat_id,
                             age_cat_id=age_cat_id)
        db.session.add(new_round)
        try:
            db.session.commit()
        except Exception as e:
            print(e)
            db.session.rollback()

        # определяем есть ли регистрации, которыми можно заполнить созданный круг

        # последний созданный раунд 
        last_round_data = RoundsDB.query.order_by(desc(RoundsDB.round_id)).first()
        last_round_id = last_round_data.round_id
        # получаем список id в текущем бэклоге
        backlogs_data = BacklogDB.query.filter_by(competition_id=competition_id, round_id=last_round_id).all()
        backlogs_data_id_list = []
        try:
            for backlog in backlogs_data:
                backlog_id = backlog.id
                backlogs_data_id_list.append(backlog_id)
        except:
            pass

        potencial_backlog_data = RegistrationsDB.query.filter_by(competition_id=competition_id,
                                                                 weight_cat_id=weight_cat_id, age_cat_id=age_cat_id,
                                                                 activity_status=1).all()
        try:
            for reg_data in potencial_backlog_data:
                reg_id = reg_data.reg_id
                if reg_id not in backlogs_data_id_list:
                    new_backlog = BacklogDB(reg_id=reg_data.reg_id, competition_id=reg_data.competition_id,
                                            round_id=last_round_id)
                    db.session.add(new_backlog)
                    db.session.commit()
        except:
            pass

        rounds_data = RoundsDB.query.filter_by(competition_id=competition_id, weight_cat_id=weight_cat_id,
                                               age_cat_id=age_cat_id).all()
        rounds_selector_data = {}
        for round_data in rounds_data:
            rounds_selector_data[round_data.round_name] = round_data.round_id
        # print("rounds_selector_data: ", rounds_selector_data)

        return jsonify({'htmlresponse': render_template('response_rounds_data.html', competition_id=competition_id,
                                                        weight_cat_id=weight_cat_id, age_cat_id=age_cat_id,
                                                        rounds_data=rounds_data), 'weight_cat_id': weight_cat_id,
                        'age_cat_id': age_cat_id
                        })


@home.route('/up_queue_ajaxfile', methods=["POST", "GET"])
def up_queue_ajaxfile():
    if request.method == 'POST':
        queue_id = int(request.form['queue_id'])
        selected_queue_data = QueueDB.query.get(queue_id)
        current_queue_sort_index = selected_queue_data.queue_sort_index
        current_tatami_id = selected_queue_data.tatami_id
        # выборка очереди на текущем татами
        tatami_queue_data = QueueDB.query.filter_by(tatami_id=current_tatami_id).all()
        # выборка записей очереди, которые находятся выше чем текущая запись
        upper_tatami_queue_data = db.session.query(QueueDB).filter(
            QueueDB.queue_sort_index < current_queue_sort_index).filter(QueueDB.tatami_id == current_tatami_id).all()

        competition_id = selected_queue_data.competition_id
        move_object_selector = request.form['move_object_selector']
        tatami_id = int(request.form['selecttatami'])
        # print("move_object_selector: ", move_object_selector)
        if move_object_selector == "move_fight":
            # получаем последнюю запись в выборке элементов, которые находятся сверху
            try:
                upper_sibling_data = db.session.query(QueueDB).filter(
                    QueueDB.queue_sort_index < current_queue_sort_index).filter(
                    QueueDB.tatami_id == current_tatami_id).order_by(
                    desc(QueueDB.queue_sort_index)).first()
                current_upper_sibling_sort_index = upper_sibling_data.queue_sort_index

                # меняем сорт индекс у верхнего элемента
                upper_sibling_data.queue_sort_index = current_upper_sibling_sort_index + 1
                selected_queue_data.queue_sort_index = current_queue_sort_index - 1
                # print("я здесь")
                try:
                    db.session.commit()
                except Exception as e:
                    print("ошибка ", e)

            except:
                pass

        elif move_object_selector == "move_category":
            # получаем выборку категории выбранной очереди
            selected_queue_fight_id = selected_queue_data.fight_id
            fight_data = FightsDB.query.get(selected_queue_fight_id)
            reg_data = RegistrationsDB.query.get(fight_data.red_fighter_id)
            weight_cat_id = reg_data.weight_cat_id
            age_cat_id = reg_data.age_cat_id
            # получаем выборку боев в очереди в данной категории
            # итерируемся по очереди
            queue_competition_data = QueueDB.query.filter_by(competition_id=competition_id).all()

            # ищем данные категории, которая находится выше текущей
            # получаем данные поединков, которые находятся выше
            try:
                upper_sibling_data = db.session.query(QueueDB).filter(
                    QueueDB.queue_sort_index < current_queue_sort_index).filter(
                    QueueDB.tatami_id == current_tatami_id).order_by(
                    desc(QueueDB.queue_sort_index)).first()
                upper_sibling_sort_index = upper_sibling_data.queue_sort_index
                upper_queue_fight_data = FightsDB.query.get(upper_sibling_data)
                reg_upper_queue_fight_data = RegistrationsDB.query.get(upper_queue_fight_data.red_fighter_id)
                upper_queue_weight_cat_id = reg_upper_queue_fight_data.weight_cat_id
                upper_queue_age_cat_id = reg_upper_queue_fight_data.age_cat_id


            except:
                pass

            fights_list = []
            for queue in queue_competition_data:
                current_queue_fight_id = queue.fight_id
                current_queue_fight_data = FightsDB.query.get(current_queue_fight_id)
                reg_current_queue_data = RegistrationsDB.query.get(current_queue_fight_data.red_fighter_id)
                current_queue_weight_cat_id = reg_current_queue_data.weight_cat_id
                current_queue_age_cat_id = reg_current_queue_data.age_cat_id
                if current_queue_weight_cat_id == weight_cat_id and current_queue_age_cat_id == age_cat_id:
                    fights_list.append(current_queue_fight_id)

            selected_category_queue_data = db.session.query(QueueDB).filter(QueueDB.fight_id.in_(fights_list)).all()

        queue_data = QueueDB.query.filter_by(tatami_id=tatami_id).order_by(QueueDB.queue_sort_index).all()
        if tatami_id == 0:
            queue_data = QueueDB.query.filter_by(competition_id=competition_id).order_by(
                asc(QueueDB.queue_sort_index)).all()
        return jsonify({'htmlresponse': render_template('queue_list.html', queue_data=queue_data)})


@home.route('/queue_ajaxfile', methods=["POST", "GET"])
def queue_ajaxfile():
    if request.method == 'POST':
        selecttatami = int(request.form['selecttatami'])
        # queue_data = FightsDB.query.filter_by(tatami_id=selecttatami).order_by(
        #         asc(FightsDB.queue_sort_index)).all()
        queue_data = FightsDB.query.filter_by(tatami_id=selecttatami).order_by(and_(FightsDB.queue_catagory_sort_index, FightsDB.queue_sort_index)).all()
        # print("queue_data: ", queue_data)        
        # print("queue_data: ", queue_data)
        return jsonify({'htmlresponse': render_template('queue_list.html', queue_data=queue_data)})


@home.route('/add_round_ajaxfile', methods=["POST", "GET"])
def add_round_ajaxfile():
    if request.method == 'POST':
        selectedweightcategory = 0
        selectedagecategory = 0
        competition_id = int(request.form['competition_id'])
        try:
            selectedweightcategory = int(request.form['selectedweightcategory'])
        except:
            pass
        try:
            selectedagecategory = int(request.form['selectedagecategory'])
        except:
            pass
        if selectedweightcategory != 0 and selectedagecategory != 0:
            weight_cat_id = selectedweightcategory
            age_cat_id = selectedagecategory
            new_round_title = new_round_name.new_round_name_func(competition_id, weight_cat_id, age_cat_id)

            return jsonify({'htmlresponse': render_template('response_new_round.html', competition_id=competition_id,
                                                            weight_cat_id=weight_cat_id, age_cat_id=age_cat_id,
                                                            new_round_title=new_round_title)})


@home.route('/edit_rounds_ajaxfile', methods=["POST", "GET"])
def edit_rounds_ajaxfile():
    if request.method == 'POST':
        selectedweightcategory = 0
        selectedagecategory = 0
        competition_id = int(request.form['competition_id'])
        selectedweightcategory = int(request.form['selectedweightcategory'])
        selectedagecategory = int(request.form['selectedagecategory'])
        # print("competition_id: ", competition_id, "selectedweightcategory: ", selectedweightcategory,
        #       "selectedagecategory: ", selectedagecategory)
        if selectedweightcategory != 0 and selectedagecategory != 0:
            weight_cat_id = selectedweightcategory
            age_cat_id = selectedagecategory
            rounds_data = RoundsDB.query.filter_by(competition_id=competition_id, weight_cat_id=weight_cat_id,
                                                   age_cat_id=age_cat_id).all()
            # print("rounds_data: ", rounds_data)
            return jsonify({'htmlresponse': render_template('response_rounds_data.html', competition_id=competition_id,
                                                            weight_cat_id=weight_cat_id, age_cat_id=age_cat_id,
                                                            rounds_data=rounds_data)})


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


@home.route('/add_weight_category_with_data_ajaxfile', methods=["POST", "GET"])
def add_weight_category_with_data_ajaxfile():
    if request.method == 'POST':
        weight_cat_id = int(request.form['weight_cat_id'])
        current_weight_category_data = WeightcategoriesDB.query.get(weight_cat_id)
        current_weight_category_from_value = current_weight_category_data.weight_category_start
        current_weight_category_to_value = current_weight_category_data.weight_category_finish
        current_weight_category_weight_cat_id = current_weight_category_data.weight_cat_id
        current_weight_category_sort_index = current_weight_category_data.sort_index
        competition_id = current_weight_category_data.competition_id

        # определяем следующую категорию
        next_weight_category_data = db.session.query(WeightcategoriesDB).order_by(
            WeightcategoriesDB.sort_index.asc()).filter(
            WeightcategoriesDB.sort_index > current_weight_category_sort_index).first()

        # если следующая категория существует
        if next_weight_category_data:
            next_weight_category_data_weight_cat_id = next_weight_category_data.weight_cat_id

            # определяем является ли следующая категория последней
            last_weight_category_data = WeightcategoriesDB.query.filter_by(competition_id=competition_id).order_by(
                desc(WeightcategoriesDB.sort_index)).first()
            last_weight_category_data_from_value = last_weight_category_data.weight_category_start
            last_weight_category_data_to_value = last_weight_category_data.weight_category_finish
            last_weight_category_data_weight_cat_id = last_weight_category_data.weight_cat_id

            # Если следующая категория - это последняя категория
            if next_weight_category_data_weight_cat_id == last_weight_category_data_weight_cat_id:
                value_from = current_weight_category_to_value
                status_of_last_record = 1
                from_field_max = current_weight_category_to_value

            else:
                # print("следующая категория существует - и она НЕ последняя")
                value_from = current_weight_category_to_value
                status_of_last_record = 2
                from_field_max = current_weight_category_to_value
        else:
            # следующей категории нет
            value_from = current_weight_category_from_value
            status_of_last_record = 0
            from_field_max = 1000000 - 1
        from_field_min = current_weight_category_from_value
        return jsonify({'htmlresponse': render_template('response_add_weight_category_with_data.html',
                                                        competition_id=competition_id, weight_cat_id=weight_cat_id,
                                                        weight_category_data=current_weight_category_data,
                                                        value_from=value_from,
                                                        from_field_min=from_field_min,
                                                        from_field_max=from_field_max,
                                                        status_of_last_record=status_of_last_record)})


@home.route('/add_weight_category_ajaxfile', methods=["POST", "GET"])
def add_weight_category_ajaxfile():
    if request.method == 'POST':
        competition_id = int(request.form['competition_id'])

        return jsonify({'htmlresponse': render_template('response_add_weight_category.html',
                                                        competition_id=competition_id)})


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


@home.route('/new_participant_ajaxfile', methods=["POST", "GET"])
def new_participant_ajaxfile():
    if request.method == 'POST':
        form = ParticipantNewForm()

        return jsonify({'htmlresponse': render_template('response_participant_create.html', form=form)})


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
        competition_data = CompetitionsDB.query.get(competition_id)
        weight_categories_data = WeightcategoriesDB.query.filter_by(competition_id=competition_id).order_by(
            WeightcategoriesDB.sort_index).all()
        age_catagories_data = AgecategoriesDB.query.filter_by(competition_id=competition_id).order_by(
            AgecategoriesDB.sort_index).all()
        last_name = participant_data.participant_last_name

        # print("Добавился ", last_name)
        first_name = participant_data.participant_first_name
        # flash(f"Создана новая регистрация {last_name} {first_name}", 'alert-success')
        # print(reg_data)
        reg_form = RegistrationeditForm()
        competition_date = competition_data.competition_date_start
        # дата рождения бойца
        birthday_date = participant_data.birthday
        date_diff = (competition_date - birthday_date).total_seconds()
        age_years_float = date_diff / (60 * 60 * 24 * 365.25)
        age_years = math.floor(age_years_float)
        # определение возрастной категории
        age_category_data = AgecategoriesDB.query.filter_by(competition_id=competition_id).all()
        default_age_cat = {}
        for age_category in age_category_data:
            age_cat_id = age_category.age_cat_id
            age_category_name = age_category.age_category_name
            age_category_start = age_category.age_category_start
            age_category_finish = age_category.age_category_finish
            if age_years >= age_category_start and age_years < age_category_finish:
                default_age_cat['age_cat_id'] = age_cat_id
                default_age_cat['age_category_name'] = age_category_name

        return jsonify(
            {'htmlresponse': render_template('response_reg_new_2.html',
                                             form=reg_form,
                                             competition_id=competition_id,
                                             participant_data=participant_data,
                                             competition_data=competition_data,
                                             age_years=age_years,
                                             default_age_cat_id=default_age_cat['age_cat_id'],
                                             weight_categories_data=weight_categories_data,
                                             age_catagories_data=age_catagories_data,
                                             )})


@home.route('/delete_age_cat_ajaxfile', methods=["POST", "GET"])
def delete_age_cat_ajaxfile():
    if request.method == 'POST':
        age_cat_id = request.form['age_cat_id']
        age_cat_data = AgecategoriesDB.query.filter_by(age_cat_id=age_cat_id).first()
        return jsonify(
            {'htmlresponse': render_template('response_age_cat_delete.html', age_cat_data=age_cat_data)})


@home.route('/delete_weight_cat_ajaxfile', methods=["POST", "GET"])
def delete_weight_cat_ajaxfile():
    """в рауте delete_weight_cat_ajaxfile - нужно проверять что именно мы пытаемся удалить и дальше уже включать нужный сценарий удаления. Отправляем weight_cat_id в функцию check_delete_weight_category.
В ответ получаем: Сколько всего категорий, Какое положение у текущей категории - первое, второе, предпоследнее, последнее, какая категория предыдущая - первая или больше первой. Какая категория следующая-
последняя или предпоследняя. Проверяем есть ли связанные категории в текущей и в соседях. Если там данные есть, то пишем названия категорий, в которых нудно сначала убрать регистрации и в моделе не даем кнопку Удалить"""
    if request.method == 'POST':
        weight_cat_id = request.form['weight_cat_id']
        weight_cat_data = WeightcategoriesDB.query.get(weight_cat_id)
        competition_id = weight_cat_data.competition_id
        delete_confirmation = check_delete_weight_category.check_delete_weight_category(weight_cat_id)[0]
        text_regs_list = check_delete_weight_category.check_delete_weight_category(weight_cat_id)[1]
        number_of_weight_categories = check_delete_weight_category.check_delete_weight_category(weight_cat_id)[2]

        # text_regs = ", ".join(text_regs_list)

        # Если категорий - 2 и удалять их нельзя
        if delete_confirmation == 0 and (number_of_weight_categories == 2 or number_of_weight_categories == 3):
            return jsonify(
                {'htmlresponse': render_template('response_weight_cat_delete_restricted.html',
                                                 text_regs_list=text_regs_list)})
        # Если категорий - 2 и удалять их можно
        elif delete_confirmation == 1 and number_of_weight_categories == 2:
            return jsonify(
                {'htmlresponse': render_template('response_weight_cat_delete_2_regs.html',
                                                 text_regs_list=text_regs_list, competition_id=competition_id)})

        # Если категорий - 3, удалять можно
        elif delete_confirmation == 1 and number_of_weight_categories == 3:
            weight_cat_id = check_delete_weight_category.check_delete_weight_category(weight_cat_id)[3]
            weight_cat_name = text_regs_list[0]
            return jsonify(
                {'htmlresponse': render_template('response_weight_cat_delete_1_regs.html',
                                                 weight_cat_name=weight_cat_name, competition_id=competition_id,
                                                 weight_cat_id=weight_cat_id)})

        # Если категорий - больше или равно 4, удалять можно
        elif delete_confirmation == 1 and number_of_weight_categories >= 4:
            weight_cat_id = check_delete_weight_category.check_delete_weight_category(weight_cat_id)[3]
            weight_cat_name = text_regs_list[0]
            return jsonify(
                {'htmlresponse': render_template('response_weight_cat_delete_1_regs.html',
                                                 weight_cat_name=weight_cat_name, competition_id=competition_id,
                                                 weight_cat_id=weight_cat_id)})

        weight_cat_data = WeightcategoriesDB.query.filter_by(weight_cat_id=weight_cat_id).first()
        # считаем количество регистраций
        weight_cat_id = weight_cat_data.weight_cat_id
        regs = RegistrationsDB.query.filter_by(weight_cat_id=weight_cat_id).all()
        if regs:
            number_of_regs = len(list(regs))
            return jsonify(
                {'htmlresponse': render_template('response_weight_cat_delete_warning.html',
                                                 weight_cat_data=weight_cat_data,
                                                 number_of_regs=number_of_regs)})
        else:
            number_of_regs = 0
            return jsonify(
                {'htmlresponse': render_template('response_weight_cat_delete.html', weight_cat_data=weight_cat_data,
                                                 number_of_regs=number_of_regs)})


@home.route('/add_tatami_ajaxfile', methods=["POST", "GET"])
def add_tatami_ajaxfile():
    if request.method == 'POST':
        competition_id = int(request.form['competition_id'])
        # print("я тут")

        return jsonify(
            {'htmlresponse': render_template('response_new_tatami.html', competition_id=competition_id)})


@home.route('/new_fight_ajaxfile', methods=["POST", "GET"])
def new_fight_ajaxfile():
    if request.method == 'POST':
        round_id = int(request.form['round_id'])
        tatami_id = int(request.form['tatami_id'])
        round_data = RoundsDB.query.get(round_id)
        competition_id = round_data.competition_id
        candidates_data = FightcandidateDB.query.filter_by(round_id=round_id).first()
        # определяем весовую и возрастную категорию одного из бойцов
        red_candidate_weight_cat_id = candidates_data.red_candidate_reg.weight_cat_id
        red_candidate_age_cat_id = candidates_data.red_candidate_reg.age_cat_id
        if candidates_data:
            red_candidate_reg_id = 0
            blue_candidate_reg_id = 0
            if candidates_data.red_candidate_reg_id:
                red_candidate_reg_id = candidates_data.red_candidate_reg_id
            if candidates_data.blue_candidate_reg_id:
                blue_candidate_reg_id = candidates_data.blue_candidate_reg_id
            if red_candidate_reg_id != 0 and blue_candidate_reg_id != 0:
                # удаляем кандидатов
                candidates_data.red_candidate_reg_id = 0
                candidates_data.blue_candidate_reg_id = 0
                
                # определям значение сорт индекса на текущем татами
                queue_data = FightsDB.query.filter_by(tatami_id=tatami_id).all()
                max_sort_index = 0
                if queue_data:
                    max_sort_index_data = db.session.query(func.max(FightsDB.queue_sort_index)).first()
                    max_sort_index = list(max_sort_index_data)[0]
                
                max_sort_index = max_sort_index + 1
                queue_sort_index = max_sort_index
                
                
                # print("candidates_data ", candidates_data.red_candidate_reg.weight_cat_id)
                
                
                
                fights_in_tatami_data = FightsDB.query.filter_by(tatami_id=tatami_id).all()
                # итерируемся по выборке с поединками
                max_category_sort_index_data = 0
                if fights_in_tatami_data:
                    max_category_sort_index_data = db.session.query(func.max(FightsDB.queue_catagory_sort_index)).first()
                    max_category_sort_index_data = list(max_category_sort_index_data)[0]     
                
                # если уже есть поединки в текущей весовой и возрастной категории. то в новый бой надо записать текущее значение
                # в этом случае бой добавится последним в категории, но останется в текущем месте в стеке категории
                fights_list = []
                for fight in fights_in_tatami_data:
                    fight_id = fight.fight_id
                    weight_cat_id = fight.red_fighter.weight_cat_id
                    age_cat_id = fight.red_fighter.age_cat_id
                    if weight_cat_id == red_candidate_weight_cat_id and age_cat_id == red_candidate_age_cat_id:
                        fights_list.append(fight_id)
                fights_data_temp =db.session.query(FightsDB).filter(FightsDB.fight_id.in_(fights_list)).all()
                queue_catagory_sort_index = 0
                if fights_data_temp:
                    fight_data_temp =db.session.query(FightsDB).filter(FightsDB.fight_id.in_(fights_list)).first()
                    queue_catagory_sort_index = fight_data_temp.queue_catagory_sort_index
                else:
                    # если данных о поединках нет, значит этотт поединок будет первым в этой категории
                    # прибавляем единицу к текущему максимальному значению
                    queue_catagory_sort_index = max_category_sort_index_data + 1
                    
               
                
                
              
                # создаем новый бой
                new_fight = FightsDB(
                    competition_id=competition_id,
                    round_number=round_id,
                    red_fighter_id=red_candidate_reg_id,
                    blue_fighter_id=blue_candidate_reg_id,
                    tatami_id=tatami_id,
                    queue_sort_index=queue_sort_index,
                    queue_catagory_sort_index=queue_catagory_sort_index
                )
                db.session.add(new_fight)
                db.session.commit()

                # создаем очередь для боя
                # определяем последний созданный бой
                last_created_fight = FightsDB.query.filter_by(competition_id=competition_id,
                                                              round_number=round_id).order_by(
                    desc(FightsDB.fight_id)).first()
                fight_id = last_created_fight.fight_id
                # определяем последний сорт индекс в очереди
               
                # new_queue = QueueDB(
                #     tatami_id=tatami_id,
                #     competition_id=competition_id,
                #     fight_id=fight_id,
                #     queue_sort_index=max_sort_index
                # )
                # db.session.add(new_queue)
                # db.session.commit()

                backlog_data = BacklogDB.query.filter_by(round_id=round_id).all()
                fights_data = FightsDB.query.filter_by(round_number=round_id).all()

                return jsonify(
                    {'htmlresponse_red_candidate': render_template('empty_candidate.html'),
                     'htmlresponse_blue_candidate': render_template('empty_candidate.html'),
                     'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                     'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),
                     })


@home.route('/delete_fight_ajaxfile', methods=["POST", "GET"])
def delete_fight_ajaxfile():
    if request.method == 'POST':
        fight_id = int(request.form['fight_id'])
        fight_data = FightsDB.query.get(fight_id)
        fight_status = fight_data.fight_status
        red_fighter_id = fight_data.red_fighter_id
        blue_fighter_id = fight_data.blue_fighter_id
        round_id = fight_data.round_number
        competition_id = fight_data.competition_id
        if fight_status == 0:
            # удаляем очередь, связанную с боем
            queue_data = QueueDB.query.filter_by(fight_id=fight_id).first()
            if queue_data:
                db.session.delete(queue_data)
            # удаляем бой
            db.session.delete(fight_data)
            # создаем записи в бэклоге
            new_backlog_red_record = BacklogDB(
                reg_id=red_fighter_id,
                competition_id=competition_id,
                round_id=round_id
            )
            new_backlog_blue_record = BacklogDB(
                reg_id=blue_fighter_id,
                competition_id=competition_id,
                round_id=round_id
            )
            db.session.add(new_backlog_red_record)
            db.session.add(new_backlog_blue_record)
            db.session.commit()

            candidates_data = FightcandidateDB.query.filter_by(round_id=round_id).first()
            backlog_data = BacklogDB.query.filter_by(round_id=round_id).all()

            red_candidate_reg_id = 0
            blue_candidate_reg_id = 0
            # если запись о кандидатах уже есть
            if candidates_data:
                if candidates_data.red_candidate_reg_id:
                    red_candidate_reg_id = candidates_data.red_candidate_reg_id
                if candidates_data.blue_candidate_reg_id:
                    blue_candidate_reg_id = candidates_data.blue_candidate_reg_id

                if red_candidate_reg_id == 0 and blue_candidate_reg_id == 0:
                    backlog_data = BacklogDB.query.filter_by(round_id=round_id).all()
                    fights_data = FightsDB.query.filter_by(round_number=round_id).all()
                    return jsonify(
                        {'htmlresponse_red_candidate': render_template('empty_candidate.html'),
                         'htmlresponse_blue_candidate': render_template('empty_candidate.html'),
                         'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                         'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),

                         })

                elif red_candidate_reg_id != 0 and blue_candidate_reg_id == 0:
                    candidates_data = FightcandidateDB.query.filter_by(round_id=round_id).first()
                    red_candidate_last_name = candidates_data.red_candidate_reg.registration_participant.participant_last_name
                    red_candidate_first_name = candidates_data.red_candidate_reg.registration_participant.participant_first_name

                    backlog_data = BacklogDB.query.filter_by(round_id=round_id).all()
                    fights_data = FightsDB.query.filter_by(round_number=round_id).all()
                    return jsonify(
                        {'htmlresponse_red_candidate': render_template('red_candidate.html',
                                                                       red_candidate_last_name=red_candidate_last_name,
                                                                       red_candidate_first_name=red_candidate_first_name,
                                                                       round_id=round_id),
                         'htmlresponse_blue_candidate': render_template('empty_candidate.html'),
                         'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                         'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),

                         })


                elif red_candidate_reg_id == 0 and blue_candidate_reg_id != 0:
                    candidates_data = FightcandidateDB.query.filter_by(round_id=round_id).first()
                    blue_candidate_last_name = candidates_data.blue_candidate_reg.registration_participant.participant_last_name
                    blue_candidate_first_name = candidates_data.blue_candidate_reg.registration_participant.participant_first_name
                    backlog_data = BacklogDB.query.filter_by(round_id=round_id).all()
                    fights_data = FightsDB.query.filter_by(round_number=round_id).all()
                    return jsonify(
                        {'htmlresponse_red_candidate': render_template('empty_candidate.html'),
                         'htmlresponse_blue_candidate': render_template('blue_candidate.html',
                                                                        blue_candidate_last_name=blue_candidate_last_name,
                                                                        blue_candidate_first_name=blue_candidate_first_name,
                                                                        round_id=round_id),
                         'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                         'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),

                         })

                else:
                    candidates_data = FightcandidateDB.query.filter_by(round_id=round_id).first()
                    red_candidate_last_name = candidates_data.red_candidate_reg.registration_participant.participant_last_name
                    red_candidate_first_name = candidates_data.red_candidate_reg.registration_participant.participant_first_name
                    blue_candidate_last_name = candidates_data.blue_candidate_reg.registration_participant.participant_last_name
                    blue_candidate_first_name = candidates_data.blue_candidate_reg.registration_participant.participant_first_name
                    backlog_data = BacklogDB.query.filter_by(round_id=round_id).all()
                    fights_data = FightsDB.query.filter_by(round_number=round_id).all()
                    return jsonify(
                        {'htmlresponse_red_candidate': render_template('red_candidate.html',
                                                                       red_candidate_last_name=red_candidate_last_name,
                                                                       red_candidate_first_name=red_candidate_first_name,
                                                                       round_id=round_id),
                         'htmlresponse_blue_candidate': render_template('blue_candidate.html',
                                                                        blue_candidate_last_name=blue_candidate_last_name,
                                                                        blue_candidate_first_name=blue_candidate_first_name,
                                                                        round_id=round_id),
                         'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                         'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),

                         })



            else:
                backlog_data = BacklogDB.query.filter_by(round_id=round_id).all()
                fights_data = FightsDB.query.filter_by(round_number=round_id).all()
                return jsonify(
                    {'htmlresponse_red_candidate': render_template('empty_candidate.html'),
                     'htmlresponse_blue_candidate': render_template('empty_candidate.html'),
                     'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                     'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),

                     })


@home.route('/delete_blue_candidate_ajaxfile', methods=["POST", "GET"])
def delete_blue_candidate_ajaxfile():
    if request.method == 'POST':
        round_id = int(request.form['round_id'])
        round_data = RoundsDB.query.get(round_id)
        competition_id = round_data.competition_id
        candidates_data = FightcandidateDB.query.filter_by(round_id=round_id).first()
        reg_id = candidates_data.blue_candidate_reg_id
        candidates_data.blue_candidate_reg_id = 0
        blue_candidate_reg_id = 0
        # Создаем запись в бэклоге
        new_backlog_record = BacklogDB(
            reg_id=reg_id,
            competition_id=competition_id,
            round_id=round_id
        )
        db.session.add(new_backlog_record)
        db.session.commit()
        candidates_data = FightcandidateDB.query.filter_by(round_id=round_id).first()
        red_candidate_reg_id = 0

        if candidates_data.red_candidate_reg_id:
            red_candidate_reg_id = candidates_data.red_candidate_reg_id
        if candidates_data.blue_candidate_reg_id:
            blue_candidate_reg_id = candidates_data.blue_candidate_reg_id

        if red_candidate_reg_id == 0 and blue_candidate_reg_id == 0:
            backlog_data = BacklogDB.query.filter_by(round_id=round_id).all()
            fights_data = FightsDB.query.filter_by(round_number=round_id).all()
            return jsonify(
                {'htmlresponse_red_candidate': render_template('empty_candidate.html'),
                 'htmlresponse_blue_candidate': render_template('empty_candidate.html'),
                 'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                 'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),
                 })

        else:
            candidates_data = FightcandidateDB.query.filter_by(round_id=round_id).first()
            red_candidate_last_name = candidates_data.red_candidate.registration_participant.participant_last_name
            red_candidate_first_name = candidates_data.red_candidate.registration_participant.participant_first_name
            backlog_data = BacklogDB.query.filter_by(round_id=round_id).all()
            fights_data = FightsDB.query.filter_by(round_number=round_id).all()
            return jsonify(
                {'htmlresponse_blue_candidate': render_template('empty_candidate.html'),
                 'htmlresponse_red_candidate': render_template('red_candidate.html',
                                                               red_candidate_last_name=red_candidate_last_name,
                                                               red_candidate_first_name=red_candidate_first_name,
                                                               round_id=round_id),
                 'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                 'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),
                 })


@home.route('/delete_red_candidate_ajaxfile', methods=["POST", "GET"])
def delete_red_candidate_ajaxfile():
    if request.method == 'POST':
        round_id = int(request.form['round_id'])
        round_data = RoundsDB.query.get(round_id)
        competition_id = round_data.competition_id
        candidates_data = FightcandidateDB.query.filter_by(round_id=round_id).first()
        reg_id = candidates_data.red_candidate_reg_id
        candidates_data.red_candidate_reg_id = 0
        red_candidate_reg_id = 0
        # Создаем запись в бэклоге
        new_backlog_record = BacklogDB(
            reg_id=reg_id,
            competition_id=competition_id,
            round_id=round_id
        )
        db.session.add(new_backlog_record)
        db.session.commit()
        candidates_data = FightcandidateDB.query.filter_by(round_id=round_id).first()
        blue_candidate_reg_id = 0

        if candidates_data.red_candidate_reg_id:
            red_candidate_reg_id = candidates_data.red_candidate_reg_id
        if candidates_data.blue_candidate_reg_id:
            blue_candidate_reg_id = candidates_data.blue_candidate_reg_id

        if red_candidate_reg_id == 0 and blue_candidate_reg_id == 0:
            backlog_data = BacklogDB.query.filter_by(round_id=round_id).all()
            fights_data = FightsDB.query.filter_by(round_number=round_id).all()
            return jsonify(
                {'htmlresponse_red_candidate': render_template('empty_candidate.html'),
                 'htmlresponse_blue_candidate': render_template('empty_candidate.html'),
                 'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                 'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),
                 })

        else:
            candidates_data = FightcandidateDB.query.filter_by(round_id=round_id).first()
            blue_candidate_last_name = candidates_data.blue_candidate.registration_participant.participant_last_name
            blue_candidate_first_name = candidates_data.blue_candidate.registration_participant.participant_first_name
            backlog_data = BacklogDB.query.filter_by(round_id=round_id).all()
            fights_data = FightsDB.query.filter_by(round_number=round_id).all()
            return jsonify(
                {'htmlresponse_red_candidate': render_template('empty_candidate.html'),
                 'htmlresponse_blue_candidate': render_template('blue_candidate.html',
                                                                blue_candidate_last_name=blue_candidate_last_name,
                                                                blue_candidate_first_name=blue_candidate_first_name,
                                                                round_id=round_id),
                 'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                 'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),
                 })


@home.route('/add_candidate_ajaxfile', methods=["POST", "GET"])
def add_candidate_ajaxfile():
    if request.method == 'POST':
        backlog_id = int(request.form['backlog_id'])
        # удаляем запись из бэклога
        backlog_data_to_delete = BacklogDB.query.get(backlog_id)
        reg_id = backlog_data_to_delete.reg_id
        round_id = backlog_data_to_delete.round_id

        try:
            db.session.commit()
        except Exception as e:
            print(e)
            db.session.rollback()

        # проверяем есть ли свободные записи в FightcandidateDB
        candidates_data = FightcandidateDB.query.filter_by(round_id=round_id).first()

        red_candidate_reg_id = 0
        blue_candidate_reg_id = 0

        # если запись о кандидатах уже есть
        if candidates_data:
            if candidates_data.red_candidate_reg_id:
                red_candidate_reg_id = candidates_data.red_candidate_reg_id
            if candidates_data.blue_candidate_reg_id:
                blue_candidate_reg_id = candidates_data.blue_candidate_reg_id

            if red_candidate_reg_id == 0 and blue_candidate_reg_id == 0:

                # редактируем запись, вписывая в нее красного кандидата
                candidates_data.red_candidate_reg_id = reg_id
                db.session.delete(backlog_data_to_delete)
                db.session.commit()

                candidates_data = FightcandidateDB.query.filter_by(round_id=round_id).first()
                red_candidate_last_name = candidates_data.red_candidate_reg.registration_participant.participant_last_name
                red_candidate_first_name = candidates_data.red_candidate_reg.registration_participant.participant_first_name
                backlog_data = BacklogDB.query.filter_by(round_id=round_id).all()
                fights_data = FightsDB.query.filter_by(round_number=round_id).all()
                return jsonify(
                    {'htmlresponse_red_candidate': render_template('red_candidate.html',
                                                                   red_candidate_last_name=red_candidate_last_name,
                                                                   red_candidate_first_name=red_candidate_first_name,
                                                                   round_id=round_id),
                     'htmlresponse_blue_candidate': render_template('empty_candidate.html'),
                     'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                     'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),

                     })

            elif red_candidate_reg_id != 0 and blue_candidate_reg_id == 0:
                # редактируем запись, вписывая в нее красного кандидата
                candidates_data.blue_candidate_reg_id = reg_id
                db.session.delete(backlog_data_to_delete)
                db.session.commit()
                candidates_data = FightcandidateDB.query.filter_by(round_id=round_id).first()
                red_candidate_last_name = candidates_data.red_candidate_reg.registration_participant.participant_last_name
                red_candidate_first_name = candidates_data.red_candidate_reg.registration_participant.participant_first_name
                blue_candidate_last_name = candidates_data.blue_candidate_reg.registration_participant.participant_last_name
                blue_candidate_first_name = candidates_data.blue_candidate_reg.registration_participant.participant_first_name
                backlog_data = BacklogDB.query.filter_by(round_id=round_id).all()
                fights_data = FightsDB.query.filter_by(round_number=round_id).all()
                return jsonify(
                    {'htmlresponse_red_candidate': render_template('red_candidate.html',
                                                                   red_candidate_last_name=red_candidate_last_name,
                                                                   red_candidate_first_name=red_candidate_first_name,
                                                                   round_id=round_id),
                     'htmlresponse_blue_candidate': render_template('blue_candidate.html',
                                                                    blue_candidate_last_name=blue_candidate_last_name,
                                                                    blue_candidate_first_name=blue_candidate_first_name,
                                                                    round_id=round_id),
                     'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                     'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),

                     })


            elif red_candidate_reg_id == 0 and blue_candidate_reg_id != 0:
                # редактируем запись, вписывая в нее красного кандидата
                candidates_data.red_candidate_reg_id = reg_id
                db.session.delete(backlog_data_to_delete)
                db.session.commit()
                candidates_data = FightcandidateDB.query.filter_by(round_id=round_id).first()
                red_candidate_last_name = candidates_data.red_candidate_reg.registration_participant.participant_last_name
                red_candidate_first_name = candidates_data.red_candidate_reg.registration_participant.participant_first_name
                blue_candidate_last_name = candidates_data.blue_candidate_reg.registration_participant.participant_last_name
                blue_candidate_first_name = candidates_data.blue_candidate_reg.registration_participant.participant_first_name
                backlog_data = BacklogDB.query.filter_by(round_id=round_id).all()
                fights_data = FightsDB.query.filter_by(round_number=round_id).all()
                return jsonify(
                    {'htmlresponse_red_candidate': render_template('red_candidate.html',
                                                                   red_candidate_last_name=red_candidate_last_name,
                                                                   red_candidate_first_name=red_candidate_first_name,
                                                                   round_id=round_id),
                     'htmlresponse_blue_candidate': render_template('blue_candidate.html',
                                                                    blue_candidate_last_name=blue_candidate_last_name,
                                                                    blue_candidate_first_name=blue_candidate_first_name,
                                                                    round_id=round_id),
                     'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                     'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),

                     })

            elif red_candidate_reg_id != 0 and blue_candidate_reg_id != 0:
                # print("все кандидаты заполены")
                candidates_data = FightcandidateDB.query.filter_by(round_id=round_id).first()
                red_candidate_last_name = candidates_data.red_candidate_reg.registration_participant.participant_last_name
                red_candidate_first_name = candidates_data.red_candidate_reg.registration_participant.participant_first_name
                blue_candidate_last_name = candidates_data.blue_candidate_reg.registration_participant.participant_last_name
                blue_candidate_first_name = candidates_data.blue_candidate_reg.registration_participant.participant_first_name
                backlog_data = BacklogDB.query.filter_by(round_id=round_id).all()
                fights_data = FightsDB.query.filter_by(round_number=round_id).all()
                return jsonify(
                    {'htmlresponse_red_candidate': render_template('red_candidate.html',
                                                                   red_candidate_last_name=red_candidate_last_name,
                                                                   red_candidate_first_name=red_candidate_first_name,
                                                                   round_id=round_id),
                     'htmlresponse_blue_candidate': render_template('blue_candidate.html',
                                                                    blue_candidate_last_name=blue_candidate_last_name,
                                                                    blue_candidate_first_name=blue_candidate_first_name,
                                                                    round_id=round_id),
                     'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                     'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),

                     })
            else:
                print("что-то непонятное")


        else:
            # создаем запись в красном кандидате
            new_candidate_record = FightcandidateDB(
                round_id=round_id,
                red_candidate_reg_id=reg_id
            )
            db.session.add(new_candidate_record)
            db.session.delete(backlog_data_to_delete)
            db.session.commit()

            backlog_data = BacklogDB.query.filter_by(round_id=round_id).all()

            candidates_data = FightcandidateDB.query.filter_by(round_id=round_id).first()

            red_candidate_last_name = candidates_data.red_candidate_reg.registration_participant.participant_last_name
            red_candidate_first_name = candidates_data.red_candidate_reg.registration_participant.participant_first_name
            fights_data = FightsDB.query.filter_by(round_number=round_id).all()
            return jsonify(
                {'htmlresponse_red_candidate': render_template('red_candidate.html',
                                                               red_candidate_last_name=red_candidate_last_name,
                                                               red_candidate_first_name=red_candidate_first_name,
                                                               round_id=round_id),
                 'htmlresponse_blue_candidate': render_template('empty_candidate.html'),
                 'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                 'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),

                 })


@home.route('/fights_list_ajaxfile', methods=["POST", "GET"])
def fights_list_ajaxfile():
    if request.method == 'POST':
        selectround = int(request.form['selectround'])
        round_data = RoundsDB.query.get(selectround)

        fights_data = FightsDB.query.filter_by(round_number=selectround).all()
        backlog_data = BacklogDB.query.filter_by(round_id=selectround).all()
        candidates_data = FightcandidateDB.query.filter_by(round_id=selectround).first()
        # print("candidates_data: ", candidates_data.blue_candidate_reg_id)
        red_candidate_reg_id = 0
        blue_candidate_reg_id = 0
        if candidates_data:
            if candidates_data.red_candidate_reg_id:
                red_candidate_reg_id = candidates_data.red_candidate_reg_id
            if candidates_data.blue_candidate_reg_id:
                blue_candidate_reg_id = candidates_data.blue_candidate_reg_id

        if red_candidate_reg_id == 0 and blue_candidate_reg_id == 0:
            return jsonify(
                {'htmlresponse_red_candidate': render_template('empty_candidate.html'),
                 'htmlresponse_blue_candidate': render_template('empty_candidate.html'),
                 'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                 'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),

                 })
        elif red_candidate_reg_id != 0 and blue_candidate_reg_id == 0:
            red_candidate_last_name = candidates_data.red_candidate_reg.registration_participant.participant_last_name
            red_candidate_first_name = candidates_data.red_candidate_reg.registration_participant.participant_first_name
            return jsonify(
                {'htmlresponse_red_candidate': render_template('red_candidate.html',
                                                               red_candidate_last_name=red_candidate_last_name,
                                                               red_candidate_first_name=red_candidate_first_name,
                                                               round_id=selectround),
                 'htmlresponse_blue_candidate': render_template('empty_candidate.html'),
                 'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                 'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),

                 })
        elif red_candidate_reg_id == 0 and blue_candidate_reg_id != 0:
            blue_candidate_last_name = candidates_data.blue_candidate_reg.registration_participant.participant_last_name
            blue_candidate_first_name = candidates_data.blue_candidate_reg.registration_participant.participant_first_name
            return jsonify(
                {'htmlresponse_red_candidate': render_template('empty_candidate.html'),
                 'htmlresponse_blue_candidate': render_template('blue_candidate.html',
                                                                blue_candidate_last_name=blue_candidate_last_name,
                                                                blue_candidate_first_name=blue_candidate_first_name,
                                                                round_id=selectround),
                 'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                 'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),

                 })
        elif red_candidate_reg_id != 0 and blue_candidate_reg_id != 0:
            red_candidate_last_name = candidates_data.red_candidate_reg.registration_participant.participant_last_name
            red_candidate_first_name = candidates_data.red_candidate_reg.registration_participant.participant_first_name
            blue_candidate_last_name = candidates_data.blue_candidate_reg.registration_participant.participant_last_name
            blue_candidate_first_name = candidates_data.blue_candidate_reg.registration_participant.participant_first_name
            return jsonify(
                {'htmlresponse_red_candidate': render_template('red_candidate.html',
                                                               red_candidate_last_name=red_candidate_last_name,
                                                               red_candidate_first_name=red_candidate_first_name,
                                                               round_id=selectround),
                 'htmlresponse_blue_candidate': render_template('blue_candidate.html',
                                                                blue_candidate_last_name=blue_candidate_last_name,
                                                                blue_candidate_first_name=blue_candidate_first_name,
                                                                round_id=selectround),
                 'htmlresponse_backlog': render_template('backlog.html', backlog_data=backlog_data),
                 'htmlresponse_fights': render_template('fights_in_round.html', fights_data=fights_data),

                 })


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
        weight_categories_data = WeightcategoriesDB.query.filter_by(competition_id=competition_id).order_by(
            WeightcategoriesDB.sort_index).all()
        age_catagories_data = AgecategoriesDB.query.filter_by(competition_id=competition_id).order_by(
            AgecategoriesDB.sort_index).all()

        # считаем количество полных лет на дату соревнования
        # дата соревнования
        competition_date = reg_data.registration_comp.competition_date_start
        # дата рождения бойца
        birthday_date = reg_data.registration_participant.birthday
        date_diff = (competition_date - birthday_date).total_seconds()
        age_years_float = date_diff / (60 * 60 * 24 * 365.25)
        age_eyars = math.floor(age_years_float)

        return jsonify({'htmlresponse': render_template('response_reg_edit.html', form=reg_form, reg_data=reg_data,
                                                        weight_categories_data=weight_categories_data,
                                                        age_catagories_data=age_catagories_data,
                                                        competition_id=competition_id, age_eyars=age_eyars)})


# Handler for a message received over 'connect' channel
@socketio.on('connect')
def test_connect():
    emit('after connect', {'data': 'Lets dance'})


values = {}


@socketio.on('save_round_selector_data')
def save_round_selector_data(received_message):
    values['selectround'] = received_message['selectround']
    # print("selectround: ", values['selectround'])


@socketio.on('define_rounds_data')
def define_rounds_data(received_message):
    values['selectedweightcategory'] = received_message['selectedweightcategory']
    values['selectedagecategory'] = received_message['selectedagecategory']

    # print("values: ", values)

    weight_cat_id = int(values['selectedweightcategory'])
    age_cat_id = int(values['selectedagecategory'])

    weight_cat_data = WeightcategoriesDB.query.get(weight_cat_id)
    competition_id = weight_cat_data.competition_id
    rounds_data = RoundsDB.query.filter_by(competition_id=competition_id, weight_cat_id=weight_cat_id,
                                           age_cat_id=age_cat_id).all()
    # print("rounds_data: ", rounds_data)
    # кол-во раундов в выборке
    number_of_rounds = len(list(rounds_data))
    rounds_selector_data = {}
    if number_of_rounds > 0:
        for round_data in rounds_data:
            rounds_selector_data[round_data.round_name] = round_data.round_id
        # print("rounds_selector_data: ", rounds_selector_data)

    emit('update_round_selector', {'rounds_selector_data': rounds_selector_data}, broadcast=True)

    # print(values)


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
            updated_age_cat['age_cat_id'] = age_cat_id
            updated_age_cat['age_category_name'] = age_category_name
            emit('update_age_category_select_value', {'age_cat_id': age_cat_id, 'age_years': age_years}, broadcast=True)
    #     else:
    #         updated_age_cat['age_cat_id'] = age_category_id
    # age_cat_id = updated_age_cat['age_cat_id']


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
    weight_category_name = WeightcategoriesDB.query.filter_by(
        weight_cat_id=weight_category_id).first().weight_category_name
    # print("default_weight_category: ",new_weight_category)
    updated_weight_cat = {}

    for weight_category in weight_category_data:
        weight_cat_id = weight_category.weight_cat_id
        weight_category_name = weight_category.weight_category_name
        weight_category_start = weight_category.weight_category_start
        weight_category_finish = weight_category.weight_category_finish
        # print("new_weight_value: ", new_weight_value, "weight_category_start: ", weight_category_start, "weight_category_finish: ", weight_category_finish)
        if new_weight_value >= weight_category_start and new_weight_value <= weight_category_finish:
            updated_weight_cat['weight_cat_id'] = weight_cat_id
            updated_weight_cat['weight_category_name'] = weight_category_name
            emit('update_weight_category_select_value', {'data': weight_cat_id}, broadcast=True)
    #     else:

    #       updated_weight_cat['weight_cat_id'] = weight_category_id
    # weight_cat_id = updated_weight_cat['weight_cat_id']
    # emit('update_timer_value', timer_message, broadcast=True)


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


@home.route('/visitor/<int:competition_id>')
def visitor(competition_id):
    competition_data = CompetitionsDB.query.get(competition_id)
    fight_duration = competition_data.fight_duration
    return render_template('visitor.html', fight_duration=fight_duration)


@socketio.on('Timer value changed')
def timer_value_changed(timer_message):
    timer_sent = timer_message
    emit('update_timer_value', timer_sent, broadcast=True)
