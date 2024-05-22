import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask import current_app as app
from .database import db
from .models import Authentication, Users, Librarians, Section, Book, Book_Issue, Book_Request, Book_Purchase, Book_Issue_History
import os
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash

SECRET_KEY = os.getenv('SECRET_KEY')
app.secret_key = SECRET_KEY

##################################   Landing Page  Controllers     ################################################


@app.route('/', methods = ['GET']) # End point for the landing page
def landing_page():
    if request.method == 'GET':
        return render_template('common/landing_page.html')


###################################################################################################################

##################################   User  Controllers     ################################################

@app.route('/login', methods = ['GET', 'POST']) # End point for the user login
def user_login():
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type')=='user')):
            return redirect(url_for('user_dashboard'))
        elif(session.get('user_logged_in') and (session.get('user_type')=='lib')):
            return redirect(url_for('lib_dashboard'))
        return render_template('user/login.html')
    else:

        # Logic for password verification
        username = request.form.get('username')
        password = request.form.get('password')

        user_auth = db.session.query(Authentication).filter((Authentication.username == username) & (Authentication.user_type == 'user')).first()

        if not user_auth:
            return render_template('user/error.html', error = 'There is no user with the given username.')

        if(user_auth.password == password):
            session['user_logged_in'] = user_auth.username
            session['user_type'] = 'user'
            return redirect(url_for('user_dashboard'))
        else:
            return render_template('user/error.html', error = 'Incorrect credentials, try again!')







@app.route('/register', methods = ['GET', 'POST']) # End point for the user registration
def user_registration():
    if request.method == 'GET':
        return render_template('user/register.html')
    else:
        f_name = request.form.get('f_name')
        l_name = request.form.get('l_name')
        search_name = f_name.lower().replace('.', '')+' '+l_name.lower().replace('.', '')
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        c_password = request.form.get('c_password')

        #Getting user with the given username
        user_auth = db.session.query(Authentication).filter((Authentication.username == username) & (Authentication.user_type == 'user')).first()

        # Getting user with the given email
        user_auth_email = db.session.query(Users).filter(Users.email == email).first()

        #checking if password and confirm password matches or not
        if password != c_password:
            return render_template('user/error.html', error='Password and Confirm Password do not match, try again.')

        #checking if the given username already exists
        if user_auth:
            return render_template('user/error.html', error = 'username already exists, choose a different one.')

        # checking if the given email already exists
        if user_auth_email:
            return render_template('user/error.html', error = 'email already exists, choose a different one.')

        new_user_auth = Authentication(username = username, password = password, user_type = 'user')
        new_user = Users(username = username, f_name = f_name, l_name = l_name, email = email, search_name =search_name)

        db.session.add(new_user_auth)
        db.session.add(new_user)
        db.session.commit()
        return render_template('user/confirm.html', message = 'User successfully registered, Login now to begin your learning journey.')






@app.route('/home', methods = ['GET', 'POST'])
def user_dashboard():
    if request.method == 'GET':
        if(session.get('user_logged_in') and (session.get('user_type')=='user')):
            username = session.get('user_logged_in')
            issued = db.session.query(Book_Issue).filter((Book_Issue.username == username)).all()
            cur_date_time = datetime.datetime.now()
            for issue in issued:
                if issue.return_date < cur_date_time:
                    new_issue_history = Book_Issue_History(book_id = issue.book_id, username = issue.username, issue_date = issue.issue_date, returned_date = issue.return_date)
                    db.session.add(new_issue_history)
                    db.session.delete(issue)
                    db.commit()
            issued = db.session.query(Book_Issue).filter((Book_Issue.username == username)).all()
            issued_books = [db.session.query(Book).filter(Book.id == issue.book_id).first() for issue in issued]

            purchased = db.session.query(Book_Purchase).filter((Book_Purchase.username == username)).all()
            purchased_books = [db.session.query(Book).filter(Book.id == purchase.book_id).first() for purchase in purchased]
            return render_template('user/user_dashboard.html', username = username, issued_books = issued_books, purchased_books = purchased_books)
        else:
            return redirect(url_for('user_login'))


