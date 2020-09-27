from app import db
from . import main
from flask import render_template, request, redirect, url_for, flash, make_response, current_app
from flask_login import login_required, login_user, current_user, logout_user
from app.models import Users, Sites
from .forms import SignIn, SignUp, IntegrationsForm
from werkzeug.security import generate_password_hash, check_password_hash

from gaapi4py import GAClient
import psycopg2
from psycopg2._psycopg import OperationalError
import pandas as pd
import numpy  # библиотека для работы с массивами
import openpyxl
import matplotlib.pyplot as plt
from statsmodels.tsa.seasonal import seasonal_decompose
from io import BytesIO
import base64


@main.route("/index", methods=['POST', 'GET'])
@main.route("/", methods=['POST', 'GET'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('.account'))

    form = SignIn()
    if form.validate_on_submit():
        user = db.session.query(Users).filter(Users.email == form.email.data).first()
        if user and user.check_password(form.psw.data):
            login_user(user, remember=form.remember.data)
            return redirect(request.args.get('.next') or url_for('.account'))

        flash('Неверная пара логин/пароль', 'error')

    return render_template('index.html', title='Авторизация', form=form)


@main.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', title='Page not found / Web Site Tools Analytics Platform'), 404


@main.route("/account")
@login_required
def account():
    # Запрашиваю данные из Google Analytics API для запрашиваемого сайта
    # Делал по инструкции http://toolmark.ru/python-ga-api/
    # http: // toolmark.ru / python - postgre /
    # view_id найти здесь: http://joxi.ru/a2X9zxDCDRLZdA

    # if GOOGLE_APPLICATION_CREDENTIALS is set:
    # c = GAClient()
    # or you may specify keyfile path:

    # Тут еще можно сделать проверку на получаемость данных из Гугла. Если данные получили - ок, а если не получили, то попробовать еще раз

    c = GAClient(json_keyfile="ga/gazolin-production-fc7ce2997b39.json")

    view_id = '52954517'

    # тело запроса отправляемого в GA
    request_body = {
        'view_id': view_id,
        'start_date': '2020-09-17',  # ставим переменную со вчерашней датой
        'end_date': '2020-09-25',  # ставим переменную со вчерашней датой
        'dimensions': {
            'ga:sourceMedium',
            'ga:year',
            'ga:month',
            'ga:day',
            'ga:hour',
            'ga:dimension1',  # в этой переменной у меня записан client id
            'ga:dimension2',  # в этой переменной у меня записан session id
            # 'ga:latitude',
            # 'ga:longitude'
        },
        'metrics': {
            'ga:sessions',
            'ga:sessionDuration',
            'ga:hits'
        },
        # 'filter': 'ga:sourceMedium==google / organic' # optional filter clause
    }

    response = c.get_all_data(request_body)

    # Записываем ответ GA в dataframe
    df = response['data']

    # Создам новый признак - дата сессии (соберу на основании разрозненных данных)
    df['date'] = df[['year', 'month', 'day']].agg('-'.join, axis=1)
    df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d', errors='ignore')

    # Преобразуем порядок столбцов, потому что из GA каждый раз получаем столбцы в разном порядке,
    # а нам нужны данные одного порядка для передачи в базу
    df = df[['date',
             'year',
             'month',
             'day',
             'hour',
             'sourceMedium',
             'sessions',
             'hits',
             'sessionDuration',
             'dimension1',
             'dimension2']]

    # Переименую колонки
    df.rename(columns={'sourceMedium': 'source_medium',
                       'sessionDuration': 'session_duration',
                       'dimension1': 'client_id',
                       'dimension2': 'session_id'
                       },
              inplace=True)

    # Возьму только нужные мне колонки
    df_short = df[['date', 'source_medium', 'sessions', 'session_duration', 'hits', 'client_id', 'session_id']]. \
        sort_values(by='date', ascending=False)

    # Преобразую некоторые данные в числовые для последующего суммирования
    df_short[['hits', 'sessions']] = df_short[['hits', 'sessions']].astype(int)
    df_short['session_duration'] = df_short['session_duration'].astype(float)


    # Экспортирую датафрейм
    # df_short.to_excel(f'output/df_{int(view_id)}.xlsx',
    #             sheet_name=f'{int(view_id)}',
    #             index=False)

    # Распределение активных пользователей по дням (сессии). Выведу график.
    img = BytesIO()
    data_graph = df_short.groupby('date').agg({'sessions': 'sum'}).sort_values(by=['date'], ascending=True).reset_index()
    # приводим индексы к стандарту pd.Datetime, чтобы потом это можно было скормить seasonal_decompose
    data_graph = data_graph.set_index(pd.DatetimeIndex(data_graph['date']))
    # замечаем, что т.к. у нас теперь есть индекс Month, нам больше не нужен столбец Month, который его дублирует
    data_graph.drop(['date'], axis=1, inplace=True)
    print(data_graph)
    # применяем seasonal_decompose
    # эта функция разложит ряд на трендовую, сезонную и шумовую составляющие
    decomposition = seasonal_decompose(data_graph, model='additive')
    decomposition.plot()
    plt.show()  # любуемся результатом
    plt.savefig(img, format='png')
    plt.close()
    img.seek(0)
    plot_url = base64.b64encode(img.getvalue()).decode('utf8')

    # как можно вывести данные на графики: https://www.patricksoftwareblog.com/creating-charts-with-chart-js-in-a-flask-application/
    # как еще можно передать данные из датафрейма в джинжу http://sarahleejane.github.io/learning/python/2015/08/09/simple-tables-in-webapps-using-flask-and-pandas-with-python.html
    return render_template('account.html', title='Account / Web Site Tools Analytics Platform', data=list(df_short.values), data_columns=df_short.columns, plot_url=plot_url)


@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта', 'success')
    return redirect(url_for('.index'))


@main.route("/signup", methods=("POST", "GET"))
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('.account'))

    form = SignUp()
    if form.validate_on_submit():
        email = form.email.data
        psw = form.psw.data

        try:
            hash = generate_password_hash(psw)
            user = Users(email=email, psw=hash)
            db.session.add(user)
            db.session.flush()  # из сессии перемещает записи в таблицу, но еще не записывает в саму таблицу

            s = Sites(user_id=user.id)
            db.session.add(s)
            db.session.commit()  # идет физическая запись в БД

            flash('Поздравляем с регистрацией! Теперь Вы можете авторизироваться в системе.', 'success')

            return redirect(url_for('.index'))

        except:
            db.session.rollback()  # если при добавлении в БД были какие-то ошибки, тогда откатываем БД до состояния, как будто ничего не записывали

            flash('Что-то пошло не так. Попробуйте, пожалуйста, еще раз!', 'error')

            return redirect(url_for('.signup'))

    return render_template("signup.html", title="Регистрация", form=form)


