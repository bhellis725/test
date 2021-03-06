
# coding: utf-8

# # Table of Contents
#  <p><div class="lev1 toc-item"><a href="#Ground-predictions" data-toc-modified-id="Ground-predictions-1"><span class="toc-item-num">1&nbsp;&nbsp;</span>Ground predictions</a></div><div class="lev2 toc-item"><a href="#PVLib-Clearsky" data-toc-modified-id="PVLib-Clearsky-11"><span class="toc-item-num">1.1&nbsp;&nbsp;</span>PVLib Clearsky</a></div><div class="lev1 toc-item"><a href="#Train/test-on-NSRDB-data-to-find-optimal-parameters" data-toc-modified-id="Train/test-on-NSRDB-data-to-find-optimal-parameters-2"><span class="toc-item-num">2&nbsp;&nbsp;</span>Train/test on NSRDB data to find optimal parameters</a></div><div class="lev1 toc-item"><a href="#Train-on-all-NSRDB-data,-test-various-freq-of-ground-data" data-toc-modified-id="Train-on-all-NSRDB-data,-test-various-freq-of-ground-data-3"><span class="toc-item-num">3&nbsp;&nbsp;</span>Train on all NSRDB data, test various freq of ground data</a></div><div class="lev2 toc-item"><a href="#30-min-freq-ground-data" data-toc-modified-id="30-min-freq-ground-data-31"><span class="toc-item-num">3.1&nbsp;&nbsp;</span>30 min freq ground data</a></div><div class="lev2 toc-item"><a href="#15-min-freq-ground-data" data-toc-modified-id="15-min-freq-ground-data-32"><span class="toc-item-num">3.2&nbsp;&nbsp;</span>15 min freq ground data</a></div><div class="lev2 toc-item"><a href="#10-min-freq-ground-data" data-toc-modified-id="10-min-freq-ground-data-33"><span class="toc-item-num">3.3&nbsp;&nbsp;</span>10 min freq ground data</a></div><div class="lev2 toc-item"><a href="#5-min-freq-ground-data" data-toc-modified-id="5-min-freq-ground-data-34"><span class="toc-item-num">3.4&nbsp;&nbsp;</span>5 min freq ground data</a></div><div class="lev2 toc-item"><a href="#1-min-freq-ground-data" data-toc-modified-id="1-min-freq-ground-data-35"><span class="toc-item-num">3.5&nbsp;&nbsp;</span>1 min freq ground data</a></div><div class="lev1 toc-item"><a href="#Save-model" data-toc-modified-id="Save-model-4"><span class="toc-item-num">4&nbsp;&nbsp;</span>Save model</a></div><div class="lev1 toc-item"><a href="#Conclusion" data-toc-modified-id="Conclusion-5"><span class="toc-item-num">5&nbsp;&nbsp;</span>Conclusion</a></div>

# In[284]:


import pandas as pd
import numpy as np
import os
import datetime
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from sklearn import tree

import pytz
import itertools
import visualize
import utils
import pydotplus
import xgboost as xgb

from sklearn import metrics
from sklearn import model_selection

import pvlib
import cs_detection

import visualize_plotly as visualize
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.graph_objs as go
init_notebook_mode(connected=True)

from IPython.display import Image

get_ipython().magic('load_ext autoreload')
get_ipython().magic('autoreload 2')

np.set_printoptions(precision=4)
get_ipython().magic('matplotlib notebook')


# # Ground predictions

# ## PVLib Clearsky

# Only making ground predictions using PVLib clearsky model and statistical model.  NSRDB model won't be available to ground measurements.

# In[285]:


nsrdb = cs_detection.ClearskyDetection.read_pickle('abq_nsrdb_1.pkl.gz')
nsrdb.df.index = nsrdb.df.index.tz_convert('MST')

nsrdb.trim_dates('01-01-2014', '01-01-2016')
# In[286]:


nsrdb.time_from_solar_noon('Clearsky GHI pvlib', 'tfn')


# In[287]:


ground = cs_detection.ClearskyDetection.read_pickle('abq_ground_1.pkl.gz')
ground.df.index = ground.df.index.tz_convert('MST')


# In[288]:


