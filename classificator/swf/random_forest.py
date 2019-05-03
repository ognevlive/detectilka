from sklearn.model_selection import train_test_split
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten
from sklearn.ensemble import RandomForestClassifier
from keras.callbacks import ModelCheckpoint
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestRegressor
from sklearn import metrics
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score, recall_score, precision_score
from sklearn.feature_selection import chi2, mutual_info_classif , SelectKBest
from sklearn.model_selection import StratifiedKFold 
from sklearn.metrics import roc_curve, auc, roc_auc_score
from sklearn.model_selection import LeaveOneOut


from pprint import pprint

def readCSV(name):
  dataset =pd.read_csv(name)
  dataset = dataset.sample(frac=1)
  y = dataset['isBad'].to_frame()
 # X = dataset.drop(['isBad', 'file_name', 'hash', 'iter'], axis = 1)
  X = dataset.drop(['isBad'], axis = 1)

  return X,y 

def selection(X, algorithm, N = 'all'):
  print ('[%s] N = %s' % (algorithm.__name__, str(N)))
  selector = SelectKBest(algorithm, k=N)

  selector.fit(X, y)

  X_new = selector.transform(X)

  attrs = list(X.columns[selector.get_support(indices=True)])

  return X_new, attrs

def crossValidation(X, y, N=3):
  from sklearn.model_selection import cross_val_score, cross_val_predict
  regressor = RandomForestClassifier(min_samples_leaf = 2, random_state=17,  criterion = 'entropy')
  from sklearn.metrics import fbeta_score, make_scorer
  y_pred = cross_val_predict(regressor, X, y, cv=N)

  tn, fp, fn, tp = confusion_matrix(y.values, y_pred).ravel()
  total = tn + fp + fn + tp

  f1 = cross_val_score(regressor, X, y, cv=N, scoring='f1').mean()
  accuracy = cross_val_score(regressor, X, y, cv=N, scoring='accuracy').mean()
  precision = cross_val_score(regressor, X, y, cv=N, scoring='precision').mean()
  recall = cross_val_score(regressor, X, y, cv=N, scoring='recall').mean()
  
  print ('[cross-validation: %d] average f1     = %f (+- %f)'   % (N, f1.mean(), f1.std()))
  print ('[cross-validation: %d] average acc    = %f (+- %f)\n' % (N, accuracy.mean(), accuracy.std()))
  print ('[cross-validation: %d] average precision = %f (+- %f)'   % (N, precision.mean(), precision.std()))
  print ('[cross-validation: %d] average    recall = %f (+- %f)\n' % (N, recall.mean(), recall.std()))

  print ('[cross-validation: %d]  true positive = %f' % (N, float(tp) / total * 100))
  print ('[cross-validation: %d]  true negative = %f' % (N, float(tn) / total * 100))
  print ('[cross-validation: %d] false positive = %f' % (N, float(fp) / total * 100))
  print ('[cross-validation: %d] false negative = %f' % (N, float(fn) / total * 100))



if __name__ == '__main__':

  import warnings
  warnings.filterwarnings("ignore", category=FutureWarning)
  warnings.filterwarnings("ignore", category=DeprecationWarning)

  X, y = readCSV('total4.csv')

  train_X, test_X, train_y, test_y = train_test_split(X, y, test_size=0.25, random_state=17)
                  
  regressor = RandomForestClassifier(min_samples_leaf = 2, random_state=17,  criterion = 'entropy')  
  regressor.fit(train_X, train_y)  
  y_pred = regressor.predict(test_X) 


  print ('accuracy = %f' % accuracy_score(test_y, y_pred))  
  print ('f1 = %f' % metrics.f1_score(test_y, y_pred))

  print ('f1     = %f '   % f1_score(test_y, y_pred))
  print ('acc    = %f \n' % accuracy_score(test_y, y_pred))

  print ('precision = %f '   % precision_score(test_y, y_pred))
  print ('   recall = %f \n' % recall_score(test_y, y_pred))
  
  tn, fp, fn, tp = confusion_matrix(test_y, y_pred).ravel()
  print (' true positive = %f' % tp)
  print (' true negative = %f' % tn)
  print ('false positive = %f' % fp)
  print ('false negative = %f' % fn)

  
  paintAUC_ROC(test_y, y_pred)