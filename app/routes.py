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
import os
from datetime import datetime

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
			filename = secure_filename(file.filename)
			save_filename = '%s__%s' % (filename, str(datetime.utcnow()))
			file.save(os.path.join(app.config['UPLOAD_FOLDER'], save_filename))

			sample = Sample(file_name=filename, owner=current_user)
			db.session.add(sample)
			db.session.commit()

			print 'predict?'
			docx.classifier.predict(save_filename, sample)

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
    	entry_form.file_name = sample.file_name
    	entry_form.answer = sample.answer
    	entry_form.hash = sample.hash

    	samples_form.samples.append_entry(entry_form)

    return render_template('user.html', user=user, samples=samples_form.samples)