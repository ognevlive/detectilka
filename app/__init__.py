from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
import logging
from logging.handlers import RotatingFileHandler
import os
from flask_bootstrap import Bootstrap


def createAnonymUser():
	anon = models.User.query.filter_by(username="Anonym").first()
	if anon == None:
		from random import choice
		from string import ascii_uppercase
		user = models.User(username="Anonym", email="Anonym")
		user.set_password(''.join(choice(ascii_uppercase) for i in range(64)))
		db.session.add(user)
		db.session.commit()

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login = LoginManager(app)
login.login_view = 'login'

bootstrap = Bootstrap(app)

from app import routes, models, errors, api

import sys
sys.path.insert(0, 'classificator/docx')
import docx 
docx.classifier.train()

createAnonymUser()

if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/detectilka.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)



# from app.models import User

# u = User(username='susan', email='susan@example.com')
# u.set_password('cat')
# db.session.add(u)
# db.session.commit()