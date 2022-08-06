from flask import Blueprint, render_template, redirect, url_for, abort, request, jsonify, flash
from models.models import ParticipantsDB, FightsDB, CompetitionsDB, BacklogDB, RegistrationsDB
from forms.forms import CompetitionForm, RegistrationeditForm
from extensions import extensions
from sqlalchemy import desc, asc
from flask_socketio import SocketIO, emit

db = extensions.db
# db.create_all()
# db.session.commit()
home = Blueprint('home', __name__, template_folder='templates')

socketio = extensions.socketio


@socketio.event
def my_event(message):
    print(message)
    emit('my_response',
         {'data': 'datadata'})


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

@home.route('/')
def home_view():
    return redirect(url_for('home.competitions'))


# Competitions list
@home.route('/competitions')
def competitions():
    competitions_data = CompetitionsDB.query.all()
    return render_template('competitions_list.html', competitions_data=competitions_data)


# competition page
@home.route('/competitions/<int:competition_id>/<active_tab_name>', methods=["POST", "GET"])
def competition_page(competition_id, active_tab_name):
    competition_data = CompetitionsDB.query.get(competition_id)
    form_general_info = CompetitionForm()
    data = {'active_tab_pass': 'competition_general_info'}
    regs = RegistrationsDB.query.filter_by(competition_id=competition_id).join(
        ParticipantsDB.registration_participant).order_by(ParticipantsDB.participant_last_name.asc()).all()

    if int(active_tab_name) == 1:
        data = {'active_tab_pass': 'competition_general_info'}
    elif int(active_tab_name) == 2:
        data = {'active_tab_pass': 'registrations_tab'}
    elif int(active_tab_name) == 3:
        data = {'active_tab_pass': 'competition_settings'}
    else:
        print("непонятно что передано вместо номера вкладки")

    if form_general_info.validate_on_submit():
        flash('Изменения сохранены', 'alert-success')
        competition_data.competition_name = form_general_info.competition_name_form.data
        competition_data.competition_date_start = form_general_info.competition_date_start.data
        competition_data.competition_date_finish = form_general_info.competition_date_finish.data
        competition_data.competition_city = form_general_info.competition_city.data
        try:
            db.session.commit()
        except Exception as e:
            print(e)
            db.session.rollback()

        data = {'active_tab_pass': 'competition_general_info'}

        return render_template('competition.html', competition_data=competition_data,
                               form_general_info=form_general_info, data=data, regs=regs)
    return render_template('competition.html', competition_data=competition_data, form_general_info=form_general_info,
                           data=data, regs=regs)


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
        return redirect(url_for('home.competition_page', competition_id=competition_id, active_tab_name=3))
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
    return render_template('competition.html', competition_data=competition_data, data=data,
                           form_general_info=form_general_info)


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
        return redirect(url_for('home.competition_page', competition_id=competition_id, active_tab_name=1))


# registration list
@home.route('/competitions/<int:competition_id>/registrations')
def registration_list(competition_id):
    competition_data = CompetitionsDB.query.get(competition_id)
    regs = RegistrationsDB.query.filter_by(competition_id=competition_id).first()
    return redirect(url_for('home.competition_page', competition_id=competition_id, active_tab_name=2))


@home.route('/registration_new/<int:competition_id>/', methods=["POST", "GET"])
def registration_new(competition_id):
    form = RegistrationeditForm()
    if form.validate_on_submit():
        new_reg = RegistrationsDB(
            weight_value=form.reg_weight.data,
            competition_id=competition_id,
            participant_id=1
        )
        db.session.add(new_reg)
        db.session.commit()
        new_reg_data = RegistrationsDB.query.filter_by(competition_id=competition_id).order_by(RegistrationsDB.reg_id.desc()).first()

        last_name = new_reg_data.registration_participant.participant_last_name
        first_name = new_reg_data.registration_participant.participant_first_name
        flash(f"Создана новая регистрация {last_name} {first_name}", 'alert-success')

        return redirect(url_for('home.competition_page', competition_id=competition_id, active_tab_name=2))
    else:
        flash(f"Что-то пошло не так с созданием новой регистрации", 'alert-danger')
        return redirect(url_for('home.competition_page', competition_id=competition_id, active_tab_name=2))


@home.route('/registration_edit/<int:reg_id>/', methods=["POST", "GET"])
def registration_edit(reg_id):
    reg_data = RegistrationsDB.query.filter_by(reg_id=reg_id).first()
    competition_id = reg_data.competition_id
    form = RegistrationeditForm()
    if form.validate_on_submit():
        reg_data.weight_value = form.reg_weight.data
        db.session.commit()
        return redirect(url_for('home.competition_page', competition_id=competition_id, active_tab_name=2))


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

    return redirect(url_for('home.competition_page', competition_id=competition_id, active_tab_name=2))


# генерация отображения формы создания соревнования
@home.route('/new_comp_ajaxfile', methods=["POST", "GET"])
def new_comp_ajaxfile():
    if request.method == 'POST':
        form = CompetitionForm()
        return jsonify({'htmlresponse': render_template('response_competition_create.html', form=form)})


@home.route('/new_reg_ajaxfile', methods=["POST", "GET"])
def new_reg_ajaxfile():
    if request.method == 'POST':
        competition_id = request.form['competition_id']
        # reg_data = RegistrationsDB.query.filter_by(reg_id=reg_id).first()
        # print(reg_data)
        reg_form = RegistrationeditForm()
        return jsonify(
            {'htmlresponse': render_template('response_reg_new.html', form=reg_form, competition_id=competition_id)})


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
        # print(reg_data)
        reg_form = RegistrationeditForm()
        return jsonify({'htmlresponse': render_template('response_reg_edit.html', form=reg_form, reg_data=reg_data)})


@home.route('/competition/<int:competition_id>', methods=["POST", "GET"])
def competition_view(competition_id):
    competition_id = competition_id
    # round_number = fight_create_func(round_number_prev)
    last_created_fight = FightsDB.query.filter_by(competition_id=competition_id).order_by(
        desc(FightsDB.fight_id)).first()

    return render_template("competition.html", fight_data=last_created_fight)


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
