import pandas as pd
import matplotlib.pyplot as plt
from ast import literal_eval
import numpy as np
from scipy import signal
import seaborn as sns
import math

acc_data = pd.read_csv('/home/pi/Documents/MPU/acc_data_new.csv')
#acc_data['accel_data'] = acc_data['accel_data'].apply(literal_eval)
#acc_data = pd.concat([acc_data.drop(['accel_data'], axis=1), acc_data['accel_data'].apply(pd.Series)], axis=1)
#acc_data['logdatetime'] = pd.to_datetime(acc_data['logdatetime'])

#acc_data.to_csv('processed_acc_data.csv', index=False)
print(acc_data.head())
#print(acc_data[~(acc_data['impact_no'] == 0)]['pos'].value_counts()/200)

mean_x = acc_data[acc_data['pos'].isna()]['x'].mean()
mean_y = acc_data[acc_data['pos'].isna()]['y'].mean()
mean_z = acc_data[acc_data['pos'].isna()]['z'].mean()

acc_data = acc_data[~(acc_data['pos'].isna())].reset_index(drop=True)
acc_data['impact_no'] = [math.floor(idx/200) + 1 for idx in list(acc_data.index)]

#def get_actual_mean_freq(impact_data):
#    impact_data['logdatetime_minus_1'] = impact_data['logdatetime'].shift(periods=1)
#    impact_data = impact_data.dropna().reset_index()
#    impact_data['logdatetime_diff'] = impact_data['logdatetime'] - impact_data['logdatetime_minus_1']
#    impact_data['logdatetime_diff'] = impact_data['logdatetime_diff'].apply(lambda x: x.microseconds)
#    #impact_data['logdatetime_diff'].plot.hist(bins=500)
#    #plt.show()
#    return int(1000000/impact_data['logdatetime_diff'].mean())

def calc_lag(impact_data):
    x_data = impact_data['x']
    y_data = impact_data['y']
    corr = np.correlate(x_data - mean_x, y_data - mean_y, mode='full')
    lag = corr.argmax() - (len(x_data) - 1)
    return lag

#def calc_nrgy(impact_data):
#    z_data = impact_data['z']
#    return np.sum((z_data - mean_z)**2) / len(z_data)

def calc_slopes(impact_data):
    z_data = impact_data['z']
    slope1 = np.mean(abs(z_data[0:50] - mean_z)) - np.mean(abs(z_data[50:100] - mean_z))
    slope2 = np.mean(abs(z_data[100:150] - mean_z)) - np.mean(abs(z_data[150:200] - mean_z))
    return {'slope1': slope1, 'slope2': slope2}

def calc_peak_freq(impact_data):
    sampling_freq = 500
    impact_data_z = impact_data['z'] - mean_z
    window = signal.windows.hann(len(impact_data_z)) #force-exp is apparently the best option...
    fourierTransform = np.fft.fft(window * (impact_data_z)) / len(impact_data_z)
    fourierTransform = fourierTransform[range(int(len(impact_data_z) / 2))]
    tpCount = len(impact_data_z)
    values = np.arange(int(tpCount/2))
    timePeriod = tpCount/sampling_freq
    frequencies = values/timePeriod
    peak_freq1 = frequencies[np.argmax(abs(fourierTransform))]
    fourierTransform[np.argmax(abs(fourierTransform))] = 0
    peak_freq2 = frequencies[np.argmax(abs(fourierTransform))]
    peak_freq = [peak_freq1, peak_freq2]
    #peakind = signal.find_peaks_cwt(abs(fourierTransform), [10])
    return {'peak_freq1': max(peak_freq), 'peak_freq2': min(peak_freq)} #frequencies[peakind]

features = []

for impact_no in acc_data['impact_no'].unique():
    impact_data = acc_data[acc_data['impact_no'] == impact_no]
    features.append([impact_no, calc_slopes(impact_data), calc_lag(impact_data), calc_peak_freq(impact_data), impact_data['pos'].unique()[0]])

features = pd.DataFrame(features, columns=['impact_no', 'slopes', 'xy_lag', 'peak_freqs', 'pos'])
features = pd.concat([features.drop(['slopes'], axis=1), features['slopes'].apply(pd.Series)], axis=1)
features = pd.concat([features.drop(['peak_freqs'], axis=1), features['peak_freqs'].apply(pd.Series)], axis=1)
#features['z_nrgy_log'] = np.log10(features['z_nrgy'])

sns.violinplot(x="pos", y="slope2", data=features)
plt.show()

sns.scatterplot(x="peak_freq1", y="peak_freq2", data=features, hue="pos")
plt.show()

sns.pairplot(features[['xy_lag', 'peak_freq1', 'pos', 'slope1', 'slope2']], hue="pos")
plt.show()

corr = features[['xy_lag', 'peak_freq1', 'pos', 'slope1', 'slope2']].corr()
print(corr)

for impact_no in [1, 8, 13, 27, 34, 41, 42]:
    impact_data = acc_data[acc_data['impact_no'] == impact_no]
    plt.plot(impact_data['z'])
    plt.show()

from sklearn import preprocessing
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import GaussianNB
from sklearn.tree import DecisionTreeClassifier
from sklearn import tree
from joblib import dump
from sklearn.ensemble import GradientBoostingClassifier

X = features[['xy_lag', 'peak_freq1', 'slope1', 'slope2']]
y = list(features['pos'])
X_scaled = preprocessing.scale(X)

sns.pairplot(pd.DataFrame(X_scaled, columns=['xy_lag', 'peak_freq', 'slope1', 'slope2']))
plt.show()

clf = LogisticRegression(random_state=0).fit(X_scaled, y)
print(clf.score(X_scaled, y))

clfNB = GaussianNB()
clfNB.fit(X_scaled, y)
print(clfNB.score(X_scaled, y))

clfDT = DecisionTreeClassifier(random_state=0, max_depth=4)
clfDT.fit(X, y)
print(clfDT.score(X, y))

fig, axes = plt.subplots(nrows = 1,ncols = 1,figsize = (4,4), dpi=300)
tree.plot_tree(clfDT,
               feature_names = ['xy_lag', 'peak_freq1', 'slope1', 'slope2'],
               class_names = clfDT.classes_,
               filled = True);
fig.savefig('imagename.png')

dump(clfDT, 'impact_classifier.skm')

clfGB = GradientBoostingClassifier(random_state=0)
clfGB.fit(X, y)
print(clfGB.score(X, y))

dump(clfGB, 'impact_classifier_GB.skm')