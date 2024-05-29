from typing import Optional
import sqlalchemy as sa
from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin, current_user
from flask import current_app
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, MetaData, Date

class Base(DeclarativeBase):
  metadata = MetaData(naming_convention={
        "ix": 'ix_%(column_0_label)s',
        "uq": "uq_%(table_name)s_%(column_0_name)s",
        "ck": "ck_%(table_name)s_%(constraint_name)s",
        "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
        "pk": "pk_%(table_name)s"
    })

db = SQLAlchemy(model_class=Base)

class Category(Base):
    __tablename__ = 'category'
    id_category: Mapped[int] = mapped_column(primary_key=True)
    category_name: Mapped[str] = mapped_column(String(128))

class Users(Base,  UserMixin):
   __tablename__ = 'users'
   id_user: Mapped[int] = mapped_column(primary_key=True)
   fio: Mapped[str] = mapped_column(String(128))
   login: Mapped[str] = mapped_column(String(32), unique=True)
   hash_pass: Mapped[str] = mapped_column(String(256))
   id_role: Mapped[int] = mapped_column(ForeignKey('roles.id_role'))

   @property
   def first_name(self):
      return self.fio.split()[1]

   @property
   def last_name(self):
      return self.fio.split()[0]

   @property
   def middle_name(self):
      return self.fio.split()[2] if len(self.fio.split()) > 2 else ""


   @property
   def full_name(self):
      return f'{self.last_name} {self.first_name} {self.middle_name or ""}'

   def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        return self.password_hash

   def is_admin(self):
        return self.id_role == current_app.config['ADMIN_ROLE_ID']
   
   def is_librarian(self):
        return self.id_role == current_app.config['LIBRARION_ROLE_ID']

   def check_password(self, password):
      return check_password_hash(self.hash_pass, password)
   
   def has_rented_books(self):
    return db.session.query(Rent).filter_by(id_user=current_user.id_user).count() > 0
   
   def get_id(self):
      return str(self.id_user) 

class Books(Base):
   __tablename__ = 'books'
   id_book: Mapped[int] = mapped_column(primary_key=True)
   book_name: Mapped[str] = mapped_column(String(128))
   author: Mapped[str] = mapped_column(String(128))
   id_category: Mapped[int] = mapped_column(ForeignKey('category.id_category'))
   id_series: Mapped[Optional[int]] = mapped_column(ForeignKey('series.id_series'))
   id_publishing: Mapped[int] = mapped_column(ForeignKey('publishing.id_publishing'))

class Rent(Base):
   __tablename__ = 'rent'
   id_rent: Mapped[int] = mapped_column(primary_key=True)
   start_date: Mapped[Date] = mapped_column(Date())
   end_date: Mapped[Date] = mapped_column(Date())
   id_book: Mapped[int] = mapped_column(ForeignKey('books.id_book'))
   id_user: Mapped[int] = mapped_column(ForeignKey('users.id_user'))

class Series(Base):
   __tablename__ = 'series'
   id_series: Mapped[int] = mapped_column(primary_key=True)
   series_name: Mapped[str] = mapped_column(String(128))

class Publishing(Base):
   __tablename__ = 'publishing'
   id_publishing: Mapped[int] = mapped_column(primary_key=True)
   name_publishing: Mapped[str] = mapped_column(String(128))

class Roles(Base):
   __tablename__ = 'roles'
   id_role: Mapped[int] = mapped_column(primary_key=True)
   role_name: Mapped[int] = mapped_column(String(128))