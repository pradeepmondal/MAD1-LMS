from flask_restful import Resource, Api
from flask_restful import fields, marshal_with
from flask_restful import reqparse
from .database import db
from .models import Section, Book, Book_Issue, Book_Request, Book_Purchase, Book_Issue_History
from .validation import BusinessValidationError, SectionNotFoundError, IssueNotFoundError, BookNotFoundError, OtherError

####### API's for CRUD on sections

section_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "date_created": fields.DateTime,
    "description": fields.String,
    "search_name": fields.String
}

book_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "search_name": fields.String,
    "content": fields.String,
    "authors": fields.String,
    "search_authors": fields.String,
    "no_of_pages": fields.Integer,
    "vol": fields.Integer,
    "section_id": fields.Integer
}

issue_fields = {
    "id": fields.Integer,
    "book_id": fields.Integer,
    "username": fields.String,
    "issue_date": fields.String,
    "return_date": fields.String
}



#Create Section Parser
create_section_parser = reqparse.RequestParser()
create_section_parser.add_argument("name")
create_section_parser.add_argument("description")

# Update Section Parser
update_section_parser = reqparse.RequestParser()
update_section_parser.add_argument('name')
update_section_parser.add_argument('description')


# Update Book Parser
update_book_parser = reqparse.RequestParser()
update_book_parser.add_argument('name')
update_book_parser.add_argument('authors')
update_book_parser.add_argument('no_of_pages')
update_book_parser.add_argument('vol')
update_book_parser.add_argument('section_id')




#Create Book Parser
create_book_parser = reqparse.RequestParser()
create_book_parser.add_argument('name')
create_book_parser.add_argument('authors')
create_book_parser.add_argument('no_of_pages')
create_book_parser.add_argument('vol')
create_book_parser.add_argument('section_id')






class SectionApi(Resource):
    @marshal_with(section_fields)
    def get(self, section_id):
        section = db.session.query(Section).filter(Section.id == section_id).first()
        if section is None:
            raise SectionNotFoundError(status_code=404)
        return section, 200

    @marshal_with(section_fields)
    def put(self, section_id):
        args = update_section_parser.parse_args()
        name = args.get("name", None)
        description = args.get("last_name", None)

        section = db.session.query(Section).filter(Section.id == section_id).first()
        if section is None:
            raise SectionNotFoundError(status_code=404)


        if name is None:
            raise BusinessValidationError(status_code=400, error_code="SECTION002",
                                          error_message="Section name is required")
        if description is None:
            raise BusinessValidationError(status_code=400, error_code="SECTION001",
                                          error_message="Section description is required")

        section = db.session.query(Section).filter(Section.id == section_id).first()
        if section:
            raise OtherError(status_code=409, description="Section already exist")

        search_name = name.lower().replace('.', '').replace(' ', '_')
        section.name = name
        section.description = description
        section.search_name =search_name
        db.session.add(section)
        db.session.commit()
        return section

    def delete(self, section_id):

        section = db.session.query(Section).filter(Section.id == section_id).first()
        if section is None:
            raise SectionNotFoundError(status_code=404)

        sec_books = db.session.query(Book).filter(Book.section_id == section_id).all()
        for book in sec_books:
            book_req = db.session.query(Book_Request).filter(Book_Request.book_id == book.book_id).all()
            for req in book_req:
                db.session.delete(req)
            book_issue = db.session.query(Book_Issue).filter(Book_Issue.book_id == book.book_id).all()
            for issue in book_issue:
                db.session.delete(issue)
            book_issue_history = db.session.query(Book_Issue_History).filter(
                Book_Issue_History.book_id == book.book_id).all()
            for issue_history in book_issue_history:
                db.session.delete(issue_history)
            book_purchase = db.session.query(Book_Purchase).filter(Book_Purchase.book_id == book.book_id).all()
            for purchase in book_purchase:
                db.session.delete(purchase)

        db.session.delete(section)
        db.session.commit()
        return 'Successfully Deleted', 200

    @marshal_with(section_fields)
    def post(self):
        args = create_section_parser.parse_args()
        name = args.get("name", None)
        description = args.get("description", None)

        if name is None:
            raise BusinessValidationError(status_code=400, error_code="SECTION002",
                                          error_message="Section name is required")
        if description is None:
            raise BusinessValidationError(status_code=400, error_code="SECTION001",
                                          error_message="Section description is required")


        search_name = name.lower().replace('.', '').replace(' ', '_')
        new_section = Section(name=name, description=description,
                              search_name = search_name)
        db.session.add(new_section)
        db.session.commit()

        return new_section, 201




