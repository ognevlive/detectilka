from flask import render_template, flash, redirect, url_for, request, jsonify, make_response
from app import app, db, jwt
from app.models import User
from app.forms import LoginForm, RegistrationForm
from datetime import datetime
from flask_jwt_extended import (
	JWTManager, jwt_required, create_access_token,
	jwt_refresh_token_required, create_refresh_token,
	get_jwt_identity, set_access_cookies,
	set_refresh_cookies, unset_jwt_cookies, decode_token
)  

def invalidResp(msg):
	invalid_resp = {
		'status': 'fail',
		'message': msg
	}
	return jsonify(invalid_resp)


def checkTokensLifetime():
	access_token = request.cookies['access_token_cookie']
	refresh_token = request.cookies['refresh_token_cookie']

	raw_refresh_token = decode_token(refresh_token, allow_expired=True)
	exp_time = datetime.utcfromtimestamp(raw_refresh_token['exp'])#.strftime('%Y-%m-%d %H:%M:%S')
	if exp_time < datetime.utcnow():
		resp, status = auth_logout(current_user.username, resp)
		if status == 201:
			return resp, 201
		else:
			return redirect(url_for('login'))

	raw_access_token = decode_token(access_token, allow_expired=True)
	exp_time = datetime.utcfromtimestamp(raw_access_token['exp'])#.strftime('%Y-%m-%d %H:%M:%S')
	if exp_time < datetime.utcnow():
		resp = make_response(redirect(request.path))
		resp, status = auth_refresh(current_user.username, resp)
		if status == 201:
			return resp, 201
		else:
			return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
	access_token = request.cookies['access_token_cookie']
	current_user = User.query.filter_by(access_token=access_token).first()
	if current_user != None:
		return redirect(url_for('index'))

	form = LoginForm()
	if request.method == 'POST':
		resp = make_response(redirect(url_for('index')))
		resp, status = auth_login(form.username.data, form.password.data, resp)
		if status == 201:
			return resp, 201
		else:
			flash('invalid credentials')
			return redirect(url_for('login'))
	else:
		return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
	access_token = request.cookies['access_token_cookie']
	current_user = User.query.filter_by(access_token=access_token).first()
	if current_user == None:
		return redirect(url_for('login'))

	resp = make_response(redirect(url_for('login')))
	resp, status = auth_logout(current_user.username, resp)
	if status == 201:
		return resp, 201
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


@app.route('/auth_register', methods=['POST'])
def auth_register(username, email, password):
	exists = db.session.query(User.id).filter_by(username=username).scalar() is not None or \
			 db.session.query(User.id).filter_by(email=email).scalar() is not None
	if exists:
		return invalidResp('invalid params'), 409

	user = User(username=username, email=email)
	user.set_password(password)

	access_token = create_access_token(identity = username)
	refresh_token = create_refresh_token(identity = username)

	user.access_token = access_token
	user.refresh_token = refresh_token

	db.session.add(user)
	db.session.commit()

	resp = {
		'status': 'success',
		'message': 'Successfully registered.',
		'access_token': access_token, 
		'refresh_token': refresh_token
	}
	return jsonify(resp), 201


@app.route('/auth_login', methods=['POST'])
def auth_login(username, password, resp=None):
	user = User.query.filter_by(username=username).first()
	if user is None or not user.check_password(password):
		if resp == None: return invalidResp('invalid credentials'), 409
		else:            return resp, 401

	access_token = create_access_token(identity=username)
	refresh_token = create_refresh_token(identity=username)

	user.access_token = access_token
	user.refresh_token = refresh_token

	db.session.commit()

	if resp == None:
		resp = jsonify({
			'status': 'success',
			'message': 'Login was successful',
			'access_token': access_token, 
			'refresh_token': refresh_token
		})

	set_access_cookies(resp, access_token)
	set_refresh_cookies(resp, refresh_token)
	return resp, 201


@app.route('/auth_logout', methods=['POST'])
def auth_logout(username, resp=None):
	current_user = User.query.filter_by(username=username).first()
	if current_user is None:
		if resp == None: return invalidResp('invalid credentials'), 409
		else:            return resp, 401

	current_user.refresh_token = ''
	current_user.access_token  = ''
	db.session.commit()

	if resp == None:
		resp = jsonify({
			'status': 'success',
			'message': 'Logout was successful'
		})

	unset_jwt_cookies(resp)

	return resp, 201


@app.route('/auth_refresh', methods=['POST'])
def auth_refresh(username, resp=None):
	current_user = User.query.filter_by(username=username).first()
	if current_user is None:
		if resp == None: return invalidResp('invalid credentials'), 409
		else:            return resp, 401

	access_token = create_access_token(identity=username)

	current_user.access_token = access_token
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