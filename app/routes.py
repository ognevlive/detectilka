from flask import render_template, flash, redirect, url_for
from app import app
from app.forms import LoginForm, SamplesListForm, SampleEntryForm
from flask_login import current_user, login_user, logout_user, login_required
from app.models import User, Sample
from flask import request
from werkzeug.urls import url_parse
from app import db
from app.forms import RegistrationForm
from werkzeug.utils import secure_filename
from datetime import datetime
from hashlib import md5
import os

import sys
sys.path.insert(0, 'classificator/docx')
import docx 

def allowed_file(file):
	ext = file.split('.')[-1]
	if ext in app.config['ALLOWED_EXTENSIONS']:
		return True
	return False

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/upload', methods=['GET', 'POST'])
@login_required
def index():
	if request.method == 'POST':
		file = request.files['file']
		if file:# and allowed_file(file.filename):
			if request.form.get('isAnon'):
				owner = User.query.filter_by(username="Anonym").first()
			else:
				owner = anonymous_user

			filename = file.filename
			filename_secure = secure_filename(file.filename)
			filename_saved  = '%s__%s' % (filename_secure, str(datetime.utcnow()))

			file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_saved))

			sample = Sample(filename=filename, owner=owner, status='Analyzed')
			sample.hash = md5(open('uploads/' + filename_saved,'rb').read()).hexdigest()



			db.session.add(sample)
			db.session.commit()

			print 'predict?'
			docx.classifier.predict(filename_saved, sample)

			flash('File uploaded!')
	return render_template('index.html', title='Detectilka')


@app.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(username=form.username.data).first()
		if user is None or not user.check_password(form.password.data):
			flash('Invalid username or password')
			return redirect(url_for('login'))
		login_user(user, remember=form.remember_me.data)
		next_page = request.args.get('next')
		if not next_page or url_parse(next_page).netloc != '':
			next_page = url_for('index')
		return redirect(next_page)
	return render_template('login.html', title='Login Page', form=form)


@app.route('/logout')
def logout():
	logout_user()
	return redirect(url_for('index'))


@app.route('/register', methods=['GET', 'POST'])
def register():
	if current_user.is_authenticated:
		return redirect(url_for('index'))
	form = RegistrationForm()
	if form.validate_on_submit():
		user = User(username=form.username.data, email=form.email.data)
		user.set_password(form.password.data)
		db.session.add(user)
		db.session.commit()
		flash('Congratulations, you are now a registered user!')
		return redirect(url_for('login'))
	return render_template('register.html', title='Register', form=form)



@app.route('/user/<username>')
@login_required
def user(username):
	user = User.query.filter_by(username=username).first_or_404()
	samples_form = SamplesListForm()
	for sample in current_user.samples.all():
		entry_form = SampleEntryForm()
		entry_form.init(sample)
		samples_form.samples.append_entry(entry_form)

	return render_template('user.html', user=user, samples=samples_form.samples)


@app.route('/search', methods=['POST'])
def search():
	if request.method == 'POST':
		req = request.values['req']
		samples_form = SamplesListForm()
		for sample in Sample.query.filter(Sample.filename.contains(req)).all():
			entry_form = SampleEntryForm()
			entry_form.init(sample)
			samples_form.samples.append_entry(entry_form)
		return render_template('search.html', req=req, samples=samples_form.samples)
	return render_template('search.html', req=req)


@app.route('/search_result', methods=['GET'])
def search_result():
	samples = parseSearchArgs(request.args)
	return render_template('samples.html', samples=samples)



def parseSearchArgs(args):
	query = { }
	for req in args:
		param = args[req].lower()
		query.update({req : param})

	samples_form = SamplesListForm()
	
	from datetime import datetime

	if 'hash' in query: h = Sample.hash == query['hash']
	else: h = Sample.hash.isnot(False)

	if 'filename' in query: f = Sample.filename.contains(query['filename'])
	else: f = Sample.filename.isnot(False)

	if 'answer' in query: a = Sample.answer.contains(query['answer'])
	else: a = Sample.answer.isnot(False)

	if 'time' in query: t = Sample.timestamp <= datetime.strptime(query['time'], '%Y-%m-%d')
	else: t = Sample.timestamp.isnot(False)

	for sample in Sample.query.filter(h & f & a & t).all():
		entry_form = SampleEntryForm()
		entry_form.init(sample)	

		samples_form.samples.append_entry(entry_form)

	return samples_form.samples



@app.route('/report/<id>', methods=['GET'])
def report(id):
	sample = Sample.query.filter_by(id=id).first_or_404()

	entry_form = SampleEntryForm()
	entry_form.init(sample)
	
	samples_form = SamplesListForm()
	samples_form.samples.append_entry(entry_form)

	return render_template('report.html', samples=samples_form.samples)