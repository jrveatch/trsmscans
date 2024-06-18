from parse import Parse
from masses import Masses
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats

file = "/Users/yukomaeda/TRSM/trsmscans/run/data/5000 pts/TRSMBroken_test_0000.tsv"

masses = Masses(mX=1000, mS=300, mH=125.09)
parse = Parse(masses=masses, decay="SbbHtautau", modelname="TRSMBroken", filename=file)

target = parse.getXB(decay="SbbHtautau")
features = parse.getParameters()

# Reshape the data and create the DataFrame
reshaped_data = {key: value.reshape(-1, 1) for key, value in features.items()}
df = pd.DataFrame(np.hstack(list(reshaped_data.values())), columns=features.keys())

# Add the target column
df['xb'] = target
print(df.head())
print()
print(f"Found {len(df)} points!!!!!")
print()

# Pairplot
sns.pairplot(df)
plt.show()

# Correlation heatmap (not sure that this is useful at all right now)
corr = df.corr()
plt.figure(figsize=(10, 8))
sns.heatmap(corr, annot=True, cmap= 'coolwarm', center=0)
plt.show()

# Histograms
df.hist(bins=20, figsize=(14, 10))
plt.show()

# Box plots and Violin plots (don't look great)
'''
plt.figure(figsize=(14, 10))
sns.boxplot(data=df)
plt.show()

plt.figure(figsize=(14, 10))
sns.violinplot(data=df)
plt.show()
'''

# Countplot for the target variable (looks pretty useless)
#plt.figure(figsize=(8, 6))
#sns.countplot(x='xb', data=df)  #  'target' is 'xb'
#plt.show()


# Calculate mean, median
statistics = {}
for column in df.columns:
    mean = df[column].mean()
    median = df[column].median()

    statistics[column] = {'mean': mean, 'median': median}

# Print the results
for column, stats in statistics.items():
    print(f"Statistics for {column}:")
    print(f"  Mean: {stats['mean']}")
    print(f"  Median: {stats['median']}")

# this is not working
'''
from sklearn.ensemble import RandomForestClassifier

# Assuming binary classification with 'xb' as the target variable
X = df.drop('xb', axis=1)
y = df['xb']

model = RandomForestClassifier()
model.fit(X, y)

importances = model.feature_importances_
indices = np.argsort(importances)[::-1]

plt.figure(figsize=(10, 6))
plt.title("Feature importances")
plt.bar(range(X.shape[1]), importances[indices], align="center")
plt.xticks(range(X.shape[1]), [X.columns[i] for i in indices])
plt.xlim([-1, X.shape[1]])
plt.show()
'''

