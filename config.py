import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
	SECRET_KEY = os.environ.get('SECRET_KEY') or 'mykey'
	SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
	'sqlite:///' + os.path.join(basedir, 'app.db')
	SQLALCHEMY_TRACK_MODIFICATIONS = False
	ALLOWED_EXTENSIONS = set(['exe', 'doc', 'docx', 'pdf'])
	UPLOAD_FOLDER = 'uploads/'
	MAX_CONTENT_LENGTH = 128 * 1024 * 1024