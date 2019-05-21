from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from logging.handlers import RotatingFileHandler
from flask_bootstrap import Bootstrap
from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    jwt_refresh_token_required, create_refresh_token,
    get_jwt_identity, set_access_cookies,
    set_refresh_cookies, unset_jwt_cookies
)  
from flask_bcrypt import Bcrypt

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

jwt = JWTManager(app)
flask_bcrypt = Bcrypt(app)

from app import routes, models, errors, api, auth

import sys
sys.path.insert(0, 'classificator/docx')
import docx 
docx.classifier.train()

if __name__ == '__main__':
    app.run(host='0.0.0.0')

# from app.models import User

# u = User(username='susan', email='susan@example.com')
# u.set_password('cat')
# db.session.add(u)
# db.session.commit()
