from flask import render_template, flash, redirect, url_for, request, jsonify, make_response
#from flask_login import current_user, login_user, logout_user, login_required
from app import app, db, jwt, auth
from app.models import User, Sample, PrivateInfo
from app.email import send_password_reset_email
from app.forms import LoginForm, SamplesListForm, SampleEntryForm, RegistrationForm, ResetPasswordRequestForm, ResetPasswordForm
from werkzeug.urls import url_parse
from werkzeug.utils import secure_filename
from datetime import datetime
from hashlib import md5
from flask_jwt_extended import (
	JWTManager, jwt_required, create_access_token,
	jwt_refresh_token_required, create_refresh_token,
	get_jwt_identity, set_access_cookies,
	set_refresh_cookies, unset_jwt_cookies
)  
from auth import checkTokensLifetime, checkCredentials, logout

import json
import os
import sys
sys.path.insert(0, 'classificator/docx')
import docx 

@app.route('/', methods=['GET', 'POST'])
@app.route('/upload/', methods=['GET', 'POST'])
@app.route('/upload', methods=['GET', 'POST'])
def index():
	current_user = checkCredentials()
	if current_user == None:
		return logout()

	if request.method == 'POST':
		file = request.files['file']
		if file:
			sample = Sample(filename=file.filename, status='Analyzed', owner=current_user)
			filename_saved = sample.saveFile(file)
			sample.is_anon = request.form.get('isAnon') == 'on'

			db.session.add(sample)
			db.session.commit()

			print 'predict?'
			docx.classifier.predict(filename_saved, sample)

			flash('File uploaded!')
	return render_template('index.html', title='Detectilka', username=current_user.username)


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
def user(username):
	current_user = checkCredentials()
	if current_user == None:
		return redirect(url_for('login'))

	if current_user.username != username:
		 render_template('404.html'), 404

	user = User.query.filter_by(username=username).first_or_404()
	samples_form = SamplesListForm()
	for sample in current_user.samples.all():
		entry_form = SampleEntryForm()
		entry_form.init(sample)
		samples_form.samples.append_entry(entry_form)

	return render_template('user.html', user=user, samples=samples_form.samples)


@app.route('/search', methods=['POST'])
def search():
	current_user = checkCredentials()
	if current_user == None:
		return redirect(url_for('login'))

	if request.method == 'POST':
		req = request.values['req']
		samples_form = SamplesListForm()
		for sample in Sample.query.filter(Sample.filename.contains(req) & Sample.is_anon == False).all():
			entry_form = SampleEntryForm()
			entry_form.init(sample)
			samples_form.samples.append_entry(entry_form)
		return render_template('search.html', req=req, samples=samples_form.samples)
	return render_template('search.html', req=req)


@app.route('/search_result', methods=['GET'])
def search_result():
	current_user = checkCredentials()
	if current_user == None:
		return redirect(url_for('login'))

	samples = parseSearchArgs(request.args)
	return render_template('samples.html', samples=samples)


def parseSearchArgs(args, api=None):
	query = { }
	for req in args:
		param = args[req].lower()
		query.update({req : param})

	if api == None:
		samples_form = SamplesListForm()
	else:
		samples = {}

	from datetime import datetime

	if 'hash' in query: h = Sample.hash == query['hash']
	else: h = Sample.hash.isnot(False)

	if 'filename' in query: f = Sample.filename.contains(query['filename'])
	else: f = Sample.filename.isnot(False)

	if 'answer' in query: a = Sample.answer.contains(query['answer'])
	else: a = Sample.answer.isnot(False)

	if 'time' in query: t = Sample.timestamp <= datetime.strptime(query['time'], '%Y-%m-%d')
	else: t = Sample.timestamp.isnot(False)

	anon = Sample.is_anon == False

	for sample in Sample.query.filter(h & f & a & t & anon).all():
		if api == None:
			entry_form = SampleEntryForm()
			entry_form.init(sample)	
			samples_form.samples.append_entry(entry_form)

		else:
			samples.update({sample.filename : {
				'answer' : sample.answer,
				'time'   : sample.timestamp,
				'status' : sample.status,
				'owner'  : sample.owner.username
				}})

	if api == None:
		return samples_form.samples
	else:
		return samples


@app.route('/report/<id>', methods=['GET'])
def report(id):
	current_user = checkCredentials()
	if current_user == None:
		return redirect(url_for('login'))

	sample = Sample.query.filter_by(id=id).first_or_404()

	entry_form = SampleEntryForm()
	entry_form.init(sample)
	
	samples_form = SamplesListForm()
	samples_form.samples.append_entry(entry_form)

	return render_template('report.html', samples=samples_form.samples)