@app.route('/explore_books', methods = ['GET', 'POST'])
def user_explore_books():
    if request.method == 'GET':
        if session.get('user_logged_in'):
            username = session.get('user_logged_in')
            search_str = ""
            search_str = request.args.get('search_str')
            if not search_str:
                sections = db.session.query(Section).all()

                books_dict = {}
                for section in sections:
                    cur_date_time = datetime.datetime.now()
                    books_of_section = db.session.query(Book).filter(Book.section_id == section.id).all()
                    books_of_section_dict_list = [{ 'id' : book.id, 'name' : book.name, 'search_name': book.search_name, 'content': book.content, 'authors': book.authors, 'search_authors': book.search_authors, 'no_of_pages': book.no_of_pages, 'vol': book.vol, 'section_id': book.section_id, 'status': 'not requested'} for book in books_of_section]
                    for book in books_of_section_dict_list:
                        book['status'] = 'not requested'

                        issued = db.session.query(Book_Issue).filter(
                            (Book_Issue.book_id == book['id']) & (Book_Issue.username == username)).first()



                        ### Checking for issue validity
                        if issued:
                            if issued.return_date < cur_date_time:
                                new_issue_history = Book_Issue_History(book_id=issued.book_id, username=issued.username,
                                                                       issue_date=issued.issue_date,
                                                                       returned_date=issued.return_date)
                                db.session.add(new_issue_history)
                                db.session.delete(issued)
                                db.commit()
                        issued = db.session.query(Book_Issue).filter(
                            (Book_Issue.book_id == book['id']) & (Book_Issue.username == username)).first()

                        purchased = db.session.query(Book_Purchase).filter(
                            (Book_Purchase.book_id == book['id']) & (Book_Purchase.username == username)).first()

                        if purchased:
                            book['status'] = 'purchased'
                        elif issued:
                            book['status'] = 'issued'
                        else:
                            requested = db.session.query(Book_Request).filter(
                                (Book_Request.book_id == book['id']) & (Book_Request.username == username)).first()
                            if requested:
                                book['status'] = 'requested'
                            else:
                                pass
                    books_dict[(section.id, section.name)] = books_of_section_dict_list

                return render_template('user/user_explore_books.html', username = username, books_dict = books_dict)
            else:
                t_search_str = search_str
                search_str = '%'+search_str+'%'

                result_books = []
                books_by_name = db.session.query(Book).filter(Book.search_name.like(search_str)).all()
                books_by_authors = db.session.query(Book).filter(Book.search_authors.like(search_str)).all()
                section_by_section_name = db.session.query(Section).filter(Section.search_name.like(search_str)).all()

                for book in books_by_name:
                    if book not in result_books:
                        result_books.append(book)

                for book in books_by_authors:
                    if book not in result_books:
                        result_books.append(book)

                for section in section_by_section_name:
                    books_of_section = db.session.query(Book).filter(Book.section_id == section.id).all()
                    for book in books_of_section:
                        if book not in result_books:
                            result_books.append(book)

                return render_template('user/user_search_book.html', username = username, result_books = result_books, search_str = t_search_str)

        else:
            return redirect(url_for('user_login'))



def create_user_bar_graph(my_issue_history, issue_dates, username):

    my_book_history = [db.session.query(Book).filter(Book.id == issue.book_id).first() for issue in my_issue_history]
    sections = [db.session.query(Section).filter(Section.id == book.section_id).first().name for book in my_book_history]
    section_dict = {}
    for section in sections:
        if(section not in section_dict.keys()):
            section_dict[section] = 1
        else:
            section_dict[section] += 1

    values = []
    labaels = []

    for section in section_dict.keys():
        values.append(section_dict[section])
        labaels.append(section)

    issue_months = []
    months = {
        1:'Jan',
        2:'Feb',
        3:'Mar',
        4:'Apr',
        5:'May',
        6:'Jun',
        7:'Jul',
        8:'Aug',
        9:'Sep',
        10:'Oct',
        11:'Nov',
        12:'Dec'
    }

    for d in issue_dates:
        issue_months.append(months[d.month])
    plt.clf()
    plt.hist(issue_months, color = 'brown')
    plt.xlabel('Months')
    plt.ylabel('No of Books Issued')
    plt.title('Books issued vs Month')
    plt.savefig(f'static/charts/users/{username}_hist.png')


    plt.clf()
    plt.pie(values, labels = labaels,)
    plt.xlabel('Section wise distribution of the issued books')
    plt.savefig(f'static/charts/users/{username}_pie.png')




@app.route('/my_stats', methods = ['GET', 'POST'])
def user_my_stats():
    if request.method == 'GET':
        if session.get('user_logged_in'):
            username = session.get('user_logged_in')
            user = db.session.query(Users).filter(Users.username == username).first()
            my_issue_history = db.session.query(Book_Issue_History).filter(Book_Issue_History.username == username).all()
            my_issue_dates = [issue.issue_date for issue in my_issue_history]
            create_user_bar_graph(my_issue_history, my_issue_dates, username)


            return render_template('user/my_stats.html', username = username, user = user)
        else:
            return redirect(url_for('user_login'))















@app.route('/books/<int:book_id>', methods = ['GET', 'POST'])
def user_book_details(book_id):
    if request.method == 'GET':
        cur_date_time = datetime.datetime.now()
        if (session.get('user_logged_in') and (session.get('user_type') == 'user')):
            username = session.get('user_logged_in')
            status = 'not requested'
            book = db.session.query(Book).filter(Book.id == book_id).first()
            issued = db.session.query(Book_Issue).filter((Book_Issue.book_id == book_id) & (Book_Issue.username == username)).first()

            ### Checking for issue validity
            if issued:
                if issued.return_date < cur_date_time:
                    new_issue_history = Book_Issue_History(book_id=issued.book_id, username=issued.username,
                                                           issue_date=issued.issue_date,
                                                           returned_date=issued.return_date)
                    db.session.add(new_issue_history)
                    db.session.delete(issued)
                    db.commit()

            issued = db.session.query(Book_Issue).filter(
                (Book_Issue.book_id == book_id) & (Book_Issue.username == username)).first()

            purchased = db.session.query(Book_Purchase).filter(
                (Book_Purchase.book_id == book_id) & (Book_Purchase.username == username)).first()


            if purchased:
                status = 'purchased'
            elif issued:
                status = 'issued'
            else:
                requested = db.session.query(Book_Request).filter((Book_Request.book_id == book_id) & (Book_Request.username == username)).first()
                if requested:
                    status = 'requested'
                else:
                    pass
            return render_template('user/user_book_details.html', username = username, book = book, status = status)
        else:
            return redirect(url_for('user_login'))


