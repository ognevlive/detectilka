from flask import jsonify, request, flash
from werkzeug.utils import secure_filename
from app import app, db
from app.models import User, Sample, PrivateInfo
from app.routes import parseSearchArgs, verifyCredentials
from datetime import datetime
from hashlib import md5
import os
import json

import sys
sys.path.insert(0, 'classificator/docx')
import docx 
from app.auth import auth_register, auth_login, auth_logout, auth_refresh

def invalidResp(msg):
	invalid_resp = {
		'status': 'fail',
		'message': msg
	}
	return jsonify(invalid_resp)

def refresh_foo():
	return invalidResp('bad credentials')


#curl -v -F 'file=@testfiile3.doc' http://localhost:5000/api/upload --cookie "access_token_cookie=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI2N2RiZDFiMi1iNzVhLTRmNWYtODAwYS1lNzAzYmUzYTViMWMiLCJleHAiOjE1NTc1ODE2NDgsImZyZXNoIjpmYWxzZSwiaWF0IjoxNTU3NTgwNzQ4LCJ0eXBlIjoiYWNjZXNzIiwibmJmIjoxNTU3NTgwNzQ4LCJpZGVudGl0eSI6IkpvaG55In0.kxkWZ3rgk67NQliPwomBcoc6hsYOwftaBJQ6m0Bxb4w"
@app.route('/api/upload', methods=["POST"])
def api_upload():
	status = verifyCredentials(refresh_foo)
	if status != True:
		return status, 404

	current_user = User.query.filter_by(access_token=request.cookies['access_token_cookie']).first()

	if request.files == None:
		return invalidResp('bad file'), 404

	sample = Sample(filename=request.files['file'].filename, status='Analyzed', owner=current_user)
	filename_saved = sample.saveFile(request.files['file'])
	sample.is_anon = False

	docx.classifier.predict(filename_saved, sample)

	db.session.add(sample)
	db.session.commit()

	repsonse = { 
		'filename' : sample.filename, 
		'hash' : sample.hash,
		'id' : sample.id, 
		'status' : sample.status,
		'url' : request.url_root + 'report/' + str(sample.id), 
		'owner' : sample.owner.username
	}

	return jsonify(repsonse), 200


@app.route('/api/report/<id>', methods=["GET"])
def api_report(id):
	status = verifyCredentials(refresh_foo)
	if status != True:
		return status, 404

	access_token = request.cookies['access_token_cookie']
	current_user = User.query.filter_by(access_token=access_token).first()

	sample = Sample.query.filter_by(id=id).first()
	if sample == None:
		return invalidResp('invalid params'), 404

	user = sample.owner
	if user.access_token != access_token:
		return invalidResp('access denied'), 404

	repsonse = { 
		'filename' : sample.filename, 
		'hash' : sample.hash,
		'id' : sample.id, 
		'status' : sample.status,
		'owner' : sample.owner.username,
		'time' : sample.timestamp,
		'answer' : sample.answer,
	}

	return jsonify(repsonse), 200


@app.route('/api/register', methods=["POST"])
def api_register():
	username = request.json['username']
	password = request.json['password']
	email = request.json['email']
	return auth_register(username, email, password)


@app.route('/api/login', methods=["POST"])
def api_login():
	username = request.json['username']
	password = request.json['password']
	return auth_login(username, password)


@app.route('/api/refresh', methods=["POST"])
def api_refresh():
	try:
		refresh_token = request.cookies['refresh_token_cookie']
	except KeyError:
		return invalidResp('invalid credentials'), 409
		
	info = Info.query.filter_by(refresh_token=refresh_token)
	if info == None:
		return invalidResp('invalid credentials'), 409

	current_user = info.owner

	access_token = create_access_token(identity=current_user.username)
	current_user.access_token = access_token
	db.session.commit()

	resp = jsonify({
			'status': 'success',
			'message': 'Refresh was successful'
		})

	set_access_cookies(resp, access_token)

	return resp, 200
	

@app.route('/api/logout', methods=["POST"])
def api_logout():
	status = verifyCredentials(refresh_foo)
	if status != True:
		return status, 404

	user = User.query.filter_by(access_token=request.cookies['access_token_cookie']).first()

	return auth_logout(user.username)


@app.route('/api/reports', methods=["GET"])
def api_reports():
	status = verifyCredentials(refresh_foo)
	if status != True:
		return status, 404

	user = User.query.filter_by(access_token=request.cookies['access_token_cookie']).first()

	reports = { }
	for sample in user.samples.all():
			reports.update({str(sample.id) : {'name' : sample.filename, 'answer' : sample.answer}})
	return jsonify(reports), 200


@app.route('/api/search', methods=["POST"])
def api_search():
	status = verifyCredentials(refresh_foo)
	if status != True:
		return status, 404

	samples = parseSearchArgs(request.json, True)

	return jsonify(samples), 200
