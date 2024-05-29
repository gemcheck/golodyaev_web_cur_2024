from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import LoginManager, login_user, logout_user, login_required
from models import db, Users
from sqlalchemy.exc import SQLAlchemyError

user=Users()

bp = Blueprint('auth', __name__, url_prefix='/auth')

def init_login_manager(app):
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Для доступа к данной странице необходимо пройти процедуру аутентификации.'
    login_manager.login_message_category = 'warning'
    login_manager.user_loader(load_user)
    login_manager.init_app(app)

def load_user(user_id):
    user = db.session.execute(db.select(Users).filter_by(id_user=user_id)).scalar_one()
    return user

# Авторизация
@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        if login and password:
            user = db.session.execute(db.select(Users).filter_by(login=login)).scalar_one_or_none()
            if user and user.check_password(password):
                login_user(user)
                flash('Вы успешно аутентифицированы.', 'success')
                next = request.args.get('next')
                return redirect(next or url_for('index'))
            else:
                flash('Введены неверные логин и/или пароль', 'danger')
        else:
            flash('Заполните все поля', 'danger')
    return render_template('auth/login.html')

# Регистрация
@bp.route('/reg', methods=['GET', 'POST'])
def reg():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')
        name = request.form.get('name')
        last_name = request.form.get('lastName')
        middle_name = request.form.get('middleName')

        if password != confirm_password:
            flash('Пароли не совпадают.', 'danger')
            return render_template('auth/reg.html')

        try:
            existing_user = db.session.execute(db.select(Users).filter_by(login=login)).scalar_one_or_none()
            if existing_user:
                flash('Пользователь с таким логином уже существует.', 'danger')
                return render_template('auth/reg.html')

            new_user = Users(
                fio=f'{last_name} {name} {middle_name or ""}',
                login=login,
                hash_pass=user.set_password(password),
                id_role=3
            )
            db.session.add(new_user)
            db.session.commit()

            flash('Вы успешно зарегистрировались.', 'success')
            login_user(new_user)
            return redirect(url_for('index'))

        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Произошла ошибка при сохранении данных: {str(e)}', 'danger')
            return render_template('auth/reg.html')

    return render_template('auth/reg.html')

# Выход из аккаунта
@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