@app.route('/books/<int:book_id>/request', methods = ['GET', 'POST'])
def user_book_request(book_id):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'user')):
            username = session.get('user_logged_in')
            book = db.session.query(Book).filter(Book.id == book_id).first()
            return render_template('user/user_book_request.html', username = username, book = book)
        else:
            return redirect(url_for('user_login'))
    else:
        if (session.get('user_logged_in') and (session.get('user_type') == 'user')):
            username = session.get('user_logged_in')
            hours = request.form.get('hours')
            days = request.form.get('days')
            weeks = request.form.get('weeks')
            if not(hours):
                hours = '0'
            if not(days):
                days = '0'
            if not(weeks):
                weeks = '0'
            duration = weeks + ' weeks '+ days + ' days '+ hours + ' hours'
            existing_requests = db.session.query(Book_Request).filter(Book_Request.username == username).all()
            existing_requests_list = [request.id for request in existing_requests]
            existing_issue_books = db.session.query(Book_Issue).filter(Book_Issue.username == username).all()
            existing_issue_books_list = [issue.id for issue in existing_issue_books]

            if((len(existing_issue_books_list) + len(existing_requests_list)) < 5):
                new_request = Book_Request(book_id = book_id, username = username, duration = duration)
                db.session.add(new_request)
                db.session.commit()
                return render_template('user/confirm_message.html', message = 'Book successfully requested.', go_to_name = 'Go to Books', go_to_path = '/explore_books')
            else:
                return render_template('user/error.html', error = 'Request Denied! You have already issued or requested 5 books allowed as per the rules, cancel request or return first.')
        else:
            return redirect(url_for('user_login'))



@app.route('/books/<int:book_id>/cancel_request', methods = ['GET', 'POST'])
def user_book_cancel_request(book_id):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'user')):
            username = session.get('user_logged_in')
            book_request = db.session.query(Book_Request).filter((Book_Request.book_id == book_id ) & (Book_Request.username == username)).first()
            db.session.delete(book_request)
            db.session.commit()
            return render_template('user/confirm_message.html', message='Book requested successfully cancelled.',
                                   go_to_name='Go to Books', go_to_path='/explore_books')
        else:
            return redirect(url_for('user_login'))


@app.route('/books/<int:book_id>/purchase', methods = ['GET', 'POST'])
def user_book_purchase(book_id):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'user')):
            username = session.get('user_logged_in')

            book = db.session.query(Book).filter(Book.id == book_id).first()

            book_purchase = db.session.query(Book).filter(Book_Purchase.id == book_id).first()

            if book_purchase:
                return render_template('user/error.html', error="The book is already purchased.")



            if not book:
                return render_template('user/error.html', error = "There is no such books")
            else:
                new_purchase = Book_Purchase(book_id = book_id, username = username)
                issue = db.session.query(Book_Issue).filter(Book_Issue.book_id == book_id).first()
                if issue:
                    new_issue_history = Book_Issue_History(book_id=book_id, username=username,
                                                           issue_date=issue.issue_date)
                    db.session.add(new_issue_history)
                    db.session.delete(issue)
                db.session.add(new_purchase)
                db.session.commit()
                return render_template('user/confirm_message.html', message='Book purchase successful.',
                                   go_to_name='Go to Books', go_to_path='/explore_books')
        else:
            return redirect(url_for('user_login'))


@app.route('/books/<int:book_id>/download', methods = ['GET', 'POST'])
def user_book_download(book_id):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'user')):
            username = session.get('user_logged_in')
            allowed = db.session.query(Book_Purchase).filter((Book_Purchase.book_id == book_id)&(Book_Purchase.username == username)).first()
            if allowed:
                book = db.session.query(Book).filter(Book.id == book_id).first()
                pdf_path = 'static/books/content/' + book.search_name + '.pdf'
                return send_file(pdf_path, as_attachment=True)
            else:
                return render_template('user/error.html', error = 'You aren not permitted to download this book.')
        else:
            return redirect(url_for('user_login'))


@app.route('/books/<int:book_id>/view', methods = ['GET', 'POST'])
def user_book_read(book_id):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'user')):
            username = session.get('user_logged_in')
            allowed = db.session.query(Book_Issue).filter((Book_Issue.book_id == book_id) & (Book_Issue.username == username)).first()
            if allowed:
                book = db.session.query(Book).filter(Book.id == book_id).first()
                pdf_path = '/static/books/content/' + book.search_name + '.pdf'
                return render_template('user/user_pdf_reader.html', username=username, book=book, pdf_url=pdf_path)
            else:
                return render_template('user/error.html', error = 'This user is not permitted to view this book.')


        else:
            return redirect(url_for('user_login'))



@app.route('/books/<int:book_id>/return', methods = ['GET', 'POST'])
def user_book_return(book_id):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'user')):
            username = session.get('user_logged_in')
            issue = db.session.query(Book_Issue).filter((Book_Issue.book_id == book_id) & (Book_Issue.username == username)).first()
            if issue:
                new_issue_history = Book_Issue_History(book_id = book_id, username = username, issue_date = issue.issue_date)
                db.session.add(new_issue_history)
                db.session.delete(issue)
                db.session.commit()
                return redirect(url_for('user_explore_books'))
            else:
                return render_template('user/error.html', error = 'This user is not permitted to perform this action.')


        else:
            return redirect(url_for('user_login'))




