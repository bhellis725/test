
# coding: utf-8

# # Table of Contents
#  <p><div class="lev1 toc-item"><a href="#Ground-predictions" data-toc-modified-id="Ground-predictions-1"><span class="toc-item-num">1&nbsp;&nbsp;</span>Ground predictions</a></div><div class="lev2 toc-item"><a href="#PVLib-Clearsky" data-toc-modified-id="PVLib-Clearsky-11"><span class="toc-item-num">1.1&nbsp;&nbsp;</span>PVLib Clearsky</a></div><div class="lev1 toc-item"><a href="#Train/test-on-NSRDB-data-to-find-optimal-parameters" data-toc-modified-id="Train/test-on-NSRDB-data-to-find-optimal-parameters-2"><span class="toc-item-num">2&nbsp;&nbsp;</span>Train/test on NSRDB data to find optimal parameters</a></div><div class="lev2 toc-item"><a href="#Default-classifier" data-toc-modified-id="Default-classifier-21"><span class="toc-item-num">2.1&nbsp;&nbsp;</span>Default classifier</a></div><div class="lev2 toc-item"><a href="#Gridsearch" data-toc-modified-id="Gridsearch-22"><span class="toc-item-num">2.2&nbsp;&nbsp;</span>Gridsearch</a></div><div class="lev2 toc-item"><a href="#Best-recall-model" data-toc-modified-id="Best-recall-model-23"><span class="toc-item-num">2.3&nbsp;&nbsp;</span>Best recall model</a></div><div class="lev2 toc-item"><a href="#Best-accuracy-model" data-toc-modified-id="Best-accuracy-model-24"><span class="toc-item-num">2.4&nbsp;&nbsp;</span>Best accuracy model</a></div><div class="lev2 toc-item"><a href="#Best-precision-model" data-toc-modified-id="Best-precision-model-25"><span class="toc-item-num">2.5&nbsp;&nbsp;</span>Best precision model</a></div><div class="lev2 toc-item"><a href="#Best-f1-model" data-toc-modified-id="Best-f1-model-26"><span class="toc-item-num">2.6&nbsp;&nbsp;</span>Best f1 model</a></div><div class="lev1 toc-item"><a href="#Train-on-all-NSRDB-data,-test-various-freq-of-ground-data" data-toc-modified-id="Train-on-all-NSRDB-data,-test-various-freq-of-ground-data-3"><span class="toc-item-num">3&nbsp;&nbsp;</span>Train on all NSRDB data, test various freq of ground data</a></div><div class="lev2 toc-item"><a href="#30-min-freq-ground-data" data-toc-modified-id="30-min-freq-ground-data-31"><span class="toc-item-num">3.1&nbsp;&nbsp;</span>30 min freq ground data</a></div><div class="lev2 toc-item"><a href="#15-min-freq-ground-data" data-toc-modified-id="15-min-freq-ground-data-32"><span class="toc-item-num">3.2&nbsp;&nbsp;</span>15 min freq ground data</a></div><div class="lev2 toc-item"><a href="#10-min-freq-ground-data" data-toc-modified-id="10-min-freq-ground-data-33"><span class="toc-item-num">3.3&nbsp;&nbsp;</span>10 min freq ground data</a></div><div class="lev2 toc-item"><a href="#5-min-freq-ground-data" data-toc-modified-id="5-min-freq-ground-data-34"><span class="toc-item-num">3.4&nbsp;&nbsp;</span>5 min freq ground data</a></div><div class="lev2 toc-item"><a href="#1-min-freq-ground-data" data-toc-modified-id="1-min-freq-ground-data-35"><span class="toc-item-num">3.5&nbsp;&nbsp;</span>1 min freq ground data</a></div><div class="lev1 toc-item"><a href="#Save-model" data-toc-modified-id="Save-model-4"><span class="toc-item-num">4&nbsp;&nbsp;</span>Save model</a></div><div class="lev1 toc-item"><a href="#Conclusion" data-toc-modified-id="Conclusion-5"><span class="toc-item-num">5&nbsp;&nbsp;</span>Conclusion</a></div>

# In[1]:


import pandas as pd
import numpy as np
import os
import datetime
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.axes_grid1 import make_axes_locatable
from sklearn import tree
from sklearn import ensemble

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
import cufflinks as cf
cf.go_offline()
init_notebook_mode(connected=True)

