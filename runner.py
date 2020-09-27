'''
При разработке использовал материалы с сайта
https://www.youtube.com/watch?v=6jxveKOdyNg&list=PLA0M1Bcd0w8yrxtwgqBvT6OM4HkOU3xYn&ab_channel=selfedu
https://pythonru.com/uroki/19-struktura-i-jeskiz-prilozhenija-flask
https://pythonru.com/uroki/14-sozdanie-baz-dannyh-vo-flask

python runner.py runserver - запуск проекта в терминале
from app import db - в пайтон-консоли подготовка к инсталляции таблиц БД
db.create_all() - создание таблиц БД
python runner.py db init - инициация репозитория для миграции
python runner.py db migrate -m  "Adding employees table" - инициирую миграцию
python runner.py db upgrade - применяем текущую миграцию (https://pythonru.com/uroki/16-migracii-bazy-dannyh-s-pomoshhju-alembic)


'''

import os
from app import db,  create_app
from app.models import Users, Sites
from flask_script import Manager, Shell
from flask_migrate import MigrateCommand

app = create_app(os.getenv('FLASK_ENV') or 'config.DevelopementConfig')
manager = Manager(app)


# эти переменные доступны внутри оболочки без явного импорта
def make_shell_context():
    return dict(app=app, db=db, User=Users, Sites=Sites)


manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)

if __name__ == '__main__':
    manager.run()
