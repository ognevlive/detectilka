from sklearn.neighbors import KNeighborsClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import StratifiedKFold, train_test_split, LeaveOneOut
from sklearn.feature_selection import chi2, mutual_info_classif, SelectKBest
from sklearn.preprocessing import LabelEncoder
from sklearn.exceptions import DataConversionWarning
from sklearn import metrics
from sklearn.metrics import roc_curve, auc
import numpy as np
import pandas
import createCSV
import hashlib


class Classifier:
	def __init__(self, dataset_file):
		self.dataset = pandas.read_csv(dataset_file)
		self.dataset = self.dataset.fillna(0)
		self.dataset = self.dataset.sample(frac=1)

		self.targets = None
		self.features = None
		self.targetName = 'Malicious'
		self.columnsToDrop = ['Unnamed: 0','MD5','Malicious']


	def getXandY(self):
		self.targets = self.dataset[self.targetName]
		self.features = self.dataset.drop(self.columnsToDrop, axis=1)
		convertedFeatures = self.features
		for column in self.features.columns:
			columnData = self.features[column]
			if columnData.dtype == type(object):
				le = LabelEncoder()
				columnData = columnData.factorize()[0]
				convertedFeatures[column] = le.fit_transform(columnData)
		self.features = convertedFeatures
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
	createCSV.run_file(file, database)
	cl = Classifier(database)
	cl.getXandY()
  	y_pred = int(model.predict(cl.features))

  	if y_pred == 1:
  		sample.answer = 'Malware'
  	else:
  		sample.answer = 'Safe'

  	sample.hash = hashlib.md5(open('uploads/' + file,'rb').read()).hexdigest()

  	db.session.commit()