from IPython.display import Image

get_ipython().magic('load_ext autoreload')
get_ipython().magic('autoreload 2')

np.set_printoptions(precision=4)
get_ipython().magic('matplotlib notebook')


# # Ground predictions

# ## PVLib Clearsky

# Only making ground predictions using PVLib clearsky model and statistical model.  NSRDB model won't be available to ground measurements.

# In[2]:


nsrdb = cs_detection.ClearskyDetection.read_pickle('abq_nsrdb_1.pkl.gz')
nsrdb.df.index = nsrdb.df.index.tz_convert('MST')
nsrdb.time_from_solar_noon('Clearsky GHI pvlib', 'tfn')


# In[3]:


len(nsrdb.df)


# # Train/test on NSRDB data to find optimal parameters

# ## Default classifier

# In[4]:


train = cs_detection.ClearskyDetection(nsrdb.df, scale_col=None)
train.trim_dates(None, '01-01-2015')
test = cs_detection.ClearskyDetection(nsrdb.df, scale_col=None)
test.trim_dates('01-01-2015', None)


# In[5]:


train.scale_model('GHI', 'Clearsky GHI pvlib', 'sky_status')


# In[6]:


clf = ensemble.RandomForestClassifier(random_state=42)


# In[7]:


utils.calc_all_window_metrics(train.df, 3, meas_col='GHI', model_col='Clearsky GHI pvlib', overwrite=True)


# In[8]:


feature_cols = [
    'tfn',
    'abs_ideal_ratio_diff grad',
    'abs_ideal_ratio_diff grad mean', 
    'abs_ideal_ratio_diff grad std',
    'abs_ideal_ratio_diff grad second',
    'abs_ideal_ratio_diff grad second mean',
    'abs_ideal_ratio_diff grad second std',
    'GHI Clearsky GHI pvlib line length ratio',
    'abs_ideal_ratio_diff', 
    'abs_ideal_ratio_diff mean',
    'abs_ideal_ratio_diff std',
    'GHI Clearsky GHI pvlib abs_diff',
    'GHI Clearsky GHI pvlib abs_diff mean', 
    'GHI Clearsky GHI pvlib abs_diff std'
]

target_cols = ['sky_status']


# In[9]:


vis = visualize.Visualizer()
vis.plot_corr_matrix(train.df[feature_cols].corr(), feature_cols)


# In[17]:


train = cs_detection.ClearskyDetection(nsrdb.df, scale_col=None)
train.trim_dates(None, '01-01-2015')
test = cs_detection.ClearskyDetection(nsrdb.df, scale_col=None)
test.trim_dates('01-01-2015', None)


# In[11]:


utils.calc_all_window_metrics(train.df, 3, meas_col='GHI', model_col='Clearsky GHI pvlib', overwrite=True)
clf.fit(train.df[feature_cols].values, train.df[target_cols].values.flatten())


# In[12]:


pred = test.iter_predict_daily(feature_cols, 'GHI', 'Clearsky GHI pvlib', clf, 3, multiproc=True, by_day=True).astype(bool)


# In[13]:


metrics.accuracy_score(test.df['sky_status'], pred)


# In[14]:


vis = visualize.Visualizer()
vis.add_line_ser(test.df['GHI'], 'GHI')
vis.add_line_ser(test.df['Clearsky GHI pvlib'], 'GHI_cs')
vis.add_circle_ser(test.df[(test.df['sky_status'] == 0) & (pred)]['GHI'], 'ML clear only')
vis.add_circle_ser(test.df[(test.df['sky_status'] == 1) & (~pred)]['GHI'], 'NSRDB clear only')
vis.add_circle_ser(test.df[(test.df['sky_status'] == 1) & (pred)]['GHI'], 'ML+NSRDB clear only')
vis.show()


# In[15]:


cm = metrics.confusion_matrix(test.df['sky_status'].values, pred)
vis = visualize.Visualizer()
vis.plot_confusion_matrix(cm, labels=['cloudy', 'clear'])


# In[16]:


bar = go.Bar(x=feature_cols, y=clf.feature_importances_)
iplot([bar])


# ## Gridsearch

# In[18]:


import warnings


# In[19]:


with warnings.catch_warnings():
    warnings.simplefilter('ignore')
    params={}
    params['max_depth'] = [4, 8, 12, 16]
    params['n_estimators'] = [64]
    params['class_weight'] = [None, 'balanced']
    params['min_samples_leaf'] = [1, 2, 3]
    results = []
    for depth, nest, cw, min_samples in itertools.product(params['max_depth'], params['n_estimators'], params['class_weight'], params['min_samples_leaf']):
        print('Params:')
        print('depth: {}, n_estimators: {}, class_weight: {}, min_samples_leaf: {}'.format(depth, nest, cw, min_samples))
        train2 = cs_detection.ClearskyDetection(train.df)
        train2.trim_dates('01-01-1999', '01-01-2014')
        utils.calc_all_window_metrics(train2.df, 3, meas_col='GHI', model_col='Clearsky GHI pvlib', overwrite=True)
        test2 = cs_detection.ClearskyDetection(train.df)
        test2.trim_dates('01-01-2014', '01-01-2015')
        clf = ensemble.RandomForestClassifier(max_depth=depth, n_estimators=nest, class_weight=cw, min_samples_leaf=min_samples, n_jobs=-1, random_state=42)
        clf.fit(train2.df[train2.df['GHI'] > 0][feature_cols].values, train2.df[train2.df['GHI'] > 0][target_cols].values.flatten())
        
        print('\t Scores:')
        test_pred = test2.iter_predict_daily(feature_cols, 'GHI', 'Clearsky GHI pvlib', clf, 3, multiproc=True, by_day=True)
        accuracy_score = metrics.accuracy_score(test2.df['sky_status'], test_pred)
        print('\t\t accuracy: {}'.format(accuracy_score))
        f1_score = metrics.f1_score(test2.df['sky_status'], test_pred)
        print('\t\t f1:{}'.format(f1_score))
        recall_score = metrics.recall_score(test2.df['sky_status'], test_pred)
        print('\t\t recall:{}'.format(recall_score))
        precision_score = metrics.precision_score(test2.df['sky_status'], test_pred)
        print('\t\t precision:{}'.format(precision_score))
        results.append({'max_depth': depth, 'n_estimators': nest, 'class_weight': cw, 'min_samples_leaf': min_samples,
                        'accuracy': accuracy_score, 'f1': f1_score, 'recall': recall_score, 'precision': precision_score})


# In[20]:


runs_df = pd.DataFrame(results)


# In[21]:


runs_df.to_csv('8_abq_non_directional_features.csv')


# In[22]:


runs_df[['accuracy', 'f1', 'recall', 'precision']].iplot(kind='box')


# In[23]:


runs_df


# ## Best recall model

# In[24]:


train = cs_detection.ClearskyDetection(nsrdb.df)
train.trim_dates(None, '01-01-2015')
test = cs_detection.ClearskyDetection(nsrdb.df)
test.trim_dates('01-01-2015', None)
train.scale_model('GHI', 'Clearsky GHI pvlib', 'sky_status')


# In[25]:


utils.calc_all_window_metrics(train.df, 3, meas_col='GHI', model_col='Clearsky GHI pvlib', overwrite=True)


# In[26]:


best_recall = runs_df.iloc[runs_df['recall'].idxmax()]


# In[27]:


params_recall = best_recall[['max_depth', 'n_estimators', 'class_weight', 'min_samples_leaf']].to_dict()


# In[28]:


params_recall


# In[29]:


clf = ensemble.RandomForestClassifier(**params_recall, n_jobs=-1)
clf.fit(train.df[feature_cols].values, train.df[target_cols].values.flatten())


# In[30]:


test = cs_detection.ClearskyDetection(nsrdb.df)
test.trim_dates('01-01-2015', None)


# In[31]:


pred = test.iter_predict_daily(feature_cols, 'GHI', 'Clearsky GHI pvlib', clf, 3, multiproc=True, by_day=True).astype(bool)


# In[32]:


