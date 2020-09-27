from flask_wtf import FlaskForm
from wtforms import StringField, \
    SubmitField, \
    BooleanField, \
    PasswordField
from wtforms.validators import DataRequired, \
    Email, \
    Length, \
    EqualTo


class SignIn(FlaskForm):
    email = StringField('E-mail: ',
                        validators=[DataRequired(), Email('Некорректный e-mail')],
                        render_kw={'autofocus': True, 'placeholder': 'E-mail'})
    psw = PasswordField('Пароль: ',
                             validators=[DataRequired(),
                                         Length(min=4,
                                                max=100,
                                                message='Пароль должен быть от 4 до 100 символов')],
                             render_kw={'placeholder': 'Пароль'})
    remember = BooleanField('Запомнить',
                            default=False)
    submit = SubmitField('Войти')


class SignUp(FlaskForm):
    email = StringField('E-mail: ',
                        validators=[DataRequired(), Email('Некорректный e-mail')],
                        render_kw={'autofocus': True, 'placeholder': 'E-mail'})
    psw = PasswordField('Пароль: ',
                             validators=[DataRequired(),
                                         Length(min=4,
                                                max=100,
                                                message='Пароль должен быть от 4 до 100 символов')],
                             render_kw={'placeholder': 'Пароль'})
    psw2 = PasswordField('Повтор пароля: ',
                              validators=[DataRequired(),
                                          EqualTo('psw',
                                                  message='Пароли не совпадают')],
                              render_kw={'placeholder': 'Повтор пароля'})
    submit = SubmitField('Зарегистрироваться')


class IntegrationsForm(FlaskForm):
    site = StringField('Сайт: ',
                       validators=[DataRequired(),
                                   Length(min=4,
                                          max=100,
                                          message='Сайт должен быть от 4 до 100 символов')],
                       render_kw={'autofocus': True, 'placeholder': 'Сайт'})
    ga_id = PasswordField('Google Analytics ID: ',
                          validators=[DataRequired(),
                                      Length(min=6,
                                             max=20,
                                             message='Google Analytics ID должен быть от 6 до 20 символов')],
                          render_kw={'placeholder': 'Google Analytics ID'})
    submit = SubmitField('Сохранить')
