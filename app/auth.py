from flask import render_template, flash, redirect, url_for, request, jsonify, make_response
from app import app, db, jwt
from app.models import User, PrivateInfo
from app.forms import LoginForm, RegistrationForm
from app.routes import verifyCredentials, invalidResp
from datetime import datetime
from flask_jwt_extended import (
	JWTManager, jwt_required, create_access_token,
	jwt_refresh_token_required, create_refresh_token,
	get_jwt_identity, set_access_cookies,
	set_refresh_cookies, unset_jwt_cookies, decode_token, get_csrf_token
)  


@app.route('/login', methods=['GET', 'POST'])
def login():
	form = LoginForm()
	if request.method == 'POST':
		resp = make_response(redirect(url_for('index'), code=302))
		resp, status = auth_login(form.username.data, form.password.data, resp)

		if status == 201:
			return resp, 302
		else:
			flash('invalid credentials')
			return redirect(url_for('logout'), code=302)
	else:
		return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
	try:
		current_user = User.query.filter_by(access_token=request.cookies['access_token_cookie']).first()
		if current_user == None:
			return redirect(url_for('login'))
	except:
		return redirect(url_for('login'))

	resp = make_response(redirect(url_for('login'), code=302))
	resp, status = auth_logout(current_user.username, resp)
	if status == 201:
		return resp, 302
	else:
		return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegistrationForm()
	if form.validate_on_submit():
		data, status = auth_register(form.username.data, form.email.data, form.password.data)
		if status == 201:
			flash('Congratulations, you are now a registered user!')
			return redirect(url_for('login'))
	return render_template('register.html', title='Register', form=form)


def auth_register(username, email, password):
	exists = db.session.query(User.id).filter_by(username=username).scalar() is not None or \
			 db.session.query(User.id).filter_by(email=email).scalar() is not None
	if exists:
		return invalidResp('invalid params'), 409

	user = User(username=username, email=email)
	user.set_password(password)

	db.session.add(user)
	db.session.commit()

	resp = {
		'status': 'success',
		'message': 'Successfully registered.'
	}
	return jsonify(resp), 201


def auth_login(username, password, resp=None):
	user = User.query.filter_by(username=username).first()
	if user is None or not user.check_password(password):
		if resp == None: return invalidResp('invalid credentials'), 409
		else:            return resp, 401

	access_token = create_access_token(identity=username)
	refresh_token = create_refresh_token(identity=username)

	user.access_token = access_token
	user.csrf_access_token = get_csrf_token(access_token)

	PrivateInfo.query.filter_by(owner=user).delete()

	ua = request.user_agent

	try:
		platform = ua.platform
	except:
		platform = 'Unknown'

	try:
		browser = ua.browser
	except:
		browser = 'Unknown'

	try:
		language = request.accept_languages[0][0]
	except:
		language = 'Unknown'

	info = PrivateInfo(access_token=access_token, refresh_token=refresh_token, owner=user, platform=platform, browser=browser, language=language)

	db.session.commit()

	if resp == None:
		resp = jsonify({
			'status': 'success',
			'message': 'Login was successful',
			'refresh_token': refresh_token,
			'access_token': access_token
		})

	set_access_cookies(resp, access_token)
	set_refresh_cookies(resp, refresh_token)
	return resp, 201


def auth_logout(username, resp=None):
	current_user = User.query.filter_by(username=username).first()
	if current_user is None:
		if resp == None: return invalidResp('invalid credentials'), 409
		else:            return resp, 401

	# refresh_token = request.cookies['refresh_token_cookie']
	# info = PrivateInfo.query.filter_by(refresh_token=refresh_token).first()
	# if current_user != info.owner:
	# 	if resp == None: return invalidResp('invalid credentials'), 409
	# 	else:            return resp, 401

	PrivateInfo.query.filter_by(access_token=request.cookies['access_token_cookie']).delete()
	
	current_user.access_token = ''
	db.session.commit()

	if resp == None:
		resp = jsonify({
			'status': 'success',
			'message': 'Logout was successful'
		})

	unset_jwt_cookies(resp)

	return resp, 201


#@app.route('/auth_refresh', methods=['POST'])
def auth_refresh(username, resp=None):
	current_user = User.query.filter_by(username=username).first()
	if current_user is None:
		if resp == None: return invalidResp('invalid credentials'), 409
		else:            return resp, 401

	access_token = create_access_token(identity=username)

	current_user.access_token = access_token
	current_user.csrf_access_token = get_csrf_token(access_token)
	db.session.commit()

	if resp == None:
		if resp == None:
			resp = jsonify({
				'status': 'success',
				'message': 'Successfully refreshed',
				'access_token': access_token
			})

	set_access_cookies(resp, access_token)

	return resp, 200