class BookApi(Resource):
    @marshal_with(book_fields)
    def get(self, book_id):
        book = db.session.query(Book).filter(Book.id == book_id).first()
        if book is None:
            raise BookNotFoundError(status_code=404)
        return book, 200


    @marshal_with(book_fields)
    def put(self, book_id):
        args = update_book_parser.parse_args()
        name = args.get("name", None)
        authors = args.get("authors", None)
        no_of_pages = args.get("no_of_pages", None)
        vol = args.get("vol", None)
        section_id = args.get("section_id", None)

        book = db.session.query(Book).filter(Book.id == book_id).first()
        if book is None:
            raise BookNotFoundError(status_code=404)

        if name is None:
            raise BusinessValidationError(status_code=400, error_code="BOOK001",
                                          error_message="Book name is required")
        if authors is None:
            raise BusinessValidationError(status_code=400, error_code="BOOK002",
                                          error_message="Book author is required")
        if no_of_pages is None:
            raise BusinessValidationError(status_code=400, error_code="BOOK003",
                                          error_message="No of pages is required")
        if vol is None:
            raise BusinessValidationError(status_code=400, error_code="BOOK004",
                                          error_message="Volume detail is required")
        if section_id is None:
            raise BusinessValidationError(status_code=400, error_code="BOOK005",
                                          error_message="section_id is required")


        book = db.session.query(Book).filter(Book.id == book_id).first()
        if book:
            raise OtherError(status_code=409, description="Book already exist")

        search_name = name.lower().replace(',', ' ').replace('.', '').replace(' ', '_')
        book.name = name
        book.search_name = search_name
        book.content = search_name+'.pdf'
        book.authors = authors
        book.search_authors = authors.lower().replace(',', ' ').replace('.', '')
        book.no_of_pages = no_of_pages
        book.vol = vol
        book.section_id = section_id
        db.session.add(book)
        db.session.commit()
        return book


    def delete(self, book_id):

        book = db.session.query(Book).filter(Book.id == book_id).first()
        if book is None:
            raise BookNotFoundError(status_code=404)

        book_req = db.session.query(Book_Request).filter(Book_Request.book_id == book.id).all()
        for req in book_req:
            db.session.delete(req)
        book_issue = db.session.query(Book_Issue).filter(Book_Issue.book_id == book.id).all()
        for issue in book_issue:
            db.session.delete(issue)
        book_issue_history = db.session.query(Book_Issue_History).filter(
            Book_Issue_History.book_id == book.id).all()
        for issue_history in book_issue_history:
            db.session.delete(issue_history)
        book_purchase = db.session.query(Book_Purchase).filter(Book_Purchase.book_id == book.id).all()
        for purchase in book_purchase:
            db.session.delete(purchase)

        db.session.delete(book)
        db.session.commit()
        return 'Successfully Deleted', 200



    @marshal_with(book_fields)
    def post(self, book_id):
        args = create_book_parser.parse_args()
        name = args.get("name", None)
        authors = args.get("authors", None)
        no_of_pages = args.get("no_of_pages", None)
        vol = args.get("vol", None)
        section_id = args.get("section_id", None)

        if name is None:
            raise BusinessValidationError(status_code=400, error_code="BOOK001",
                                          error_message="Book name is required")
        if authors is None:
            raise BusinessValidationError(status_code=400, error_code="BOOK002",
                                          error_message="Book author is required")
        if no_of_pages is None:
            raise BusinessValidationError(status_code=400, error_code="BOOK003",
                                          error_message="No of pages is required")
        if vol is None:
            raise BusinessValidationError(status_code=400, error_code="BOOK004",
                                          error_message="Volume detail is required")
        if section_id is None:
            raise BusinessValidationError(status_code=400, error_code="BOOK005",
                                          error_message="section_id is required")

        book = db.session.query(Book).filter(Book.id == book_id).first()
        if book:
            raise OtherError(status_code=409, description="Book already exist")


        search_name = name.lower().replace(',', ' ').replace('.', '').replace(' ', '_')
        search_authors = authors.lower().replace(',', ' ').replace('.', '')


        new_book = Section(name=name, search_name = search_name, content = search_name+'.pdf', authors =authors, search_authors = search_authors, no_of_pages =no_of_pages, vol = vol, section_id = section_id)
        db.session.add(new_book)
        db.session.commit()

        return new_book, 201

class IssueApi(Resource):

    @marshal_with(issue_fields)
    def get(self, book_id, username):
        issue = db.session.query(Book_Issue).filter((Book_Issue.id == book_id) & (Book_Issue.username == username)).first()
        if issue is None:
            raise IssueNotFoundError(status_code=404)
        return issue, 200

    def delete(self, book_id, username):
        book_issue = db.session.query(Book_Issue).filter(
            (Book_Issue.book_id == book_id) & (Book_Issue.username == username)).first()
        if book_issue is None:
            raise IssueNotFoundError(status_code=404)
        else:
            new_issue_history = Book_Issue_History(book_id=book_id, username=username, issue_date=book_issue.issue_date)
            db.session.add(new_issue_history)
            db.session.delete(book_issue)
            db.session.commit()
            return 'Successfully Deleted', 200

    @marshal_with(issue_fields)
    def post(self, book_id, username):
        book_issue = db.session.query(Book_Issue).filter(
            (Book_Issue.book_id == book_id) & (Book_Issue.username == username)).first()
        if book_issue:
            raise OtherError(status_code=409, description="Book is already issued")
        else:
            new_issue = Book_Issue(book_id = book_id, username = username)
            db.session.add(new_issue)
            db.session.commit()

            return new_issue, 201