######################### Controllers for the Librarian ###############################################




@app.route('/lib_login', methods = ['GET', 'POST']) # End point for the librarian login

def lib_login():
    if request.method == 'GET':
        return render_template('lib/lib_login.html')
    else:
        # Logic for password verification
        username = request.form.get('username')
        password = request.form.get('password')

        lib_auth = db.session.query(Authentication).filter((Authentication.username == username) & (Authentication.user_type == 'lib')).first()

        if not lib_auth:
            return render_template('lib/lib_error.html', error='There is no librarian with the given username.')

        if (lib_auth.password == password):
            session['user_logged_in'] = lib_auth.username
            session['user_type'] = 'lib'
            return redirect(url_for('lib_dashboard'))
        else:
            return render_template('lib/lib_error.html', error='Incorrect credentials, try again!')






@app.route('/lib_home', methods = ['GET', 'POST'])
def lib_dashboard():
    if request.method == 'GET':
        if(session.get('user_logged_in') and (session.get('user_type')=='lib')):
            username = session.get('user_logged_in')
            book_requests = db.session.query(Book_Request).all()
            duration = [{req.duration.split(' ')[1]: req.duration.split(' ')[0], req.duration.split(' ')[3]: req.duration.split(' ')[2], req.duration.split(' ')[5]: req.duration.split(' ')[4]} for req in book_requests]
            requested_books = [{'req': req, 'book': db.session.query(Book).filter(Book.id == req.book_id).first(), 'user': db.session.query(Users).filter(Users.username == req.username).first()} for req in book_requests]
            return render_template('lib/lib_dashboard.html', username = username, requested_books = requested_books, duration = duration)
        else:
            return redirect(url_for('lib_login'))


@app.route('/lib_books', methods = ['GET', 'POST'])
def lib_books():
    if request.method == 'GET':
        if(session.get('user_logged_in') and (session.get('user_type')=='lib')):
            username = session.get('user_logged_in')
            sections = db.session.query(Section).all()
            search_str = ""
            search_str = request.args.get('search_str')
            if not search_str:
                return render_template('lib/lib_books.html', username = username, sections = sections)
            else:
                t_search_str = search_str
                search_str = '%' + search_str + '%'
                result_books = []
                books_by_name = db.session.query(Book).filter(Book.search_name.like(search_str)).all()
                books_by_authors = db.session.query(Book).filter(Book.search_authors.like(search_str)).all()
                section_by_section_name = db.session.query(Section).filter(Section.search_name.like(search_str)).all()

                for book in books_by_name:
                    if book not in result_books:
                        result_books.append(book)

                for book in books_by_authors:
                    if book not in result_books:
                        result_books.append(book)

                for section in section_by_section_name:
                    books_of_section = db.session.query(Book).filter(Book.section_id == section.id).all()
                    for book in books_of_section:
                        if book not in result_books:
                            result_books.append(book)

                return render_template('lib/lib_search_book.html', username=username, result_books=result_books,
                                       search_str=t_search_str)

        else:
            return redirect(url_for('lib_login'))


@app.route('/lib_users', methods = ['GET', 'POST'])
def lib_users():
    if request.method == 'GET':
        if(session.get('user_logged_in') and (session.get('user_type')=='lib')):
            username = session.get('user_logged_in')
            users = db.session.query(Users).all()

            search_str = ""
            search_str = request.args.get('search_str')

            if not search_str:
                return render_template('lib/lib_users.html', username = username, users = users)
            else:
                t_search_str = search_str
                search_str = '%' + search_str + '%'
                user_by_name = db.session.query(Users).filter(Users.search_name.like(search_str)).all()
                user_by_email = db.session.query(Users).filter(Users.email.like(search_str)).all()
                user_by_username = db.session.query(Users).filter(Users.username.like(search_str)).all()

                result_users = []

                for user in user_by_name:
                    if user not in result_users:
                        result_users.append(user)

                for user in user_by_email:
                    if user not in result_users:
                        result_users.append(user)

                for user in user_by_username:
                    if user not in result_users:
                        result_users.append(user)




                return render_template('lib/lib_search_users.html', username=username, result_users=result_users,
                                       search_str=t_search_str)


        else:
            return redirect(url_for('lib_login'))

@app.route('/lib_users/users/<username>', methods = ['GET', 'POST'])
def lib_user_details(username):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'lib')):
            lib_username = session.get('user_logged_in')
            user = db.session.query(Users).filter(Users.username == username).first()

            ### Checking for issues validity

            issues = db.session.query(Book_Issue).filter(Book_Issue.username == username).all()
            cur_date_time = datetime.datetime.now()
            for issue in issues:
                if issue.return_date < cur_date_time:
                    new_issue_history = Book_Issue_History(book_id=issue.book_id, username=issue.username,
                                                           issue_date=issue.issue_date, returned_date=issue.return_date)
                    db.session.add(new_issue_history)
                    db.session.delete(issue)
                    db.commit()

            #############

            issues = db.session.query(Book_Issue).filter(Book_Issue.username == username).all()

            books_issued = [(db.session.query(Book).filter(Book.id == issue.book_id).first(), issue) for issue in issues]
            return render_template('lib/lib_user_details.html', username = lib_username, user = user, books_issued = books_issued)
        else:
            return redirect(url_for('lib_login'))