@main.route("/integrations", methods=['POST', 'GET'])
@login_required
def integrations():
    user_id = current_user.id
    print(user_id)
    form = IntegrationsForm()
    if form.validate_on_submit():
        site = form.site.data
        ga_id = form.ga_id.data

        try:
            user = db.session.query(Users).filter(Users.id == user_id).first()

            site = Sites(user_id=user.id)
            db.session.add(site)
            db.session.commit()  # идет физическая запись в БД

            flash('Интеграция успешно добавлена!', 'success')

            return redirect(url_for('.integrations'))

        except:
            db.session.rollback()  # если при добавлении в БД были какие-то ошибки, тогда откатываем БД до состояния, как будто ничего не записывали

            flash('Что-то пошло не так. Попробуйте, пожалуйста, еще раз!', 'error')

            return redirect(url_for('.integrations'))

    return render_template("integrations.html", title="Регистрация", form=form)


@main.route('/cookie')
def cookie():
    if not request.cookies.get('foo'):
        res = make_response("Setting a cookie")
        res.set_cookie('foo', 'bar', max_age=60 * 60 * 24 * 365 * 2)
    else:
        res = make_response("Value of cookie foo is {}".format(request.cookies.get('foo')))
    return res


@main.route('/delete-cookie')
def delete_cookie():
    res = make_response("Cookie Removed")
    res.set_cookie('foo', 'bar', max_age=0)
    return res
