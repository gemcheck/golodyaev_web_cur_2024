from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from functools import wraps
from flask_migrate import Migrate
from models import db, Books, Category, Series, Publishing, Rent, Users
from sqlalchemy.exc import SQLAlchemyError
from datetime import date, timedelta
from auth import bp as auth_bp, init_login_manager
from books import bp as books_bp
from users import bp as users_bp
from stats import bp as stats_bp
from sqlalchemy import desc
from datetime import datetime
from books import admin_or_librarian

app = Flask(__name__)
application = app
app.config.from_pyfile('config.py')

db.init_app(app)
migrate = Migrate(app, db)

init_login_manager(app)

app.register_blueprint(auth_bp)
app.register_blueprint(books_bp)
app.register_blueprint(users_bp)
app.register_blueprint(stats_bp)


@app.errorhandler(SQLAlchemyError)
def database_error(error):
    return f'Произошла ошибка при подключении к базе данных: {error}', 500


# Функция для удаления записи из таблицы rent при истечении срока аренды,
# будет вызываться каждый раз, когда пользователь будет заходить на страницу "Читать книгу" (read_book.html)
def check_rent_expiration(id_user, id_book):
    try:
        current_date = datetime.now().date()
        rent = db.session.query(Rent).filter_by(id_user=id_user, id_book=id_book).first()
        if rent and rent.end_date <= current_date:
            db.session.delete(rent)
            db.session.commit()
            return True
        return False
    except SQLAlchemyError as e:
        db.session.rollback()
        flash('Произошла ошибка при удалении просроченной аренды.', 'danger')
        return False


# Главная страница с пагинацией
@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    book_name = request.args.get('book_name', '')
    query = db.select(Books)
    if book_name:
        query = query.filter(Books.book_name.ilike(f'%{book_name}%'))
    pagination = db.paginate(query, per_page=9, page=page)
    books = pagination.items
    return render_template("index.html", books=books, pagination=pagination, book_name=book_name)


# Личный кабинет
@app.route('/personal_account')
@login_required
def personal_account():
    user_record = db.session.query(Users).filter_by(id_user=current_user.id_user).one()
    rented_books = db.session.query(Books.id_book, Books.book_name, Books.author) \
        .join(Rent, Rent.id_book == Books.id_book) \
        .filter(Rent.id_user == current_user.id_user) \
        .all()
    return render_template("personal_account.html", user_record=user_record, rented_books=rented_books)


# Удаление арендованной книги из личного кабинета
@app.route('/<int:id_book>/delete', methods=['POST'])
@login_required
def delete(id_book):
    try:
        rent_to_delete = db.session.query(Rent).filter_by(id_book=id_book).first()
        db.session.delete(rent_to_delete)
        db.session.commit()
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'Произошла ошибка при удалении записи: {str(e)}', 'danger')
        return render_template('personal_account.html')

    flash('Арендованная книга успешно удалена', 'success')
    return redirect(url_for('personal_account'))


# Аренда книг
@app.route('/rent', methods=['GET', 'POST'])
@login_required
def rent():
    id_book = request.args.get('id_book', type=int)

    if request.method == 'POST':
        rent_term = request.form.get('rent_term')

        if rent_term == '3_days':
            end_date = date.today() + timedelta(days=3)
        elif rent_term == '5_days':
            end_date = date.today() + timedelta(days=5)
        elif rent_term == 'week':
            end_date = date.today() + timedelta(weeks=1)
        elif rent_term == '2_week':
            end_date = date.today() + timedelta(weeks=2)
        elif rent_term == 'month':
            end_date = date.today() + timedelta(days=30)

        try:
            # Проверка на то, что книга уже арендована,
            existing_rent = db.session.query(Rent).filter_by(
                id_book=id_book,
                id_user=current_user.id_user
            ).first()

            if existing_rent:
                flash('Аренда на эту книгу уже оформлена.', 'danger')
                return redirect(url_for('rent', id_book=id_book))

            new_rent = Rent(
                start_date=date.today(),
                end_date=end_date,
                id_book=id_book,
                id_user=current_user.id_user
            )
            db.session.add(new_rent)
            db.session.commit()

            flash('Аренда успешно оформлена', 'success')
            return redirect(url_for('read_book', id_book=id_book))

        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Произошла ошибка при оформлении аренды. Попробуйте снова.', 'danger')
            return redirect(url_for('rent', id_book=id_book))

    id_book = request.args.get('id_book', type=int)
    book = db.session.query(
        Books.id_book,
        Books.book_name,
        Books.author,
        Books.id_series,
        Books.id_publishing,
        Category.category_name,
        Series.series_name,
        Publishing.name_publishing
    ).outerjoin(Category, Books.id_category == Category.id_category
                ).outerjoin(Series, Books.id_series == Series.id_series
                            ).outerjoin(Publishing, Books.id_publishing == Publishing.id_publishing
                                        ).filter(Books.id_book == id_book).one()
    return render_template("rent.html", book=book)


# Страница чтении книги, если у пользователя нет арендованных книг, она недоступна
@app.route('/read_book')
@login_required
def read_book():
    id_book = request.args.get('id_book', type=int)
    user_rents = db.session.query(Rent).filter_by(id_user=current_user.id_user).order_by(desc(Rent.id_rent)).all()

    if not user_rents:
        flash('У вас нет арендованных книг.', 'danger')
        return redirect(url_for('index'))

        # Этот запрос нужен, чтобы получить id_book, если пользователь переходит
    # на страницу чтения книги сразу, а не через аренду. И если пользователь
    # сразу переходит на страницу чтения, то открывается последняя арендованная книга,
    # чтобы изменить книгу, надо в личном кабинете нажать на кнопку Открыть у нужной книги
    if not id_book:
        last_rent = db.session.query(Rent).filter_by(id_user=current_user.id_user).order_by(desc(Rent.id_rent)).first()
        id_book = last_rent.id_book

    # Провека, что срок аренды не истек
    check_rent = check_rent_expiration(current_user.id_user, id_book)
    if check_rent:
        return redirect(url_for('index'))

    book_name = db.session.execute(
        db.select(Books.book_name).filter_by(id_book=id_book)
    ).scalar_one_or_none()

    return render_template("read_book.html", book_name=book_name)
