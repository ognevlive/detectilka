from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from logging.handlers import RotatingFileHandler
from flask_bootstrap import Bootstrap
import logging
import os

from flask_mail import Mail

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login = LoginManager(app)
login.login_view = 'login'

bootstrap = Bootstrap(app)

mail = Mail(app)

from app import routes, models, errors, api

import sys
sys.path.insert(0, 'classificator/docx')
import docx 
docx.classifier.train()

# from app.models import User

# u = User(username='susan', email='susan@example.com')
# u.set_password('cat')
# db.session.add(u)
# db.session.commit()