vis = visualize.Visualizer()
vis.add_line_ser(test.df['GHI'], 'GHI')
vis.add_line_ser(test.df['Clearsky GHI pvlib'], 'GHI_cs')
vis.add_circle_ser(test.df[(test.df['sky_status'] == 0) & (pred)]['GHI'], 'ML clear only')
vis.add_circle_ser(test.df[(test.df['sky_status'] == 1) & (~pred)]['GHI'], 'NSRDB clear only')
vis.add_circle_ser(test.df[(test.df['sky_status'] == 1) & (pred)]['GHI'], 'ML+NSRDB clear only')
vis.show()


# In[33]:


cm = metrics.confusion_matrix(test.df['sky_status'].values, pred)
vis = visualize.Visualizer()
vis.plot_confusion_matrix(cm, labels=['cloudy', 'clear'])


# ## Best accuracy model

# In[34]:


train = cs_detection.ClearskyDetection(nsrdb.df)
train.trim_dates(None, '01-01-2015')
test = cs_detection.ClearskyDetection(nsrdb.df)
test.trim_dates('01-01-2015', None)
train.scale_model('GHI', 'Clearsky GHI pvlib', 'sky_status')


# In[35]:


utils.calc_all_window_metrics(train.df, 3, meas_col='GHI', model_col='Clearsky GHI pvlib', overwrite=True)


# In[36]:


best_accuracy = runs_df.iloc[runs_df['accuracy'].idxmax()]


# In[37]:


print(best_accuracy.equals(best_recall))


# In[38]:


params_accuracy = best_accuracy[['max_depth', 'n_estimators', 'class_weight', 'min_samples_leaf']].to_dict()


# In[39]:


params_accuracy


# In[40]:


clf = ensemble.RandomForestClassifier(**params_accuracy, n_jobs=-1)
clf.fit(train.df[feature_cols].values, train.df[target_cols].values.flatten())


# In[41]:


test = cs_detection.ClearskyDetection(nsrdb.df)
test.trim_dates('01-01-2015', None)


# In[42]:


pred = test.iter_predict_daily(feature_cols, 'GHI', 'Clearsky GHI pvlib', clf, 3, multiproc=True, by_day=True).astype(bool)


# In[43]:


vis = visualize.Visualizer()
vis.add_line_ser(test.df['GHI'], 'GHI')
vis.add_line_ser(test.df['Clearsky GHI pvlib'], 'GHI_cs')
vis.add_circle_ser(test.df[(test.df['sky_status'] == 0) & (pred)]['GHI'], 'ML clear only')
vis.add_circle_ser(test.df[(test.df['sky_status'] == 1) & (~pred)]['GHI'], 'NSRDB clear only')
vis.add_circle_ser(test.df[(test.df['sky_status'] == 1) & (pred)]['GHI'], 'ML+NSRDB clear only')
vis.show()


# In[44]:


cm = metrics.confusion_matrix(test.df['sky_status'].values, pred)
vis = visualize.Visualizer()
vis.plot_confusion_matrix(cm, labels=['cloudy', 'clear'])


# ## Best precision model

# In[45]:


train = cs_detection.ClearskyDetection(nsrdb.df)
train.trim_dates(None, '01-01-2015')
test = cs_detection.ClearskyDetection(nsrdb.df)
test.trim_dates('01-01-2015', None)
train.scale_model('GHI', 'Clearsky GHI pvlib', 'sky_status')


# In[46]:


utils.calc_all_window_metrics(train.df, 3, meas_col='GHI', model_col='Clearsky GHI pvlib', overwrite=True)


# In[47]:


best_precision = runs_df.iloc[runs_df['precision'].idxmax()]


# In[48]:


print(best_precision.equals(best_recall))
print(best_precision.equals(best_accuracy))


# In[49]:


params_precision = best_precision[['max_depth', 'n_estimators', 'class_weight', 'min_samples_leaf']].to_dict()


# In[50]:


params_precision


# In[51]:


clf = ensemble.RandomForestClassifier(**params_precision, n_jobs=-1)
clf.fit(train.df[feature_cols].values, train.df[target_cols].values.flatten())


# In[52]:


test = cs_detection.ClearskyDetection(nsrdb.df)
test.trim_dates('01-01-2015', None)


# In[53]:


pred = test.iter_predict_daily(feature_cols, 'GHI', 'Clearsky GHI pvlib', clf, 3, multiproc=True, by_day=True).astype(bool)


# In[54]:


vis = visualize.Visualizer()
vis.add_line_ser(test.df['GHI'], 'GHI')
vis.add_line_ser(test.df['Clearsky GHI pvlib'], 'GHI_cs')
vis.add_circle_ser(test.df[(test.df['sky_status'] == 0) & (pred)]['GHI'], 'ML clear only')
vis.add_circle_ser(test.df[(test.df['sky_status'] == 1) & (~pred)]['GHI'], 'NSRDB clear only')
vis.add_circle_ser(test.df[(test.df['sky_status'] == 1) & (pred)]['GHI'], 'ML+NSRDB clear only')
vis.show()


# In[55]:


cm = metrics.confusion_matrix(test.df['sky_status'].values, pred)
vis = visualize.Visualizer()
vis.plot_confusion_matrix(cm, labels=['cloudy', 'clear'])


# ## Best f1 model

# In[56]:


train = cs_detection.ClearskyDetection(nsrdb.df)
train.trim_dates(None, '01-01-2015')
test = cs_detection.ClearskyDetection(nsrdb.df)
test.trim_dates('01-01-2015', None)
train.scale_model('GHI', 'Clearsky GHI pvlib', 'sky_status')


# In[57]:


utils.calc_all_window_metrics(train.df, 3, meas_col='GHI', model_col='Clearsky GHI pvlib', overwrite=True)


# In[58]:


best_f1 = runs_df.iloc[runs_df['f1'].idxmax()]


# In[59]:


print(best_f1.equals(best_recall))
print(best_f1.equals(best_accuracy))
print(best_f1.equals(best_precision))


# Same model as best accuracy - scroll up.

# # Train on all NSRDB data, test various freq of ground data

# In[60]:


train = cs_detection.ClearskyDetection(nsrdb.df)
train.scale_model('GHI', 'Clearsky GHI pvlib', 'sky_status')
utils.calc_all_window_metrics(train.df, 3, meas_col='GHI', model_col='Clearsky GHI pvlib', overwrite=True)
clf = ensemble.RandomForestClassifier(**best_precision[['max_depth', 'class_weight', 'min_samples_leaf']].to_dict(), n_estimators=100)
clf.fit(train.df[feature_cols].values, train.df[target_cols].values.flatten())


# In[61]:


bar = go.Bar(x=feature_cols, y=clf.feature_importances_)
iplot([bar])


# ## 30 min freq ground data

# In[62]:


ground = cs_detection.ClearskyDetection.read_pickle('abq_ground_1.pkl.gz')
ground.df.index = ground.df.index.tz_convert('MST')
test = cs_detection.ClearskyDetection(ground.df)


# In[63]:


test.trim_dates('10-01-2015', '11-01-2015')


# In[64]:


test.df = test.df[test.df.index.minute % 30 == 0]


# In[65]:


test.df.keys()


# In[66]:


test.time_from_solar_noon('Clearsky GHI pvlib', 'tfn')


# In[67]:


pred = test.iter_predict_daily(feature_cols, 'GHI', 'Clearsky GHI pvlib', clf, 3, multiproc=True, by_day=True).astype(bool)


# In[68]:


train2 = cs_detection.ClearskyDetection(nsrdb.df)
train2.intersection(test.df.index)


# In[69]:


nsrdb_clear = train2.df['sky_status'].values
ml_clear = pred
vis = visualize.Visualizer()
vis.add_line_ser(test.df['GHI'], 'GHI')
vis.add_line_ser(test.df['Clearsky GHI pvlib'], 'GHI_cs')
vis.add_circle_ser(test.df[ml_clear & ~nsrdb_clear]['GHI'], 'ML clear only')
vis.add_circle_ser(test.df[~ml_clear & nsrdb_clear]['GHI'], 'NSRDB clear only')
vis.add_circle_ser(test.df[ml_clear & nsrdb_clear]['GHI'], 'Both clear')
vis.show()


# In[70]:


probas = clf.predict_proba(test.df[feature_cols].values)
test.df['probas'] = 0
test.df['probas'] = probas[:, 1]
visualize.plot_ts_slider_highligther(test.df, prob='probas')


# ## 15 min freq ground data

# In[71]:


ground = cs_detection.ClearskyDetection.read_pickle('abq_ground_1.pkl.gz')
ground.df.index = ground.df.index.tz_convert('MST')
test = cs_detection.ClearskyDetection(ground.df)


