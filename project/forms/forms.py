from flask_wtf import FlaskForm
from wtforms import Form, TextAreaField, validators, StringField, SubmitField, IntegerField, DateField, RadioField, \
    DecimalField, BooleanField
from wtforms.validators import InputRequired
from sqlalchemy import desc, asc


class CompetitionForm(FlaskForm):
    competition_name_form = StringField('Наименование турнира', validators=[validators.DataRequired()])
    competition_date_start = DateField('Дата начала соревнования', format='%Y-%m-%d',
                                       validators=[validators.DataRequired()])
    competition_date_finish = DateField('Дата завершения соревнования', format='%Y-%m-%d',
                                        validators=[validators.DataRequired()])
    competition_city = StringField('Город турнира', validators=[validators.DataRequired()])
    submit = SubmitField('Сохранить')


class RegistrationeditForm(FlaskForm):
    reg_weight = DecimalField('Вес, кг', validators=[validators.DataRequired()])
    submit = SubmitField('Сохранить')


class WeightCategoriesForm(FlaskForm):
    sort_index_form_field = IntegerField('Индекс сортировки', validators=[validators.DataRequired()])
    weight_category_name_form_field = StringField('Наименование категории', validators=[validators.DataRequired()])
    weight_from_form_field = IntegerField('Вес От', validators=[validators.InputRequired()])
    weight_to_form_field = IntegerField('Вес До', validators=[validators.DataRequired()])
    submit = SubmitField('Сохранить')

class AgeCategoriesForm(FlaskForm):
    age_sort_index_form_field = IntegerField('Индекс сортировки', validators=[validators.DataRequired()])
    age_category_name_form_field = StringField('Наименование возрастной категории', validators=[validators.DataRequired()])
    age_from_form_field = IntegerField('Возраст От', validators=[validators.InputRequired()])
    age_to_form_field = IntegerField('Возраст До', validators=[validators.DataRequired()])
    submit = SubmitField('Сохранить')

class ParticipantForm(FlaskForm): 
   participant_name_form = StringField('Имя', validators=[validators.DataRequired()]) 
   participant_last_name_form = StringField('Фамилия', validators=[validators.DataRequired()]) 
   birthday_form = DateField('Дата рождения', format = '%Y-%m-%d',validators=[validators.DataRequired()]) 
   avatar_google_code = StringField('Код ссылки для аватарки') 
   participant_city = StringField('Город') 
   active_status = BooleanField('Активен')
   submit = SubmitField('Сохранить')

class ParticipantNewForm(FlaskForm): 
   participant_name_form = StringField('Имя', validators=[validators.DataRequired()]) 
   participant_last_name_form = StringField('Фамилия', validators=[validators.DataRequired()]) 