feature_cols = [
'tfn',
'abs_ideal_ratio_diff',
'abs_ideal_ratio_diff mean',
'abs_ideal_ratio_diff std',
'GHI Clearsky GHI pvlib gradient ratio', 
'GHI Clearsky GHI pvlib gradient ratio mean', 
'GHI Clearsky GHI pvlib gradient ratio std', 
'GHI Clearsky GHI pvlib gradient second ratio', 
'GHI Clearsky GHI pvlib gradient second ratio mean', 
'GHI Clearsky GHI pvlib gradient second ratio std', 
'GHI Clearsky GHI pvlib line length ratio',
'GHI Clearsky GHI pvlib line length ratio gradient',
'GHI Clearsky GHI pvlib line length ratio gradient second'
]

target_cols = ['sky_status']


# # Train/test on NSRDB data to find optimal parameters

# In[327]:


train = cs_detection.ClearskyDetection(nsrdb.df)
train.trim_dates('01-01-2010', '06-01-2015')
test = cs_detection.ClearskyDetection(nsrdb.df)
test.trim_dates('06-01-2015', None)


# In[328]:


train.scale_model('GHI', 'Clearsky GHI pvlib', 'sky_status')


# In[329]:


utils.calc_all_window_metrics(train.df, 3, meas_col='GHI', model_col='Clearsky GHI pvlib', overwrite=True)


# In[332]:


vis = visualize.Visualizer()
vis.plot_corr_matrix(train.df[feature_cols].corr().values, labels=feature_cols)


# In[333]:


param_grid = {'max_depth': [3, 4], 'n_estimators': [200, 400], 'learning_rate': [.1, .01]}


# In[334]:


import itertools
import warnings
best_score = 0
best_params = {}
with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    for depth, n_est, lr in itertools.product(param_grid['max_depth'], param_grid['n_estimators'], param_grid['learning_rate']):
        clf = xgb.XGBClassifier(max_depth=depth, n_estimators=n_est, learning_rate=lr, n_jobs=4)
        clf.fit(train.df[feature_cols].values, train.df[target_cols].values.flatten())
        test = cs_detection.ClearskyDetection(nsrdb.df)
        test.trim_dates('06-01-2015', None)    
        pred = test.iter_predict_daily(feature_cols, 'GHI', 'Clearsky GHI pvlib', clf, 3, multiproc=False)
        score = metrics.f1_score(test.df['sky_status'], pred)
        # score = metrics.precision_score(test.df['sky_status'], pred)
        indicator = ''
        if score > best_score:
            best_score = score
            best_params['max_depth'] = depth
            best_params['n_estimators'] = n_est
            best_params['learnin_rate'] = lr
            indicator = '*'
        print('max_depth: {}, n_estimators: {}, learning_rate: {}, accuracy: {} {}'.format(depth, n_est, lr, score, indicator))

max_depth: 5, n_estimators: 300, learning_rate: 0.1, accuracy: 0.9149868536371605 *best_params = {'max_depth': 3, 'n_estimators': 300, 'learning_rate': 0.05}
# In[341]:


clf = xgb.XGBClassifier(**best_params, n_jobs=4)
clf.fit(train.df[feature_cols].values, train.df[target_cols].values.flatten())


# In[342]:


test = cs_detection.ClearskyDetection(nsrdb.df)
test.trim_dates('06-01-2015', None)


# In[343]:


get_ipython().run_cell_magic('time', '', "pred = test.iter_predict_daily(feature_cols, 'GHI', 'Clearsky GHI pvlib', clf, 3, multiproc=False).astype(bool)")


# In[344]:


vis = visualize.Visualizer()
vis.add_line_ser(test.df['GHI'], 'GHI')
vis.add_line_ser(test.df['Clearsky GHI pvlib'], 'GHI_cs')
vis.add_circle_ser(test.df[(test.df['sky_status'] == 0) & (pred)]['GHI'], 'ML clear only')
vis.add_circle_ser(test.df[(test.df['sky_status'] == 1) & (~pred)]['GHI'], 'NSRDB clear only')
vis.add_circle_ser(test.df[(test.df['sky_status'] == 1) & (pred)]['GHI'], 'ML+NSRDB clear only')
vis.show()


# In[345]:


cm = metrics.confusion_matrix(test.df['sky_status'].values, pred)
vis = visualize.Visualizer()
vis.plot_confusion_matrix(cm, labels=['cloudy', 'clear'])


# In[346]:


print(metrics.f1_score(test.df['sky_status'].values, pred))


# # Train on all NSRDB data, test various freq of ground data

# In[347]:


train = cs_detection.ClearskyDetection(nsrdb.df)
train.scale_model('GHI', 'Clearsky GHI pvlib', 'sky_status')
utils.calc_all_window_metrics(train.df, 3, meas_col='GHI', model_col='Clearsky GHI pvlib', overwrite=True)
clf.fit(train.df[feature_cols].values, train.df[target_cols].values.flatten())


