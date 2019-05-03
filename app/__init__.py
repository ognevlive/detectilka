from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login = LoginManager(app)
login.login_view = 'login'

from app import routes

import sys
sys.path.insert(0, 'classificator/docx')
import docx 
docx.classifier.train()



# from app.models import User

# u = User(username='susan', email='susan@example.com')
# u.set_password('cat')
# db.session.add(u)
# db.session.commit()