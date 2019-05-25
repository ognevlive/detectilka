from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, train_test_split, LeaveOneOut
from sklearn.feature_selection import chi2, mutual_info_classif, SelectKBest
from sklearn.preprocessing import LabelEncoder
from sklearn.exceptions import DataConversionWarning
from sklearn import metrics
from sklearn.metrics import roc_curve, auc
from datetime import datetime
import numpy as np
import pandas
import createCSV

import exiftool
import xml.etree.ElementTree as ET
import zipfile as zf


class Classifier:
	def __init__(self, dataset_file):
		self.dataset = pandas.read_csv(dataset_file)
		self.dataset = self.dataset.fillna(0)
		self.dataset = self.dataset.sample(frac=1)

		self.targets = None
		self.features = None
		self.features2 = None
		self.targetName = 'Malicious'
		self.columnsToDrop = ['Unnamed: 0','MD5','Malicious']


	def getXandY(self):
		self.targets = self.dataset[self.targetName]
		self.features = self.dataset.drop(self.columnsToDrop, axis=1)
		self.features2 = self.dataset.drop(self.columnsToDrop, axis=1)
		convertedFeatures = self.features
		convertedFeatures2 = self.features
		for column in self.features.columns:
			columnData = self.features[column]
			if columnData.dtype == type(object):
				le = LabelEncoder()
				columnData = columnData.factorize()[0]
				convertedFeatures[column] = le.fit_transform(columnData)
				convertedFeatures2[column] = columnData
		self.features = convertedFeatures
		self.features2 = convertedFeatures2
		self.features[self.features < 0] = 0


	def getResults(self, real_malicious, predict_malicious):
		confusionMatrix = metrics.confusion_matrix(real_malicious, predict_malicious)
		tp, fp, fn, tn = confusionMatrix.ravel()
		positives = tp + fp
		negatives = fn + tn
		tp = tp / positives
		fp = fp / positives
		fn = fn / negatives
		tn = tn / negatives
		precision = metrics.precision_score(real_malicious, predict_malicious)
		recall = metrics.recall_score(real_malicious, predict_malicious)
		f1 = metrics.f1_score(real_malicious, predict_malicious)
		return (tp, fp, fn, tn, precision, recall, f1)

model = RandomForestClassifier(n_estimators=500, min_samples_leaf = 2, random_state=1)  

import sys
sys.path.insert(0, '../../app')
from app import db
from app.models import Sample

root_path = 'classificator/docx/'

def train():
	print ('training docx classifier...')
	database = root_path + 'database.csv'
	good_files = root_path + 'good/'
	bad_files  = root_path + 'bad/'

	# createCSV.run(good_files, bad_files, database)

	cl = Classifier(database)
	cl.getXandY()
				  
	model.fit(cl.features, cl.targets)  
	print ('finish')

def predict(file, sample):
	database = root_path + 'temp.csv'
	if createCSV.run_file(file, database) == 0:
		cl = Classifier(database)
		cl.getXandY()

		with exiftool.ExifTool() as et:
			metadata = et.get_metadata('uploads/' + file)

		print metadata


		sample.filesize =  metadata['File:FileSize']
		sample.words    =  metadata['XML:Words']
		sample.pages    =  metadata['XML:Pages']
		sample.characters     =  metadata['XML:Characters']
		sample.totaledittime  =  metadata['XML:TotalEditTime']
		sample.revisionnumber =  metadata['XML:RevisionNumber']

		sample.title = metadata['XMP:Title']
		sample.creator = metadata['XMP:Creator']
		sample.company = metadata['XML:Company']

		sample.lastprinted = metadata['XML:LastPrinted']
		sample.createdate  = metadata['XML:CreateDate']
		sample.lastmodifiedby = metadata['XML:LastModifiedBy']

		# sample.lastprinted = datetime.strptime(str(cl.features2['LastPrinted'].data), '%b %d %Y %H:%M:%S')
		# sample.createdate  = datetime.strptime(str(cl.features2['CreateDate'].data), '%b %d %Y %H:%M:%S')
		# sample.lastmodifiedby = datetime.strptime(str(cl.features2['LastModifiedBy'].data), '%b %d %Y %H:%M:%S')

		y_pred = int(model.predict(cl.features))

		if y_pred == 1: sample.answer = 'Malware'
		else:			sample.answer = 'Safe'
	else:
		sample.answer = 'Invalid file'
	
	sample.status = 'Checked'

