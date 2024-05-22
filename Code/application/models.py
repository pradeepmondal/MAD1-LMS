from .database import db
from datetime import datetime, timedelta

class Authentication(db.Model):
    __tablename__ = 'auth'
    username = db.Column(db.String, primary_key = True)
    password = db.Column(db.String, nullable = False)
    user_type = db.Column(db.String, nullable = False)

class Users(db.Model):
    __tablename__ = 'users'
    username = db.Column(db.String, db.ForeignKey('auth.username'), primary_key = True)
    f_name = db.Column(db.String, nullable = False)
    l_name = db.Column(db.String)
    email = db.Column(db.String, unique = True, nullable = False)
    search_name = db.Column(db.String, nullable = False)


class Librarians(db.Model):
    __tablename__ = 'librarians'
    username = db.Column(db.String, db.ForeignKey('auth.username'), primary_key = True)
    f_name = db.Column(db.String, nullable = False)
    l_name = db.Column(db.String)
    email = db.Column(db.String, unique = True, nullable = False)

class Section(db.Model):
    __tablename__ = 'section'
    id = db.Column(db.Integer, autoincrement=True, primary_key = True)
    name = db.Column(db.String, unique = True, nullable = False)
    search_name = db.Column(db.String, nullable=False)
    date_created = db.Column(db.DateTime, nullable = False, default = datetime.now())
    description = db.Column(db.String, nullable = False, default = 'This is a dummy description')


class Book(db.Model):
    __tablename__ = 'book'
    id = db.Column(db.Integer, autoincrement=True, primary_key = True)
    name = db.Column(db.String, nullable=False)
    search_name = db.Column(db.String, nullable = False)
    authors = db.Column(db.String, nullable=False)
    search_authors = db.Column(db.String, nullable=False)
    content = db.Column(db.String, nullable=False, default = 'file_name of the book.')
    no_of_pages = db.Column(db.Integer, nullable=False, default=0)
    vol = db.Column(db.Integer)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'))


class Book_Issue(db.Model):
    __tablename__ = 'book_issue'
    id = db.Column(db.Integer, autoincrement=True, primary_key = True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable = False)
    username = db.Column(db.String, db.ForeignKey('users.username'), nullable = False)
    issue_date = db.Column(db.DateTime, nullable = False, default = datetime.now())
    return_date = db.Column(db.DateTime, nullable = False, default = datetime.now() + timedelta(days=7))

class Book_Issue_History(db.Model):
    __tablename__ = 'book_issue_history'
    id = db.Column(db.Integer, autoincrement=True, primary_key = True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable = False)
    username = db.Column(db.String, db.ForeignKey('users.username'), nullable = False)
    issue_date = db.Column(db.DateTime, nullable = False)
    returned_date = db.Column(db.DateTime, nullable = False, default = datetime.now())


class Book_Request(db.Model):
    __tablename__ = 'book_request'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    username = db.Column(db.String, db.ForeignKey('users.username'), nullable=False)
    duration = db.Column(db.String, nullable = False, default = '0 weeks 7 days 0 hours')


class Book_Purchase(db.Model):
    __tablename__ = 'book_purchase'
    id = db.Column(db.Integer, autoincrement=True, primary_key = True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable = False)
    username = db.Column(db.String, db.ForeignKey('users.username'), nullable = False)
    purchase_date = db.Column(db.DateTime, nullable = False, default = datetime.now())


