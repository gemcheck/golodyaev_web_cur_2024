from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from functools import wraps
from models import db, Books, Category, Series, Publishing
from sqlalchemy.exc import SQLAlchemyError
import os
from flask import current_app
from werkzeug.utils import secure_filename

bp = Blueprint('books', __name__, url_prefix='/books')

# Декоратор для разграничения прав доступа, на вход подается 
# либо 'admin'(доступ только для админа) либо 'admin_librarian' (доступ для админа и библиотекаря)
def admin_or_librarian(role):
    def decorator(func):
        @wraps(func)
        def decorated(*args, **kwargs):
            if role == 'admin' and not current_user.is_admin():
                flash('Доступ к этой странице разрешен только администраторам.', 'danger')
            elif role == 'admin_librarian' and not (current_user.is_admin() or current_user.is_librarian()):
                flash('Доступ к этой странице разрешен только администраторам и библиотекарям.', 'danger')
            else:
                return func(*args, **kwargs)
            return redirect(url_for('index')) 
        return decorated
    return decorator

# Страница управления книгами с пагинацией
@bp.route('/manage_books')
@login_required
@admin_or_librarian('admin_librarian')
def manage_books():
    page = request.args.get('page', 1, type=int)
    query = db.session.query(
        Books.id_book,
        Books.book_name,
        Books.author,
        Category.category_name,
        Series.series_name,
        Publishing.name_publishing
    ).outerjoin(Category, Books.id_category == Category.id_category
    ).outerjoin(Series, Books.id_series == Series.id_series
    ).outerjoin(Publishing, Books.id_publishing == Publishing.id_publishing)

    pagination = query.paginate(per_page=10, page=page)
    books = pagination.items
    return render_template("books/manage_books.html", books=books,  pagination=pagination)

# Изменение книг
@bp.route('/edit_books', methods=['GET', 'POST'])
@login_required
@admin_or_librarian('admin_librarian')
def edit_books():
    id_book = request.args.get('id_book', type=int)
    if request.method == 'POST':
        author = request.form.get('author')
        book_name = request.form.get('nameBook')
        category_name = request.form.get('category')
        series_name = request.form.get('seria')
        publishing_name = request.form.get('publisher')

        try:
            book = db.session.query(Books).filter_by(id_book=id_book).one()
            category = db.session.query(Category).filter_by(category_name=category_name).first()
            if not category:
                category = Category(category_name=category_name)
                db.session.add(category)
            
            series = db.session.query(Series).filter_by(series_name=series_name).first()
            if not series:
                series = Series(series_name=series_name)
                db.session.add(series)
            
            publishing = db.session.query(Publishing).filter_by(name_publishing=publishing_name).first()
            if not publishing:
                publishing = Publishing(name_publishing=publishing_name)
                db.session.add(publishing)
            
            db.session.commit()

            book.author = author
            book.book_name = book_name
            book.id_category = category.id_category
            book.id_series = series.id_series if series else None
            book.id_publishing = publishing.id_publishing

            db.session.commit()

        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Произошла ошибка при редактировании. Попробуйте снова.', 'danger')
            return redirect(url_for('books.edit_books', id_book=id_book))

        flash('Книга успешно обновлена', 'success')
        return redirect(url_for('books.manage_books'))

    record_book = db.session.query(
        Books.id_book,
        Books.book_name,
        Books.author,
        Category.category_name,
        Series.series_name,
        Publishing.name_publishing
    ).outerjoin(Category, Books.id_category == Category.id_category
    ).outerjoin(Series, Books.id_series == Series.id_series
    ).outerjoin(Publishing, Books.id_publishing == Publishing.id_publishing
    ).filter(Books.id_book == id_book).one()

    return render_template("books/edit_books.html", record_book=record_book)

# Загрузка изображений, название изображения соответствует id_book
@bp.route('/upload_image', methods=['POST'])
@login_required
@admin_or_librarian('admin_librarian')
def upload_image():
    id_book = request.args.get('id_book', type=int)
    if 'image' not in request.files:
        flash('Нет файла для загрузки', 'danger')
        return redirect(url_for('books.edit_books', id_book=id_book))

    file = request.files['image']
    if file.filename == '':
        flash('Не выбрано изображение для загрузки', 'danger')
        return redirect(url_for('books.edit_books', id_book=id_book))

    # Когда добавляем новое изображение при редактировании, то старое изображение переименовываем
    if file:
        filename = secure_filename(f'{id_book}.jpg')
        old_filepath = os.path.join(current_app.static_folder, 'images', filename)
        new_filepath = os.path.join(current_app.static_folder, 'images', f'{id_book}_old.jpg')
        
        if os.path.exists(old_filepath):
            os.rename(old_filepath, new_filepath)
        
        file.save(os.path.join(current_app.static_folder, 'images', filename))
        flash('Изображение успешно загружено', 'success')
    
    return redirect(url_for('books.edit_books', id_book=id_book))

# Добавление новой книги
@bp.route('/new_book', methods=['GET', 'POST'])
@login_required
@admin_or_librarian('admin_librarian')
def new_book():
    if request.method == 'POST':
        author = request.form['author']
        book_name = request.form['nameBook']
        category_name = request.form['category']
        series_name = request.form.get('seria', '')
        publishing_name = request.form['publisher']
        image = request.files['image']

        try:
            category = db.session.query(Category).filter_by(category_name=category_name).first()
            if not category:
                category = Category(category_name=category_name)
                db.session.add(category)

            series = db.session.query(Series).filter_by(series_name=series_name).first()
            if not series and series_name:
                series = Series(series_name=series_name)
                db.session.add(series)

            publishing = db.session.query(Publishing).filter_by(name_publishing=publishing_name).first()
            if not publishing:
                publishing = Publishing(name_publishing=publishing_name)
                db.session.add(publishing)

            db.session.commit()

            new_book = Books(
                author=author,
                book_name=book_name,
                id_category=category.id_category,
                id_series=series.id_series if series else None,
                id_publishing=publishing.id_publishing
            )
            db.session.add(new_book)
            db.session.commit()

            if not image:
                flash('Добавьте изображение', 'warning')
            else:
                filename = secure_filename(f'{new_book.id_book}.jpg')
                image.save(os.path.join('static/images', filename))

        except SQLAlchemyError as e:
            db.session.rollback()
            flash('Произошла ошибка при добавлении. Попробуйте снова.', 'danger')
            return redirect(url_for('books.new_books'))

        flash('Книга успешно добавлена', 'success')
        return redirect(url_for('books.manage_books'))

    return render_template("books/new_book.html")

# Удаление книги на странице Управление книгами
@bp.route('/<int:id_book>/delete_book', methods = ['POST'])
@login_required
def delete_bokk(id_book):
    try:
        book_to_delete = db.session.query(Books).filter_by(id_book=id_book).first()
        db.session.delete(book_to_delete)
        db.session.commit()
        flash('Выбранная книга успешно удалена', 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f'Произошла ошибка при удалении книги: {str(e)}', 'danger')
        return render_template('books/manage_books.html')
    
    return redirect(url_for('books.manage_books'))