# In[348]:


bar = go.Bar(x=feature_cols, y=clf.feature_importances_)
iplot([bar])


# ## 30 min freq ground data

# In[349]:


ground = cs_detection.ClearskyDetection.read_pickle('abq_ground_1.pkl.gz')
ground.df.index = ground.df.index.tz_convert('MST')
test = cs_detection.ClearskyDetection(ground.df)


# In[350]:


test.trim_dates('10-08-2015', '10-16-2015')


# In[351]:


test.time_from_solar_noon('Clearsky GHI pvlib', 'tfn')


# In[352]:


test.df = test.df[test.df.index.minute % 30 == 0]


# In[353]:


pred = test.iter_predict_daily(feature_cols, 'GHI', 'Clearsky GHI pvlib', clf, 3).astype(bool)


# In[354]:


train2 = cs_detection.ClearskyDetection(train.df)
train2.intersection(test.df.index)


# In[355]:


nsrdb_clear = train2.df['sky_status'].values
ml_clear = pred
vis = visualize.Visualizer()
vis.add_line_ser(test.df['GHI'], 'GHI')
vis.add_line_ser(test.df['Clearsky GHI pvlib'], 'GHI_cs')
vis.add_circle_ser(test.df[ml_clear & ~nsrdb_clear]['GHI'], 'ML clear only')
vis.add_circle_ser(test.df[~ml_clear & nsrdb_clear]['GHI'], 'NSRDB clear only')
vis.add_circle_ser(test.df[ml_clear & nsrdb_clear]['GHI'], 'Both clear')
vis.show()


# ## 15 min freq ground data

# In[356]:


ground = cs_detection.ClearskyDetection.read_pickle('abq_ground_1.pkl.gz')
ground.df.index = ground.df.index.tz_convert('MST')
test = cs_detection.ClearskyDetection(ground.df)


# In[357]:


test.trim_dates('10-08-2015', '10-16-2015')


# In[358]:


test.time_from_solar_noon('Clearsky GHI pvlib', 'tfn')


# In[359]:


test.df = test.df[test.df.index.minute % 15 == 0]


# In[360]:


pred = test.iter_predict_daily(feature_cols, 'GHI', 'Clearsky GHI pvlib', clf, 5).astype(bool)


# In[361]:


train2 = cs_detection.ClearskyDetection(train.df)
train2.trim_dates('10-08-2015', '10-16-2015')
train2.df = train2.df.reindex(pd.date_range(start=train2.df.index[0], end=train2.df.index[-1], freq='15min'))
train2.df['sky_status'] = train2.df['sky_status'].fillna(False)


# In[362]:


nsrdb_clear = train2.df['sky_status']
ml_clear = test.df['sky_status iter']
vis = visualize.Visualizer()
vis.add_line_ser(test.df['GHI'], 'GHI')
vis.add_line_ser(test.df['Clearsky GHI pvlib'], 'GHI_cs')
vis.add_circle_ser(test.df[ml_clear & ~nsrdb_clear]['GHI'], 'ML clear only')
vis.add_circle_ser(test.df[~ml_clear & nsrdb_clear]['GHI'], 'NSRDB clear only')
vis.add_circle_ser(test.df[ml_clear & nsrdb_clear]['GHI'], 'Both clear')
vis.show()


# ## 10 min freq ground data

# In[263]:


ground = cs_detection.ClearskyDetection.read_pickle('abq_ground_1.pkl.gz')
ground.df.index = ground.df.index.tz_convert('MST')
test = cs_detection.ClearskyDetection(ground.df)


# In[264]:


test.trim_dates('10-08-2015', '10-16-2015')


# In[265]:


test.time_from_solar_noon('Clearsky GHI pvlib', 'tfn')


# In[266]:


test.df = test.df[test.df.index.minute % 10 == 0]


# In[267]:


pred = test.iter_predict_daily(feature_cols, 'GHI', 'Clearsky GHI pvlib', clf, 7).astype(bool)


# In[268]:


train2 = cs_detection.ClearskyDetection(train.df)
train2.trim_dates('10-08-2015', '10-16-2015')
train2.df = train2.df.reindex(pd.date_range(start=train2.df.index[0], end=train2.df.index[-1], freq='10min'))
train2.df['sky_status'] = train2.df['sky_status'].fillna(False)


# In[269]:


nsrdb_clear = train2.df['sky_status']
ml_clear = test.df['sky_status iter']
vis = visualize.Visualizer()
vis.add_line_ser(test.df['GHI'], 'GHI')
vis.add_line_ser(test.df['Clearsky GHI pvlib'], 'GHI_cs')
vis.add_circle_ser(test.df[ml_clear & ~nsrdb_clear]['GHI'], 'ML clear only')
vis.add_circle_ser(test.df[~ml_clear & nsrdb_clear]['GHI'], 'NSRDB clear only')
vis.add_circle_ser(test.df[ml_clear & nsrdb_clear]['GHI'], 'Both clear')
vis.show()


# ## 5 min freq ground data

# In[270]:


ground = cs_detection.ClearskyDetection.read_pickle('abq_ground_1.pkl.gz')
ground.df.index = ground.df.index.tz_convert('MST')
test = cs_detection.ClearskyDetection(ground.df)


# In[271]:


test.trim_dates('10-08-2015', '10-16-2015')


# In[272]:


test.time_from_solar_noon('Clearsky GHI pvlib', 'tfn')


# In[273]:


test.df = test.df[test.df.index.minute % 5 == 0]


# In[274]:


pred = test.iter_predict_daily(feature_cols, 'GHI', 'Clearsky GHI pvlib', clf, 13).astype(bool)


# In[275]:


train2 = cs_detection.ClearskyDetection(train.df)
train2.trim_dates('10-08-2015', '10-16-2015')
train2.df = train2.df.reindex(pd.date_range(start=train2.df.index[0], end=train2.df.index[-1], freq='5min'))
train2.df['sky_status'] = train2.df['sky_status'].fillna(False)


# In[276]:


nsrdb_clear = train2.df['sky_status']
ml_clear = test.df['sky_status iter']
vis = visualize.Visualizer()
vis.add_line_ser(test.df['GHI'], 'GHI')
vis.add_line_ser(test.df['Clearsky GHI pvlib'], 'GHI_cs')
vis.add_circle_ser(test.df[ml_clear & ~nsrdb_clear]['GHI'], 'ML clear only')
vis.add_circle_ser(test.df[~ml_clear & nsrdb_clear]['GHI'], 'NSRDB clear only')
vis.add_circle_ser(test.df[ml_clear & nsrdb_clear]['GHI'], 'Both clear')
vis.show()


# ## 1 min freq ground data

# In[277]:


ground = cs_detection.ClearskyDetection.read_pickle('abq_ground_1.pkl.gz')
ground.df.index = ground.df.index.tz_convert('MST')
test = cs_detection.ClearskyDetection(ground.df)


# In[278]:


test.trim_dates('10-08-2015', '10-16-2015')


# In[279]:


test.time_from_solar_noon('Clearsky GHI pvlib', 'tfn')


# In[280]:


test.df = test.df[test.df.index.minute % 1 == 0]


# In[281]:


pred = test.iter_predict_daily(feature_cols, 'GHI', 'Clearsky GHI pvlib', clf, 61).astype(bool)


# In[282]:


train2 = cs_detection.ClearskyDetection(train.df)
train2.trim_dates('10-08-2015', '10-16-2015')
train2.df = train2.df.reindex(pd.date_range(start=train2.df.index[0], end=train2.df.index[-1], freq='1min'))
train2.df['sky_status'] = train2.df['sky_status'].fillna(False)


# In[283]:


nsrdb_clear = train2.df['sky_status']
ml_clear = test.df['sky_status iter']
vis = visualize.Visualizer()
vis.add_line_ser(test.df['GHI'], 'GHI')
vis.add_line_ser(test.df['Clearsky GHI pvlib'], 'GHI_cs')
vis.add_circle_ser(test.df[ml_clear & ~nsrdb_clear]['GHI'], 'ML clear only')
vis.add_circle_ser(test.df[~ml_clear & nsrdb_clear]['GHI'], 'NSRDB clear only')
vis.add_circle_ser(test.df[ml_clear & nsrdb_clear]['GHI'], 'Both clear')
vis.show()


# # Save model

# In[67]:


import pickle


# In[68]:


with open('abq_trained.pkl', 'wb') as f:
    pickle.dump(clf, f)


# In[70]:


get_ipython().system('ls abq*')


# # Conclusion

# In general, the clear sky identification looks good.  At lower frequencies (30 min, 15 min) we see good agreement with NSRDB labeled points.  I suspect this could be further improved my doing a larger hyperparameter search, or even doing some feature extraction/reduction/additions.  

# In[ ]:




