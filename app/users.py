from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from models import db, Users, Roles
from sqlalchemy.exc import SQLAlchemyError
from books import admin_or_librarian

bp = Blueprint('users', __name__, url_prefix='/users')


# Страница Управление пользователями
@bp.route('/manage_users')
@login_required
@admin_or_librarian('admin')
def manage_users():
    users = db.session.query(
        Users.id_user,
        Users.login,
        Users.fio,
        Roles.role_name
    ).outerjoin(Roles, Users.id_role == Roles.id_role).all()
    return render_template("users/manage_users.html", users=users)


# Редактирование пользователя
@bp.route('/edit_users', methods=['GET', 'POST'])
@login_required
def edit_users():
    id_user = request.args.get('id_user', type=int)
    user = db.session.query(Users).filter(Users.id_user == id_user).one()
    if request.method == 'POST':
        login = request.form['login']
        first_name = request.form['name']
        last_name = request.form['lastName']
        middle_name = request.form['middleName']
        role_id = request.form.get('role_id')

        user.login = login
        user.fio = f"{last_name} {first_name} {middle_name}"
        if current_user.is_admin():
            user.id_role = role_id

        try:
            db.session.commit()
            flash('Данные пользователя успешно обновлены', 'success')
            return redirect(url_for('users.manage_users'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f'Произошла ошибка при обновлении данных: {str(e)}', 'danger')

    return render_template("users/edit_users.html", user=user)


# Удаление пользователя
@bp.route('/<int:id_user>/delete_user', methods=['POST'])
@login_required
def delete_user(id_user):
    try:
        user_to_delete = db.session.query(Users).filter_by(id_user=id_user).first()
        db.session.delete(user_to_delete)
        db.session.commit()
        flash('Выбранный пользователь успешно удалена', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'Произошла ошибка при удалении учетной записи: {str(e)}', 'danger')
        return render_template('users/manage_users.html')

    return redirect(url_for('users.manage_users'))
