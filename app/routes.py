from flask import render_template, flash, redirect, url_for, request, jsonify, make_response
#from flask_login import current_user, login_user, logout_user, login_required
from app import app, db, jwt
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
	set_refresh_cookies, unset_jwt_cookies, decode_token, get_csrf_token
)  

import json
import os
import sys
sys.path.insert(0, 'classificator/docx')
import docx 


def invalidResp(msg):
	invalid_resp = {
		'status': 'fail',
		'message': msg
	}
	return jsonify(invalid_resp)

def refreshFoo1():
	return redirect(url_for('refresh', next=request.endpoint))

def verifyCredentials(refresh=refreshFoo1):
	try:
		access_token = request.cookies['access_token_cookie']
	except KeyError:
		return refresh()
		
	raw_access_token = decode_token(access_token, allow_expired=True)
	exp_time = datetime.utcfromtimestamp(raw_access_token['exp'])
	if exp_time < datetime.utcnow():
		return refresh()

	try:
		ua = request.user_agent
		pi = PrivateInfo.query.filter_by(access_token=access_token).first()
		print pi
		if pi == None:
			return refresh()
		if pi.platform != ua.platform or \
		   pi.browser  != ua.browser  or \
		   pi.language != request.accept_languages[0][0]:
			return refresh()
		
	except:
		return refresh()

	return True

@app.route('/', methods=['GET', 'POST'])
@app.route('/upload/', methods=['GET', 'POST'])
@app.route('/upload', methods=['GET', 'POST'])
def index():
	status = verifyCredentials()
	if status != True:
		return status

	current_user = User.query.filter_by(access_token=request.cookies['access_token_cookie']).first()

	if request.method == 'POST':

		if current_user.csrf_access_token != request.values.get('csrf_access_token'):
			print 'csrf error!'
			return redirect(url_for('logout'))
		file = request.files['file']
		if file:
			sample = Sample(filename=file.filename, status='Analyzed', owner=current_user)
			filename_saved = sample.saveFile(file)
			sample.is_anon = request.form.get('isAnon') == 'on'

			old_sample = Sample.query.filter((Sample.hash == sample.hash )& (Sample.answer != None)).first()
			if old_sample != None:
				sample.status = 'Checked'
				sample.answer = old_sample.answer
			else:
				docx.classifier.predict(filename_saved, sample)

			db.session.add(sample)
			db.session.commit()


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
	status = verifyCredentials()
	print status
	if status != True:
		return status
	
	current_user = User.query.filter_by(access_token=request.cookies['access_token_cookie']).first()

	if current_user.username != username:
		 render_template('404.html'), 404

	samples_form = SamplesListForm()
	for sample in current_user.samples.all():
		entry_form = SampleEntryForm()
		entry_form.init(sample)
		samples_form.samples.append_entry(entry_form)

	return render_template('user.html', user=current_user, samples=samples_form.samples)


@app.route('/search', methods=['POST'])
def search():
	status = verifyCredentials()
	if status != True:
		return status
	
	current_user = User.query.filter_by(access_token=request.cookies['access_token_cookie']).first()

	if current_user.csrf_access_token != request.values.get('csrf_access_token'):
		return redirect(url_for('logout'))

	req = request.values['req']
	samples_form = SamplesListForm()
	for sample in Sample.query.filter(Sample.filename.contains(req) & (Sample.is_anon == False)).all():
		entry_form = SampleEntryForm()
		entry_form.init(sample)
		samples_form.samples.append_entry(entry_form)
	return render_template('search.html', req=req, samples=samples_form.samples)


@app.route('/search_result', methods=['GET'])
def search_result():
	status = verifyCredentials()
	if status != True:
		return status
	
	current_user = User.query.filter_by(access_token=request.cookies['access_token_cookie']).first()

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
	status = verifyCredentials()
	if status != True:
		return status
	
	current_user = User.query.filter_by(access_token=request.cookies['access_token_cookie']).first()

	sample = Sample.query.filter_by(id=id).first_or_404()

	entry_form = SampleEntryForm()
	entry_form.init(sample)
	
	samples_form = SamplesListForm()
	samples_form.samples.append_entry(entry_form)

	return render_template('report.html', samples=samples_form.samples)


@app.route('/refresh', methods=['GET'])
def refresh(api=False):
	try:
		refresh_token = request.cookies['refresh_token_cookie']
	except KeyError:
		if not api: return redirect(url_for('logout'))
		else:		return invalidResp('invalid credentials'), 409
		
	info = PrivateInfo.query.filter_by(refresh_token=refresh_token).first()
	if info == None:
		if not api: return redirect(url_for('logout'))
		else:		return invalidResp('invalid credentials'), 409

	current_user = info.owner

	access_token = create_access_token(identity=current_user.username)
	current_user.access_token = access_token
	current_user.csrf_access_token = get_csrf_token(access_token)
	db.session.commit()

	resp = jsonify({
			'status': 'success',
			'message': 'Refresh was successful'
		})

	set_access_cookies(resp, access_token)

	if not api: return redirect(url_for(request.args.get('next')))
	else:		return invalidResp('invalid credentials'), 409
