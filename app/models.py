from datetime import datetime
from app import db, login, app
from werkzeug.security import generate_password_hash, check_password_hash
from time import time
import jwt
import flask_bcrypt
import os
import magic
from hashlib import md5
from werkzeug.utils import secure_filename


class User(db.Model):
    password_hash = db.Column(db.String(128))
    access_token  = db.Column(db.String(256), index=True)
    csrf_access_token  = db.Column(db.String(256), index=True)
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), index=True, unique=True)
    username = db.Column(db.String(64), index=True, unique=True)
    samples = db.relationship('Sample', backref='owner', lazy='dynamic')
    info    = db.relationship('PrivateInfo', backref='owner', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = flask_bcrypt.generate_password_hash(password)

    def check_password(self, password):
        return flask_bcrypt.check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username)


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Sample(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    filename = db.Column(db.String(128, collation='NOCASE'), index=True)
    user_id   = db.Column(db.Integer, db.ForeignKey('user.id'))
    hash      = db.Column(db.String(128), index=True)
    answer    = db.Column(db.String(16), index=True)
    status    = db.Column(db.String(16), index=True)
    is_anon   = db.Column(db.Boolean, index=True)

    filesize = db.Column(db.Integer)
    words    = db.Column(db.Integer)
    pages    = db.Column(db.Integer)
    characters     = db.Column(db.Integer)
    totaledittime  = db.Column(db.Integer)
    revisionnumber = db.Column(db.Integer)

    title = db.Column(db.String(128))
    creator = db.Column(db.String(128))
    company = db.Column(db.String(128))
    lastprinted = db.Column(db.String(128))
    createdate  = db.Column(db.String(128))
    lastmodifiedby = db.Column(db.String(128))

    def __repr__(self):
        return '<Sample {}>'.format(self.filename)

    def saveFile(self, file):
        filename_secure = secure_filename(self.filename)
        filename_saved  = '%s__%s' % (filename_secure, str(datetime.utcnow()))
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_saved))
        self.hash = md5(open('uploads/' + filename_saved,'rb').read()).hexdigest()
        return filename_saved


class PrivateInfo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    platform  = db.Column(db.String(64))
    browser   = db.Column(db.String(64))
    language  = db.Column(db.String(64))
    user_id   = db.Column(db.Integer, db.ForeignKey('user.id'))
    refresh_token = db.Column(db.String(256), index=True)
    access_token = db.Column(db.String(256), index=True)

    def __repr__(self):
        return '<PrivateInfo {}>'.format(self.access_token)


class Stats(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    malware_count = db.Column(db.Integer)
    safe_count = db.Column(db.Integer)

    last_update = db.Column(db.DateTime)

    extentions = {}

    def __repr__(self):
        return '<Stats {}>'.format(self.access_token)

    def get(self):
        if self.last_update == None or self.last_update + 5000 < datetime.now():
            print 'need update'
        self.updateTypeStats()

    def updateTypeStats(self):
        self.extentions = {}
        for file in os.listdir('uploads'):
            ext = magic.from_file('uploads/' + file)
            end = ext.find(',')
            ext = ext[:end]
            if ext in self.extentions:
                self.extentions.update({ext : self.extentions[ext] + 1})
            else:
                self.extentions.update({ext : 1})

        self.counts = list(self.extentions.values())
        self.names  = list(self.extentions.keys())