@app.route('/lib_users/users/<username>/update', methods = ['POST'])
def lib_user_update(username):
    if request.method == 'POST':
        if (session.get('user_logged_in') and (session.get('user_type') == 'lib')):
            lib_username = session.get('user_logged_in')
            user = db.session.query(Users).filter(Users.username == username).first()
            f_name = request.form.get('f_name')
            l_name = request.form.get('l_name')
            search_name = f_name.lower().replace('.', '')+' '+l_name.lower().replace('.', '')
            email = request.form.get('email')
            username = request.form.get('username')

            user.f_name = f_name
            user.l_name = l_name
            user.search_name = search_name
            user.email = email


            db.session.add(user)
            db.session.commit()
            return render_template('lib/lib_confirm_message.html', message = 'User successfully updated!!', go_to_name = 'Go to Users', go_to_path = '/lib_users')


@app.route('/lib_users/users/<username>/delete', methods=['GET'])
def lib_user_delete_confirm(username):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'lib')):
            lib_username = session.get('user_logged_in')
            user = db.session.query(Users).filter(Users.username == username).first()
            if not user:
                return render_template('lib/lib_error.html', error = "There is no such user!! ")
            return render_template('lib/lib_confirm_message.html', username = lib_username, message='This will delete all the associated requests, purchases, current issue and past issue details!! Are You Sure?',
                                   go_to_name=f'Delete user {username}', go_to_path=f'/lib_users/users/{username}/delete/final')
    else:
        return redirect(url_for('lib_login'))

@app.route('/lib_users/users/<username>/delete/final', methods=['GET'])
def lib_user_delete_final(username):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'lib')):
            lib_username = session.get('user_logged_in')
            user = db.session.query(Users).filter(Users.username == username).first()
            if not user:
                return render_template('lib/lib_error.html', error = "There is no such user!! ")
            user_req = db.session.query(Book_Request).filter(Book_Request.username == username).all()
            for req in user_req:
                db.session.delete(req)
            user_issue = db.session.query(Book_Issue).filter(Book_Issue.username == username).all()
            for issue in user_issue:
                db.session.delete(issue)
            user_issue_history = db.session.query(Book_Issue_History).filter(Book_Issue_History.username == username).all()
            for issue_history in user_issue_history:
                db.session.delete(issue_history)
            user_purchase = db.session.query(Book_Purchase).filter(Book_Purchase.username == username).all()
            for purchase in user_purchase:
                db.session.delete(purchase)

            user_auth = db.session.query(Authentication).filter(Authentication.username == username).first()
            db.session.delete(user)
            db.session.delete(user_auth)
            db.session.commit()


            return render_template('lib/lib_confirm_message.html', username = lib_username, message='User successfully deleted.',
                                   go_to_name='Go to Users', go_to_path='/lib_users')

    else:
        return redirect(url_for('lib_login'))



def create_lib_bar_graph(issue_history, issue_dates):

    book_history = [db.session.query(Book).filter(Book.id == issue.book_id).first() for issue in issue_history]
    sections = [db.session.query(Section).filter(Section.id == book.section_id).first().name for book in book_history]
    section_dict = {}
    for section in sections:
        if(section not in section_dict.keys()):
            section_dict[section] = 1
        else:
            section_dict[section] += 1

    values = []
    labels = []

    for section in section_dict.keys():
        values.append(section_dict[section])
        labels.append(section)

    issue_months = []
    months = {
        1:'Jan',
        2:'Feb',
        3:'Mar',
        4:'Apr',
        5:'May',
        6:'Jun',
        7:'Jul',
        8:'Aug',
        9:'Sep',
        10:'Oct',
        11:'Nov',
        12:'Dec'
    }

    total_books = db.session.query(Book).all()
    t_sections = [db.session.query(Section).filter(Section.id == book.section_id).first().name for book in total_books]

    t_section_dict = {}
    for section in t_sections:
        if (section not in t_section_dict.keys()):
            t_section_dict[section] = 1
        else:
            t_section_dict[section] += 1

    t_values = []
    t_labels = []

    for section in t_section_dict.keys():
        t_values.append(t_section_dict[section])
        t_labels.append(section)



    for d in issue_dates:
        issue_months.append(months[d.month])


    plt.clf()
    plt.hist(issue_months, color = 'brown')
    plt.xlabel('Months')
    plt.ylabel('No of Books Issued')
    plt.title('Books issued vs Month')
    plt.savefig(f'static/charts/lib/lib_hist.png')


    plt.clf()
    plt.pie(values, labels = labels)
    plt.xlabel('Section wise distribution of the issued books')
    plt.savefig(f'static/charts/lib/lib_pie.png')

    plt.clf()
    plt.pie(t_values, labels=t_labels)
    plt.xlabel('Section wise distribution of total available books')
    plt.savefig(f'static/charts/lib/lib_pie_total.png')



@app.route('/lib_stats', methods = ['GET', 'POST'])
def lib_stats():
    if request.method == 'GET':
        if(session.get('user_logged_in') and (session.get('user_type')=='lib')):
            username = session.get('user_logged_in')
            issue_history = db.session.query(Book_Issue_History).all()
            issue_dates = [issue.issue_date for issue in issue_history]
            create_lib_bar_graph(issue_history, issue_dates)

            return render_template('lib/lib_stats.html', username=username)
        else:
            return redirect(url_for('lib_login'))

