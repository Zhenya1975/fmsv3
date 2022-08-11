from flask_wtf import FlaskForm
from wtforms import Form, TextAreaField, validators, StringField, SubmitField, IntegerField, DateField, RadioField, DecimalField
from wtforms.validators import InputRequired
from sqlalchemy import desc, asc

class CompetitionForm(FlaskForm):
    competition_name_form = StringField('Наименование турнира', validators=[validators.DataRequired()])
    competition_date_start = DateField('Дата начала соревнования', format = '%Y-%m-%d',validators=[validators.DataRequired()])
    competition_date_finish = DateField('Дата завершения соревнования', format = '%Y-%m-%d',validators=[validators.DataRequired()])
    competition_city =  StringField('Город турнира', validators=[validators.DataRequired()])
    submit = SubmitField('Сохранить')

class RegistrationeditForm(FlaskForm):
    reg_weight = DecimalField('Вес, кг', validators=[validators.DataRequired()])

    submit = SubmitField('Сохранить')


class WeightCategoriesForm(FlaskForm):
    sort_index_form_field = IntegerField('Индекс сортировки', validators=[validators.DataRequired()])
    weight_category_name_form_field = StringField('Наименование категории', validators=[validators.DataRequired()])
    weight_from_form_field = IntegerField('Вес От', validators=[validators.DataRequired()])
    weight_to_form_field = IntegerField('Вес До', validators=[validators.DataRequired()])
    submit = SubmitField('Сохранить')