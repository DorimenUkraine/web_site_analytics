from app import app
from flask import render_template, request, redirect, url_for, flash, make_response
from flask_login import login_required, login_user, current_user, logout_user
from .models import Users, Sites, db
from .forms import SignIn, SignUp, IntegrationsForm
from werkzeug.security import generate_password_hash, check_password_hash


@app.route("/index", methods=['POST', 'GET'])
@app.route("/", methods=['POST', 'GET'])
def index():
    if current_user.is_authenticated:
        return redirect(url_for('account'))

    form = SignIn()
    if form.validate_on_submit():
        user = db.session.query(Users).filter(Users.email == form.email.data).first()
        if user and user.check_password(form.psw.data):
            login_user(user, remember=form.remember.data)
            return redirect(request.args.get('next') or url_for('account'))

        flash('Неверная пара логин/пароль', 'error')

    return render_template('index.html', title='Авторизация', form=form)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html', title='Page not found / Web Site Tools Analytics Platform'), 404


@app.route("/account")
@login_required
def account():
    return render_template('account.html', title='Account / Web Site Tools Analytics Platform')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из аккаунта', 'success')
    return redirect(url_for('index'))


@app.route("/signup", methods=("POST", "GET"))
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('account'))

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

            return redirect(url_for('index'))

        except:
            db.session.rollback()  # если при добавлении в БД были какие-то ошибки, тогда откатываем БД до состояния, как будто ничего не записывали

            flash('Что-то пошло не так. Попробуйте, пожалуйста, еще раз!', 'error')

            return redirect(url_for('signup'))

    return render_template("signup.html", title="Регистрация", form=form)


@app.route("/integrations", methods=['POST', 'GET'])
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

            return redirect(url_for('integrations'))

        except:
            db.session.rollback()  # если при добавлении в БД были какие-то ошибки, тогда откатываем БД до состояния, как будто ничего не записывали

            flash('Что-то пошло не так. Попробуйте, пожалуйста, еще раз!', 'error')

            return redirect(url_for('integrations'))

    return render_template("integrations.html", title="Регистрация", form=form)


@app.route('/cookie')
def cookie():
    if not request.cookies.get('foo'):
        res = make_response("Setting a cookie")
        res.set_cookie('foo', 'bar', max_age=60 * 60 * 24 * 365 * 2)
    else:
        res = make_response("Value of cookie foo is {}".format(request.cookies.get('foo')))
    return res


@app.route('/delete-cookie')
def delete_cookie():
    res = make_response("Cookie Removed")
    res.set_cookie('foo', 'bar', max_age=0)
    return res