@app.route('/lib_books/section/<int:section_id>/add_book', methods = ['GET', 'POST'])
def lib_add_book(section_id):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'lib')):
            username = session.get('user_logged_in')
            section = db.session.query(Section).filter(Section.id == section_id).first()
            return render_template('lib/lib_add_book.html', username=username, section = section)
        else:
            return redirect(url_for('lib_login'))
    else:
        name = request.form.get('name')
        search_name = name.lower().replace(',', ' ').replace('.', '').replace(' ', '_')
        authors = request.form.get('authors')
        search_authors = authors.lower().replace(',', ' ').replace('.', '')
        no_of_pages = request.form.get('no_of_pages')
        vol = request.form.get('vol')
        if request.files['content'].filename != '':
            content = request.files['content']
            content.filename = search_name + '.pdf'
            content.save('static/books/content/' + content.filename)
        else:
            return render_template('lib/lib_error.html', error = 'No Content file was uploaded, try again.')
        if request.files['thumbnail'].filename != '':
            thumbnail = request.files['thumbnail']
            thumbnail.filename = search_name + '.png'
            thumbnail.save('static/books/thumbnail/' + thumbnail.filename)
        else:
            return render_template('lib/lib_error.html', error='No Thumbnail image was uploaded, try again.')

        new_book = Book(name=name, search_name=search_name, authors=authors,
                        search_authors=search_authors, content=search_name + '.pdf', no_of_pages=no_of_pages, vol=vol,
                        section_id=section_id)
        db.session.add(new_book)
        db.session.commit()
        return render_template('lib/lib_confirm_message.html', message='Book successfully added.', go_to_name='Go to Books', go_to_path='/lib_books')



@app.route('/lib_books/section/add', methods = ['GET', 'POST'])
def lib_books_add_section():
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'lib')):
            username = session.get('user_logged_in')
            return render_template('lib/lib_add_section.html', username=username)
        else:
            return redirect(url_for('lib_login'))
    else:
        name = request.form.get('name')
        search_name = name.lower().replace(',', ' ').replace('.', ' ').replace(' ', '_')
        description = request.form.get('description')
        if 'thumbnail' in request.files:
            thumbnail = request.files['thumbnail']
            thumbnail.filename = search_name + '.png'
            thumbnail.save('static/sections/thumbnails/' + thumbnail.filename)
        else:
            return render_template('lib/lib_error.html', error='No Thumbnail image was uploaded, try again.')

        new_section = Section(name=name, search_name=search_name, description =description)
        db.session.add(new_section)
        db.session.commit()
        return render_template('lib/lib_confirm_message.html', message='Section successfully added.', go_to_name='Go to Books',
                               go_to_path='/lib_books')


@app.route('/lib_books/sections/<int:section_id>', methods = ['GET', 'POST'])
def lib_section_details(section_id):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'lib')):
            lib_username = session.get('user_logged_in')
            section = db.session.query(Section).filter(Section.id == section_id).first()

            return render_template('lib/lib_section_update.html', username = lib_username, section = section)
        else:
            return redirect(url_for('lib_login'))


@app.route('/lib_books/sections/<int:section_id>/update', methods = ['POST'])
def lib_section_update(section_id):
    if request.method == 'POST':
        if (session.get('user_logged_in') and (session.get('user_type') == 'lib')):
            lib_username = session.get('user_logged_in')
            section = db.session.query(Section).filter(Section.id == section_id).first()
            name = request.form.get('name')
            description = request.form.get('description')
            search_name = name.lower().replace('.', '').replace(' ', '_')
            if request.files['thumbnail'].filename != '':
                thumbnail = request.files['thumbnail']
                thumbnail.filename = search_name + '.png'
                thumbnail.save('static/sections/thumbnails/' + thumbnail.filename)
            else:
                os.rename('static/sections/thumbnails/'+section.search_name+'.png', 'static/sections/thumbnails/'+search_name+'.png')

            section.name = name
            section.description = description
            section.search_name = search_name
            db.session.add(section)
            db.session.commit()
            return render_template('lib/lib_confirm_message.html', message='Section successfully updated!!',
                                   go_to_name='Go to Books', go_to_path='/lib_books')
    else:
        return redirect(url_for('lib_login'))


@app.route('/lib_books/sections/<int:section_id>/delete', methods=['GET'])
def lib_section_delete_confirm(section_id):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'lib')):
            lib_username = session.get('user_logged_in')
            section = db.session.query(Section).filter(Section.id == section_id).first()
            if not section:
                return render_template('lib/lib_error.html', error = "There is no such section!! ")
            return render_template('lib/lib_confirm_message.html', username = lib_username, message='This will delete all the associated books, requests, current issue and past issue details!! Are You Sure?',
                                   go_to_name=f'Delete section {section.name}', go_to_path=f'/lib_books/sections/{section.id}/delete/final')
    else:
        return redirect(url_for('lib_login'))

@app.route('/lib_books/sections/<int:section_id>/delete/final', methods=['GET'])
def lib_section_delete_final(section_id):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'lib')):
            lib_username = session.get('user_logged_in')
            section = db.session.query(Section).filter(Section.id == section_id).first()
            if not section:
                return render_template('lib/lib_error.html', error = "There is no such section!! ")

            sec_books = db.session.query(Book).filter(Book.section_id == section_id).all()
            for book in sec_books:
                book_req = db.session.query(Book_Request).filter(Book_Request.book_id == book.id).all()
                for req in book_req:
                    db.session.delete(req)
                book_issue = db.session.query(Book_Issue).filter(Book_Issue.book_id == book.id).all()
                for issue in book_issue:
                    db.session.delete(issue)
                book_issue_history = db.session.query(Book_Issue_History).filter(Book_Issue_History.book_id == book.id).all()
                for issue_history in book_issue_history:
                    db.session.delete(issue_history)
                book_purchase = db.session.query(Book_Purchase).filter(Book_Purchase.book_id == book.id).all()
                for purchase in book_purchase:
                    db.session.delete(purchase)

            db.session.delete(section)
            db.session.commit()


            return render_template('lib/lib_confirm_message.html', username = lib_username, message='Section successfully deleted.',
                                   go_to_name='Go to Books', go_to_path='/lib_books')

    else:
        return redirect(url_for('lib_login'))





@app.route('/lib_books/section/<int:section_id>', methods = ['GET', 'POST'])
def lib_sec_books(section_id):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'lib')):
            username = session.get('user_logged_in')
            section = db.session.query(Section).filter(Section.id == section_id).first()
            books_of_section = db.session.query(Book).filter(Book.section_id == section.id).all()
            return render_template('lib/lib_sec_books.html', username = username, section = section, books = books_of_section)
        else:
            return redirect(url_for('lib_login'))



@app.route('/lib_books/books/<int:book_id>', methods = ['GET', 'POST'])
def lib_book_details(book_id):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'lib')):
            username = session.get('user_logged_in')
            sections = db.session.query(Section).all()
            book = db.session.query(Book).filter(Book.id == book_id).first()

            ### Checking for issues validity

            issues = db.session.query(Book_Issue).filter(Book_Issue.book_id == book_id).all()
            cur_date_time = datetime.datetime.now()
            for issue in issues:
                if issue.return_date < cur_date_time:
                    new_issue_history = Book_Issue_History(book_id=issue.book_id, username=issue.username,
                                                           issue_date=issue.issue_date, returned_date=issue.return_date)
                    db.session.add(new_issue_history)
                    db.session.delete(issue)
                    db.commit()

            #####################################

            issues = db.session.query(Book_Issue).filter(Book_Issue.book_id == book_id).all()

            users_issued = [(db.session.query(Users).filter(Users.username == issue.username).first(), issue)  for issue in issues]
            return render_template('lib/lib_book_details.html', username = username, book = book, users_issued = users_issued, sections = sections)
        else:
            return redirect(url_for('lib_login'))



@app.route('/lib_books/books/<int:book_id>/content/view', methods = ['GET', 'POST'])
def lib_book_content_view(book_id):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'lib')):
            username = session.get('user_logged_in')
            book = db.session.query(Book).filter(Book.id == book_id).first()
            pdf_path = '/static/books/content/'+book.search_name+'.pdf'
            return render_template('lib/pdf_viewer.html', username = username, param = book, pdf_url = pdf_path)
        else:
            return redirect(url_for('lib_login'))


@app.route('/lib_books/books/<int:book_id>/thumbnail/view', methods = ['GET', 'POST'])
def lib_book_thumbnail_view(book_id):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'lib')):
            username = session.get('user_logged_in')
            book = db.session.query(Book).filter(Book.id == book_id).first()
            thumbnail_path = '/static/books/thumbnail/'+book.search_name+'.png'
            return render_template('lib/pdf_viewer.html', username = username, param = book, pdf_url = thumbnail_path)
        else:
            return redirect(url_for('lib_login'))


@app.route('/lib_books/sections/<int:section_id>/thumbnail/view', methods = ['GET', 'POST'])
def lib_section_thumbnail_view(section_id):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'lib')):
            username = session.get('user_logged_in')
            section = db.session.query(Section).filter(Section.id == section_id).first()
            thumbnail_path = '/static/sections/thumbnails/'+section.search_name+'.png'
            return render_template('lib/pdf_viewer.html', username = username, param = section, pdf_url = thumbnail_path)
        else:
            return redirect(url_for('lib_login'))




@app.route('/lib_books/books/<int:book_id>/update', methods = ['POST'])
def lib_book_update(book_id):
    if request.method == 'POST':
        if (session.get('user_logged_in') and (session.get('user_type') == 'lib')):
            username = session.get('user_logged_in')
            book = db.session.query(Book).filter(Book.id == book_id).first()
            name = request.form.get('name')
            search_name = name.lower().replace(',', ' ').replace('.', ' ').replace(' ', '_')
            authors = request.form.get('authors')
            search_authors = authors.lower().replace(',', ' ').replace('.', ' ')
            no_of_pages = request.form.get('no_of_pages')
            vol = request.form.get('vol')
            section_id = request.form.get('section_id')
            if request.files['content'].filename != '':
                content = request.files['content']
                content.filename = search_name + '.pdf'
                content.save('static/books/content/' + content.filename)
            else:
                os.rename('static/books/content/'+book.search_name+'.pdf', 'static/books/content/'+search_name+'.pdf')
            if request.files['thumbnail'].filename != '':
                thumbnail = request.files['thumbnail']
                thumbnail.filename = search_name + '.png'
                thumbnail.save('static/books/thumbnail/' + thumbnail.filename)
            else:
                os.rename('static/books/thumbnail/'+book.search_name+'.png', 'static/books/thumbnail/'+search_name+'.png')

            book.name=name
            book.search_name=search_name
            book.authors=authors
            book.search_authors=search_authors
            book.content=search_name + '.content'
            book.no_of_pages=no_of_pages
            book.vol=vol
            book.section_id=section_id
            db.session.add(book)
            db.session.commit()
            return render_template('lib/lib_confirm_message.html', message = 'Book successfully updated!!', go_to_name = 'Go to Books', go_to_path = '/lib_books')



@app.route('/lib_books/books/<int:book_id>/delete', methods=['GET'])
def lib_book_delete_confirm(book_id):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'lib')):
            lib_username = session.get('user_logged_in')
            book = db.session.query(Book).filter(Book.id == book_id).first()
            if not book:
                return render_template('lib/lib_error.html', error="There is no such book!! ")
            return render_template('lib/lib_confirm_message.html', username=lib_username,
                                   message='This will delete all the associated requests, purchases, current issue and past issue details!! Are You Sure?',
                                   go_to_name=f'Delete book {book.name}',
                                   go_to_path=f'/lib_books/books/{book.id}/delete/final')
    else:
        return redirect(url_for('lib_login'))

@app.route('/lib_books/books/<int:book_id>/delete/final', methods=['GET'])
def lib_book_delete_final(book_id):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'lib')):
            lib_username = session.get('user_logged_in')
            book = db.session.query(Book).filter(Book.id == book_id).first()
            if not book:
                return render_template('lib/lib_error.html', error="There is no such book!! ")

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

            return render_template('lib/lib_confirm_message.html', username=lib_username,
                                   message='Book successfully deleted.',
                                   go_to_name='Go to Books', go_to_path='/lib_books')

    else:
        return redirect(url_for('lib_login'))



@app.route('/lib_books/books/<int:book_id>/issue/<username>', methods = ['GET', 'POST'])
def lib_issue_book(book_id, username):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'lib')):
            lib_username = session.get('user_logged_in')
            return_date = datetime.datetime.now()
            book_request = db.session.query(Book_Request).filter((Book_Request.book_id == book_id) & (Book_Request.username == username)).first()
            if not book_request:
                return render_template('lib/lib_error.html', error = 'There is no such request')
            else:
                duration = book_request.duration
                weeks = duration.split(' ')[0]
                days = duration.split(' ')[2]
                hours = duration.split(' ')[4]
                if((not(hours)) and (not(days)) and (not(weeks))):
                    return_date += datetime.timedelta(days = 7)

                if(hours):
                    return_date += datetime.timedelta(hours = int(hours))
                if(days):
                    return_date += datetime.timedelta(days=int(days))
                if(weeks):
                    return_date += datetime.timedelta(weeks=int(weeks))

                new_issue =  Book_Issue(book_id = book_id, username = username, issue_date = datetime.datetime.now(), return_date = return_date)
                db.session.add(new_issue)
                db.session.delete(book_request)
                db.session.commit()
                return redirect(url_for('lib_dashboard'))


        else:
            return redirect(url_for('lib_login'))



@app.route('/lib_books/books/<int:book_id>/reject/<username>', methods = ['GET', 'POST'])
def lib_reject_book(book_id, username):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'lib')):
            lib_username = session.get('user_logged_in')
            book_request = db.session.query(Book_Request).filter((Book_Request.book_id == book_id) & (Book_Request.username == username)).first()
            if not book_request:
                return render_template('error.html', error = 'There is no such request')
            else:
                db.session.delete(book_request)
                db.session.commit()
                return redirect(url_for('lib_dashboard'))
        else:
            return redirect(url_for('lib_login'))

@app.route('/lib_books/books/<int:book_id>/revoke/<username>', methods = ['GET', 'POST'])
def lib_revoke_book(book_id, username):
    if request.method == 'GET':
        if (session.get('user_logged_in') and (session.get('user_type') == 'lib')):
            lib_username = session.get('user_logged_in')
            book_issue = db.session.query(Book_Issue).filter((Book_Issue.book_id == book_id) & (Book_Issue.username == username)).first()
            if not book_issue:
                return render_template('error.html', error = 'There is no such issue of this book.')
            else:
                new_issue_history = Book_Issue_History(book_id=book_id, username=username, issue_date=book_issue.issue_date)
                db.session.add(new_issue_history)
                db.session.delete(book_issue)
                db.session.commit()
                return redirect(request.referrer)
        else:
            return redirect(url_for('lib_login'))






############################################### Common controller ########################################################
@app.route('/logout', methods = ['GET']) # End point for the user/lib logout
def logout():
    if request.method == 'GET' and session.get('user_type') == 'user':
        session.pop('user_logged_in', None)
        session.pop('user_type', None)
        return redirect(url_for('user_login'))
    else:
        if request.method == 'GET' and session.get('user_type') == 'lib':
            session.pop('user_logged_in', None)
            session.pop('user_type', None)
            return redirect(url_for('lib_login'))