# In[72]:


test.trim_dates('10-01-2015', '10-17-2015')


# In[73]:


test.time_from_solar_noon('Clearsky GHI pvlib', 'tfn')


# In[74]:


test.df = test.df[test.df.index.minute % 15 == 0]
# test.df = test.df.resample('15T').apply(lambda x: x[len(x) // 2])


# In[75]:


pred = test.iter_predict_daily(feature_cols, 'GHI', 'Clearsky GHI pvlib', clf, 5, multiproc=True, by_day=True).astype(bool)


# In[76]:


train2 = cs_detection.ClearskyDetection(train.df)
train2.trim_dates('10-01-2015', '10-17-2015')
train2.df = train2.df.reindex(pd.date_range(start=train2.df.index[0], end=train2.df.index[-1], freq='15min'))
train2.df['sky_status'] = train2.df['sky_status'].fillna(False)


# In[77]:


nsrdb_clear = train2.df['sky_status']
ml_clear = test.df['sky_status iter']
vis = visualize.Visualizer()
vis.add_line_ser(test.df['GHI'], 'GHI')
vis.add_line_ser(test.df['Clearsky GHI pvlib'], 'GHI_cs')
vis.add_circle_ser(test.df[ml_clear & ~nsrdb_clear]['GHI'], 'ML clear only')
vis.add_circle_ser(test.df[~ml_clear & nsrdb_clear]['GHI'], 'NSRDB clear only')
vis.add_circle_ser(test.df[ml_clear & nsrdb_clear]['GHI'], 'Both clear')
vis.show()


# In[78]:


probas = clf.predict_proba(test.df[feature_cols].values)
test.df['probas'] = 0
test.df['probas'] = probas[:, 1]
visualize.plot_ts_slider_highligther(test.df, prob='probas')


# ## 10 min freq ground data

# In[79]:


ground = cs_detection.ClearskyDetection.read_pickle('abq_ground_1.pkl.gz')
ground.df.index = ground.df.index.tz_convert('MST')
test = cs_detection.ClearskyDetection(ground.df)


# In[80]:


test.trim_dates('10-01-2015', '10-08-2015')


# In[81]:


test.time_from_solar_noon('Clearsky GHI pvlib', 'tfn')
test.scale_by_irrad('Clearsky GHI pvlib')


# In[82]:


test.df = test.df[test.df.index.minute % 10 == 0]


# In[83]:


pred = test.iter_predict_daily(feature_cols, 'GHI', 'Clearsky GHI pvlib', clf, 7, multiproc=True, by_day=True).astype(bool)


# In[84]:


train2 = cs_detection.ClearskyDetection(train.df)
train2.trim_dates('10-01-2015', '10-08-2015')
train2.df = train2.df.reindex(pd.date_range(start=train2.df.index[0], end=train2.df.index[-1], freq='10min'))
train2.df['sky_status'] = train2.df['sky_status'].fillna(False)


# In[85]:


nsrdb_clear = train2.df['sky_status']
ml_clear = test.df['sky_status iter']
vis = visualize.Visualizer()
vis.add_line_ser(test.df['GHI'], 'GHI')
vis.add_line_ser(test.df['Clearsky GHI pvlib'], 'GHI_cs')
vis.add_circle_ser(test.df[ml_clear & ~nsrdb_clear]['GHI'], 'ML clear only')
vis.add_circle_ser(test.df[~ml_clear & nsrdb_clear]['GHI'], 'NSRDB clear only')
vis.add_circle_ser(test.df[ml_clear & nsrdb_clear]['GHI'], 'Both clear')
vis.show()


# In[86]:


probas = clf.predict_proba(test.df[feature_cols].values)
test.df['probas'] = 0
test.df['probas'] = probas[:, 1]

visualize.plot_ts_slider_highligther(test.df, prob='probas')


# ## 5 min freq ground data

# In[87]:


ground = cs_detection.ClearskyDetection.read_pickle('abq_ground_1.pkl.gz')
ground.df.index = ground.df.index.tz_convert('MST')
test = cs_detection.ClearskyDetection(ground.df)


# In[88]:


test.trim_dates('10-01-2015', '10-04-2015')


# In[89]:


test.time_from_solar_noon('Clearsky GHI pvlib', 'tfn')
test.scale_by_irrad('Clearsky GHI pvlib')


# In[90]:


test.df = test.df[test.df.index.minute % 5 == 0]


# In[91]:


pred = test.iter_predict_daily(feature_cols, 'GHI', 'Clearsky GHI pvlib', clf, 13, multiproc=True, by_day=True).astype(bool)


# In[92]:


train2 = cs_detection.ClearskyDetection(train.df)
train2.trim_dates('10-01-2015', '10-17-2015')
train2.df = train2.df.reindex(pd.date_range(start=train2.df.index[0], end=train2.df.index[-1], freq='5min'))
train2.df['sky_status'] = train2.df['sky_status'].fillna(False)


# In[93]:


nsrdb_clear = train2.df['sky_status']
ml_clear = test.df['sky_status iter']
vis = visualize.Visualizer()
vis.add_line_ser(test.df['GHI'], 'GHI')
vis.add_line_ser(test.df['Clearsky GHI pvlib'], 'GHI_cs')
vis.add_circle_ser(test.df[ml_clear & ~nsrdb_clear]['GHI'], 'ML clear only')
vis.add_circle_ser(test.df[~ml_clear & nsrdb_clear]['GHI'], 'NSRDB clear only')
vis.add_circle_ser(test.df[ml_clear & nsrdb_clear]['GHI'], 'Both clear')
vis.show()


# In[94]:


probas = clf.predict_proba(test.df[feature_cols].values)
test.df['probas'] = 0
test.df['probas'] = probas[:, 1]

visualize.plot_ts_slider_highligther(test.df, prob='probas')


# ## 1 min freq ground data

# In[95]:


ground = cs_detection.ClearskyDetection.read_pickle('abq_ground_1.pkl.gz')
ground.df.index = ground.df.index.tz_convert('MST')
test = cs_detection.ClearskyDetection(ground.df)


# In[96]:


test.trim_dates('10-01-2015', '10-08-2015')


# In[97]:


test.time_from_solar_noon('Clearsky GHI pvlib', 'tfn')
test.scale_by_irrad('Clearsky GHI pvlib')


# In[98]:


test.df = test.df[test.df.index.minute % 1 == 0]


# In[99]:


pred = test.iter_predict_daily(feature_cols, 'GHI', 'Clearsky GHI pvlib', clf, 61, multiproc=True, by_day=True).astype(bool)


# In[100]:


train2 = cs_detection.ClearskyDetection(train.df)
train2.trim_dates('10-01-2015', '10-08-2015')
train2.df = train2.df.reindex(pd.date_range(start=train2.df.index[0], end=train2.df.index[-1], freq='1min'))
train2.df['sky_status'] = train2.df['sky_status'].fillna(False)


# In[101]:


nsrdb_clear = train2.df['sky_status']
ml_clear = test.df['sky_status iter']
vis = visualize.Visualizer()
vis.add_line_ser(test.df['GHI'], 'GHI')
vis.add_line_ser(test.df['Clearsky GHI pvlib'], 'GHI_cs')
vis.add_circle_ser(test.df[ml_clear & ~nsrdb_clear]['GHI'], 'ML clear only')
vis.add_circle_ser(test.df[~ml_clear & nsrdb_clear]['GHI'], 'NSRDB clear only')
vis.add_circle_ser(test.df[ml_clear & nsrdb_clear]['GHI'], 'Both clear')
vis.show()


# In[102]:


probas = clf.predict_proba(test.df[feature_cols].values)
test.df['probas'] = 0
test.df['probas'] = probas[:, 1]
visualize.plot_ts_slider_highligther(test.df, prob='probas')


# # Save model

# In[ ]:


import pickle


# In[ ]:


with open('8_abq_direction_features_model.pkl', 'wb') as f:
    pickle.dump(clf, f)


# In[ ]:


get_ipython().system('ls *abq*')


# # Conclusion

# In general, the clear sky identification looks good.  At lower frequencies (30 min, 15 min) we see good agreement with NSRDB labeled points.  I suspect this could be further improved my doing a larger hyperparameter search, or even doing some feature extraction/reduction/additions.  

# In[ ]:




