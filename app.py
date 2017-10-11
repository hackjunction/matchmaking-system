#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from flask import Flask, render_template, request, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
import logging
from logging import Formatter, FileHandler
from forms import *
from functools import wraps
from models import *
import os
import json

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
app.config.from_object('config')
db = SQLAlchemy(app)

skills = ['Unix', 'Mac', 'Linux']
jobtitles = ['Manager', 'Frontend Dev', 'Backend Dev']

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

bcrypt = Bcrypt(app)

# Login manager user loade
@login_manager.user_loader
def load_user(user_id):
    user = User.query.filter_by(id=user_id).first()
    return user

# Automatically tear down SQLAlchemy.
@app.teardown_request
def shutdown_session(exception=None):
    print 'Tearing down SQLAlchemy'
    db_session.commit()
    db_session.remove()


#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.errorhandler(404)
def page_not_found(e):
    return redirect(url_for('home'))

@app.route('/', methods=['GET', 'POST'])
@login_required
def home():
    print current_user.excellent_skills
    print current_user.extra_skills
    print current_user.titles
    print current_user.contact_email
    print current_user.company_name
    print current_user.amount_meetings

    errors = []

    form = CompanyForm(request.form)
    if request.method == 'POST':
        if form.validate():
            excellent_skills = form.excellent_skills.data
            extra_skills = form.extra_skills.data
            titles = form.titles.data
            amount_meetings = form.amount_meetings.data

            current_user.company_name = form.name.data
            current_user.contact_email = form.contact_email.data
            current_user.excellent_skills = json.dumps(excellent_skills)
            current_user.extra_skills = json.dumps(extra_skills)
            current_user.titles = json.dumps(titles)
            current_user.amount_meetings = amount_meetings

            try:
                db.session.commit()
            except Exception, e:
                print 'Commit failed'
                db.session.rollback()
                print str(e)
                errors.append('Database commit failure.')


        else:
            print 'Form did not validate:'
            for fieldName, errorMessages in form.errors.items():
                for err in errorMessages:
                    print err

    else:
        if (current_user.company_name is not None):
            # If company name is set, all other data should also already be there
            form.name.data = current_user.company_name
            form.contact_email.data = current_user.contact_email
            form.excellent_skills.data = json.loads(current_user.excellent_skills)
            form.extra_skills.data = json.loads(current_user.extra_skills)
            form.titles.data = json.loads(current_user.titles)
            form.amount_meetings.data = current_user.amount_meetings
        else:
            # Set a couple of default values if user has never submitted form
            form.name.data = current_user.name
            form.contact_email.data = current_user.email
            form.amount_meetings.data = 20

    form.excellent_skills.choices = [(g, g) for g in skills]
    form.extra_skills.choices = [(g, g) for g in skills]
    form.titles.choices = [(g, g) for g in jobtitles]

    return render_template('pages/home.html', form=form, errors=errors)


@app.route('/about')
def about():
    return render_template('pages/about.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    errors = []
    if form.validate_on_submit():
        username = form.name.data
        password = form.password.data

        user = User.query.filter_by(name=username).first()
        if not user:
            print 'User not found'
            errors.append('Invalid login')
            return render_template('forms/login.html', form=form, errors=errors)

        elif not bcrypt.check_password_hash(user.password, password):
            print 'Invalid password'
            errors.append('Invalid login')

        else:
            login_user(user)
            return redirect(url_for('home'))
    else:
        for fieldName, errorMessages in form.errors.items():
            for err in errorMessages:
                print err

    return render_template('forms/login.html', form=form, errors = errors)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    errors = []
    if request.method == 'POST' and form.validate():
        username = form.name.data
        password = form.password.data
        email = form.email.data

        hashed_pass = bcrypt.generate_password_hash(password)
        user = User(username, hashed_pass, email)
        if user:
            db.session.add(user)
            db.session.commit()
            login_user(user)
            return redirect(url_for('home'))
        else:
            errors.append('Invalid reg')

    else:
        for fieldName, errorMessages in form.errors.items():
            for err in errorMessages:
                print err

    return render_template('forms/register.html', form=form, errors=errors)


@app.route('/forgot')
def forgot():
    form = ForgotForm(request.form)
    return render_template('forms/forgot.html', form=form)

# Error handlers.

'''
@app.errorhandler(500)
def internal_error(error):
    db_session.rollback()
    return render_template('errors/500.html'), 500
'''

if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
