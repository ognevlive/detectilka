from flask import jsonify, request, flash
from werkzeug.utils import secure_filename
from app import app, db
from app.models import User, Sample
from datetime import datetime
from hashlib import md5
import os
import json

import sys
sys.path.insert(0, 'classificator/docx')
import docx 
from app.auth import auth_register, auth_login, auth_logout, auth_refresh, checkCredentials

def invalidResp(msg):
	invalid_resp = {
		'status': 'fail',
		'message': msg
	}
	return jsonify(invalid_resp)


#curl -v -F 'file=@testfiile3.doc' http://localhost:5000/api/upload --cookie "access_token_cookie=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJqdGkiOiI2N2RiZDFiMi1iNzVhLTRmNWYtODAwYS1lNzAzYmUzYTViMWMiLCJleHAiOjE1NTc1ODE2NDgsImZyZXNoIjpmYWxzZSwiaWF0IjoxNTU3NTgwNzQ4LCJ0eXBlIjoiYWNjZXNzIiwibmJmIjoxNTU3NTgwNzQ4LCJpZGVudGl0eSI6IkpvaG55In0.kxkWZ3rgk67NQliPwomBcoc6hsYOwftaBJQ6m0Bxb4w"
@app.route('/api/upload', methods=["POST"])
def api_upload():
	current_user = checkCredentials()
	if current_user == None:
		return invalidResp('bad credentials'), 404

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
	sample = Sample.query.filter_by(id=id).first()
	if sample == None:
		return invalidResp('invalid params'), 404

	user = sample.owner
	access_token = request.cookies['access_token_cookie']
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
	refresh_token = request.cookies['refresh_token_cookie']
	current_user = PrivateInfo.query.filter_by(refresh_token=refresh_token).first().owner()
	if current_user == None:
		return invalidResp('bad credentials'), 404

	return auth_refresh(current_user.username)


@app.route('/api/logout', methods=["POST"])
def api_logout():
	refresh_token = request.cookies['refresh_token_cookie']
	current_user = PrivateInfo.query.filter_by(refresh_token=refresh_token).first().owner()
	if current_user == None:
		return invalidResp('bad credentials'), 404

	return auth_logout(current_user.username)