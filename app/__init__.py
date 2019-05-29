
from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
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
from logging.handlers import RotatingFileHandler
import os

from flask_mail import Mail

app = Flask(__name__)
app.config.from_object(Config)

# handler = RotatingFileHandler('app.log', maxBytes=100000, backupCount=3)
# logger = logging.getLogger('tdm')
# logger.setLevel(logging.ERROR)
# logger.addHandler(handler)

from flask_talisman import Talisman
csp = {
    'default-src': [
      '\'self\'',
      'https://*.amplitude.com'
    ],
    'img-src': '*',
    'media-src' : '*',
    'script-src': [
        '\'self\'',
        'https://*.cloudflare.com',
        'https://*.datatables.net',
        'https://*.jsdelivr.net',
        'https://*.amplitude.com'
    ],
   'style-src' : [
       '\'self\'',
       'https://*.datatables.net',
   ]
}

Talisman(app, content_security_policy=csp, content_security_policy_nonce_in=['script-src'])

db = SQLAlchemy(app)
migrate = Migrate(app, db)

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
    app.run()

