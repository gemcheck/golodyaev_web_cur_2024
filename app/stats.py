from flask import Blueprint, send_file, render_template
from flask_login import login_required
from models import db, Books, Rent
from sqlalchemy import desc
from books import admin_or_librarian
from sqlalchemy import func
from io import BytesIO

bp = Blueprint('stats', __name__, url_prefix='/stats')


# Статистика аренды книг
@bp.route('/rent_stats')
@login_required
@admin_or_librarian('admin')
def rent_stats():
    rent_statistics = db.session.query(
        Books.author,
        Books.book_name,
        func.count(Rent.id_book).label('rent_count'),
        Books.id_book
    ).join(Rent, Books.id_book == Rent.id_book
           ).group_by(Books.author, Books.book_name, Books.id_book
                      ).all()
    return render_template("stats/rent_stats.html", rent_statistics=rent_statistics)


# Статистика популярности книг
@bp.route('/popular_stats')
@login_required
@admin_or_librarian('admin')
def popular_stats():
    rent_statistics = db.session.query(
        Books.book_name,
        Books.author,
        func.count(Rent.id_book).label('rent_count')
    ).join(Rent, Books.id_book == Rent.id_book
           ).group_by(Books.book_name, Books.author
                      ).order_by(desc('rent_count')).all()

    # Определение места по результатам аренды, если есть книги,
    # число аренд которых одинако, то у них одно и то же место
    ranked_books = []
    current_rank = 0
    current_count = None
    for book in rent_statistics:
        if book.rent_count != current_count:
            current_rank += 1
            current_count = book.rent_count
        ranked_books.append({
            'rank': current_rank,
            'book_name': book.book_name,
            'author': book.author,
            'rent_count': book.rent_count
        })
    return render_template("stats/popular_stats.html", ranked_books=ranked_books)


# Скачиваение статистики по аренде
@bp.route('/rent_stats_export.csv')
@login_required
@admin_or_librarian('admin')
def rent_stats_export():
    rent_stats = db.session.query(
        Books.author,
        Books.book_name,
        func.count(Rent.id_book).label('rent_count'),
        Books.id_book
    ).join(Rent, Books.id_book == Rent.id_book
           ).group_by(Books.author, Books.book_name, Books.id_book
                      ).all()

    result = ''
    fields = ['book_name', 'author', 'rent_count']
    result += ';'.join(fields) + '\n'
    for record in rent_stats:
        result += ';'.join([str(getattr(record, field)) for field in fields]) + '\n'

    return send_file(BytesIO(result.encode('windows-1251')), as_attachment=True, mimetype='text/csv; charset=windows-1251',
                     download_name='rent_stats_export.csv')
