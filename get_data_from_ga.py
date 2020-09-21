from gaapi4py import GAClient
import psycopg2
from psycopg2._psycopg import OperationalError
import pandas as pd
import numpy  # библиотека для работы с массивами
import openpyxl

# Делал по инструкции http://toolmark.ru/python-ga-api/
# view_id найти здесь: http://joxi.ru/a2X9zxDCDRLZdA


# if GOOGLE_APPLICATION_CREDENTIALS is set:
# c = GAClient()
# or you may specify keyfile path:
c = GAClient(json_keyfile="ga/gazolin-production-fc7ce2997b39.json")

VIEW_ID = '52954517'

# тело запроса отправляемого в GA
request_body = {
    'view_id': VIEW_ID,
    'start_date': '2020-09-16',  # ставим переменную со вчерашней датой
    'end_date': '2020-09-17',  # ставим переменную со вчерашней датой
    'dimensions': {
        'ga:sourceMedium',
        'ga:year',
        'ga:month',
        'ga:day',
        'ga:hour',
        'ga:minute',
        'ga:dimension1', # в этой переменной у меня записан client id
        'ga:dimension2', # в этой переменной у меня записан session id
        'ga:latitude',
        'ga:longitude'
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

# Преобразуем порядок столбцов, потому что из GA каждый раз получаем столбцы в разном порядке,
# а нам нужны данные одного порядка для передачи в базу
# а нам нужны данные одного порядка для передачи в базу
df = df[['year', 'month', 'day', 'hour', 'minute', 'sourceMedium', 'sessions', 'hits', 'sessionDuration', 'latitude', 'longitude', 'fullReferrer']]

print(df)

df.to_excel(f'output/df_{int(VIEW_ID)}.xlsx',
            sheet_name=f'{int(VIEW_ID)}',
            index=False)

# Конвертируем pandas df в список кортежей
sessions1 = df.to_records(index=False)

# Преобразование данных из массива numpy в список
sessions = numpy.recarray.tolist(sessions1)


# Функция для подключения к БД
def create_connection(db_name, db_user, db_password):
    connection = None
    try:
        connection = psycopg2.connect(
            database=db_name,
            user=db_user,
            password=db_password,

        )
        print("Connection to PostgreSQL DB successful")
    except OperationalError as e:
        print(f"The error '{e}' occurred")
    return connection


# Создаем подключение в качестве аргументов функции create_connection указываем название БД, имя пользователя и пароль
connection = create_connection(
    "gp_ga_api", "postgres", "231284"
)

## Запись полученных строк в БД
sessions_records = ", ".join(["%s"] * len(sessions))

insert_query = (
    f"INSERT INTO ga (data_sessions, client_id, session_id, source_medium, session) VALUES {sessions_records}"
)
connection.autocommit = True
cursor = connection.cursor()
cursor.execute(insert_query, sessions)
