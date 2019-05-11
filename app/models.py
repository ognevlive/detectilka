from datetime import datetime
from app import db, login, app
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from time import time
import jwt
import flask_bcrypt
import os
from hashlib import md5
from werkzeug.utils import secure_filename


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    samples = db.relationship('Sample', backref='owner', lazy='dynamic')
    access_token  = db.Column(db.String(256), index=True)
    refresh_token = db.Column(db.String(256), index=True)

    def set_password(self, password):
        self.password_hash = flask_bcrypt.generate_password_hash(password)

    def check_password(self, password):
        return flask_bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def encode_auth_token(self, user_id):
        try:
            payload = {
                'exp': datetime.utcnow() + datetime.timedelta(days=0, seconds=5),
                'iat': datetime.utcnow(),
                'sub': user_id
            }
            return jwt.encode(
                payload,
                app.config.get('JWT_SECRET_KEY'),
                algorithm='HS256'
            )
        except Exception as e:
            return e

    def validateAccessToken(self, token):
        if token == self.access_token:
            return True
        return False


    # def get_reset_password_token(self, expires_in=600):
    #     return jwt.encode(
    #         {'reset_password': self.id, 'exp': time() + expires_in},
    #         app.config['SECRET_KEY'], algorithm='HS256').decode('utf-8')

    # @staticmethod
    # def verify_reset_password_token(token):
    #     try:
    #         id = jwt.decode(token, app.config['SECRET_KEY'],
    #                         algorithms=['HS256'])['reset_password']
    #     except:
    #         return
    #     return User.query.get(id)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    filename = db.Column(db.String(128), index=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('user.id'))
    hash      = db.Column(db.String(128), index=True)
    answer    = db.Column(db.String(16), index=True)
    status    = db.Column(db.String(16), index=True)
    is_anon   = db.Column(db.Boolean, index=True)

    def __repr__(self):
        return '<Sample {}>'.format(self.filename)

    def saveFile(self, file):
        filename_secure = secure_filename(self.filename)
        filename_saved  = '%s__%s' % (filename_secure, str(datetime.utcnow()))
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_saved))
        self.hash = md5(open('uploads/' + filename_saved,'rb').read()).hexdigest()
        return filename_saved