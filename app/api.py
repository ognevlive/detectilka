from flask import jsonify, request, flash
from werkzeug.utils import secure_filename
from app import app, db
from app.models import User, Sample
from datetime import datetime
from hashlib import md5
import os
import sys
sys.path.insert(0, 'classificator/docx')
import docx 

@app.route('/api/upload', methods=["POST"])
def api_upload():

	if request.files == None:
		return jsonify({'message' : 'invalid params'}), 200

	file = request.files['file']
	filename = file.filename
	filename_secure = secure_filename(filename)
	filename_saved  = '%s__%s' % (filename_secure, str(datetime.utcnow()))

	file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename_saved))

	# add owner / api key
	sample = Sample(filename=filename)
	sample.hash = md5(open('uploads/' + filename_saved,'rb').read()).hexdigest()

	db.session.add(sample)
	db.session.commit()

	docx.classifier.predict(filename_saved, sample)

	repsonse = { 
		'filename' : sample.filename, 
		'hash' : sample.hash,
		'id' : sample.id, 
		'status' : sample.status,
		'url' : request.url_root + 'report/' + str(sample.id)
	}

	return jsonify(repsonse), 200


@app.route('/api/report/<id>', methods=["GET"])
def api_report(id):

	if id == None:
		return jsonify({'message' : 'invalid params'}), 200

	sample = Sample.query.filter_by(id=id).first_or_404()

	repsonse = { 
		'filename' : sample.filename, 
		'hash' : sample.hash,
		'id' : sample.id, 
		'status' : sample.status,
		'owner' : sample.owner.username,
		'time' : sample.timestamp,
	}

	return jsonify(repsonse), 200