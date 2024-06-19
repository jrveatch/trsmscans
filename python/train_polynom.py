from parse import Parse
from masses import Masses
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
#import torch
#from torch.utils.data import DataLoader, TensorDataset

from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score


# load dataset
file = "/Users/yukomaeda/TRSM/trsmscans/run/data/10k/TRSMBroken_test_0000.tsv"

# set values for random seed, train/test/validation split here
random_seed = 42
train_size = 0.7
val_size = 0.2
test_size = 1 - train_size - val_size

#***********************************************************************************************

# Using Masses and Parse object to filter out only the points that fit the criteria in the tsv
masses = Masses(mX=1000, mS=300, mH=125.09)
parse = Parse(masses=masses, decay="SbbHtautau", modelname="TRSMBroken", filename=file)

target = parse.getXB(decay="SbbHtautau")
features = parse.getParameters()

# Reshape the data and create the DataFrame
reshaped_data = {key: value.reshape(-1, 1) for key, value in features.items()}
df = pd.DataFrame(np.hstack(list(reshaped_data.values())), columns=features.keys())

# Add the target column
df_target = pd.DataFrame(target, columns=['xb'])

# Since number of points found is not the same as requested, print how many pts here
print(f"Found {len(df)} points!!!!!")

# check number of target matches the features
if not len(df) == len(df_target):
    print("Value mismatch: features and target")

# Normalize ... or maybe scale???
scaler = MinMaxScaler()
X = scaler.fit_transform(df)
normalized_df = pd.DataFrame(X, columns=df.columns)

# if standardizing... (ie, instead of normalizing)
standard_scaler = StandardScaler()
X = standard_scaler.fit_transform(df)
standardized_df = pd.DataFrame(X, columns=df.columns)

# Split into train 
X_train, X_temp, y_train, y_temp = train_test_split(normalized_df, df_target, train_size=train_size, random_state=random_seed)
#X_train, X_temp, y_train, y_temp = train_test_split(standardized_df, df_target, train_size=train_size, random_state=random_seed)

# Split rest into test and validation (did I do my math right?)
X_val, X_test, y_val, y_test = train_test_split(X_temp, y_temp, test_size=(test_size/(val_size + test_size)), random_state=random_seed)

# Generate polynomial features
degree = 2  # Degree of the polynomial features
poly = PolynomialFeatures(degree)
X_train_poly = poly.fit_transform(X_train)
X_val_poly = poly.transform(X_val)
X_test_poly = poly.transform(X_test)

# Fit the Linear Regression model on polynomial features
model = LinearRegression()
model.fit(X_train_poly, y_train)

# Predict on validation and test sets
y_val_pred = model.predict(X_val_poly)
y_test_pred = model.predict(X_test_poly)

# Evaluate the model
val_mse = mean_squared_error(y_val, y_val_pred)
test_mse = mean_squared_error(y_test, y_test_pred)
# Evaluate the model using RMSE and R-squared
val_rmse = np.sqrt(mean_squared_error(y_val, y_val_pred))
test_rmse = np.sqrt(mean_squared_error(y_test, y_test_pred))

val_r2 = r2_score(y_val, y_val_pred)
test_r2 = r2_score(y_test, y_test_pred)

print(f"Validation MSE: {val_mse}")
print(f"Test MSE: {test_mse}")
print(f"Validation RMSE: {val_rmse}")
print(f"Test RMSE: {test_rmse}")
print(f"Validation R-squared: {val_r2}")
print(f"Test R-squared: {test_r2}")

# Print the polynomial expression
feature_names = poly.get_feature_names_out(df.columns)
coefficients = model.coef_
intercept = model.intercept_

#expression = "%.2f" % intercept
#print("expression: ", expression)
for coef, name in zip(coefficients, feature_names):
    print("coef: ",coef)
    print("name: ", name)
    #expression += " + " + coef +" * " + name

#print("Polynomial expression:")
#print(expression)



