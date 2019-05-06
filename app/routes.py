from flask import render_template, flash, redirect, url_for, request
from flask_login import current_user, login_user, logout_user, login_required
from app import app, db
from app.models import User, Sample
from app.email import send_password_reset_email
from app.forms import LoginForm, SamplesListForm, SampleEntryForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from werkzeug.urls import url_parse
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
	return render_template('login.html', title='Sign In', form=form)


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


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
    	user = User.query.filter_by(email=form.email.data).first()
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been set.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', title='Restore Password', form=form)


@app.route('/user/<username>')
@login_required
def user(username):
	user = User.query.filter_by(username=username).first_or_404()
	samples_form = SamplesListForm()
	for sample in current_user.samples.all():
		entry_form = SampleEntryForm()
		entry_form.filename = sample.filename
		entry_form.answer = sample.answer
		entry_form.hash = sample.hash
		entry_form.timestamp = sample.timestamp

		samples_form.samples.append_entry(entry_form)

	return render_template('user.html', title='Profile', user=user, samples=samples_form.samples)


@app.route('/search', methods=['POST'])
def search():
	if request.method == 'POST':
		req = request.values['req']
		samples_form = SamplesListForm()
		if req:
			for sample in Sample.query.all():
				if sample.filename.lower().find(req) != -1:
					entry_form = SampleEntryForm()
					entry_form.filename = sample.filename
					entry_form.answer = sample.answer
					entry_form.hash = sample.hash
					entry_form.timestamp = sample.timestamp

					samples_form.samples.append_entry(entry_form)
		return render_template('search.html', req=req, samples=samples_form.samples)
	return render_template('search.html', title='Search', req=req)


@app.route('/search_result', methods=['GET'])
def search_result():
	query = { }
	for req in request.args:
		param = request.args[req].lower()
		query.update({req : param})

#User.query.order_by(User.username).all()
	samples_form = SamplesListForm()
	if req:
		
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
			entry_form.filename = sample.filename
			entry_form.answer = sample.answer
			entry_form.hash = sample.hash
			entry_form.timestamp = sample.timestamp

			samples_form.samples.append_entry(entry_form)

	return render_template('samples.html', req=req, samples=samples_form.samples)