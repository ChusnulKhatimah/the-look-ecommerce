# -*- coding: utf-8 -*-
"""Sales_Kelompok_113_Andi_Chusnul_Khatimah_Amin.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1k3675d8nZNP_vQI-Ee2eWt0EGD5GXd1p

# 1. Data Understanding

Load all the modules needed in this analysis.
"""

! pip install catboost

! pip install shap

# Commented out IPython magic to ensure Python compatibility.
import numpy as np 
import pandas as pd 
import matplotlib.pyplot as plt
# %matplotlib inline

import seaborn as sns
sns.set()

from catboost import CatBoostRegressor, Pool, cv
from catboost import MetricVisualizer

from sklearn.model_selection import TimeSeriesSplit
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans

from scipy.stats import boxcox
from os import listdir

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=RuntimeWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

import shap
shap.initjs()

# import sales dataset
data = pd.read_csv('/content/drive/MyDrive/RG CAMP/Final Project - 113/Dataset Final Project/Sales/sales1.csv')

# see sales dataset dimension
data.shape
print('Dataframe dimensions:', data.shape)

"""sales dataset contains 180.508 rows and 12 columns."""

# take a look at first five rows of sales dataset
data.head()

data.info()

# convert shipped_at, delivered_at, and returned_at into datetime
data['shipped_at'] = pd.to_datetime(data['shipped_at'])
data['delivered_at'] = pd.to_datetime(data['delivered_at'])
data['returned_at'] = pd.to_datetime(data['returned_at'])

data.info()

data.describe()

data.describe()

data.head().sort_values('order_id')

# take a look at each column type and number of null values
data_info = pd.DataFrame(data.dtypes).T.rename(index={0:'column type'})
data_info = data_info.append(pd.DataFrame(data.isnull().sum()).T.rename(index={0:'null values in number'}))
data_info = data_info.append(pd.DataFrame(data.isnull().sum()/data.shape[0]*100).T.rename(index={0:'null values in percent'}))
data_info

"""from data_info above, we can see that:
*   shipped_at contains 34.9% null values
*   delivered_at contains 65% null values
*   returned_at 90% null values
*   name contains 12 null values
*   brand contains 143 null values
"""

# Replace NaN with 0
data['shipped_at'] = data['shipped_at'].fillna(0)
data['delivered_at'] = data['delivered_at'].fillna(0)
data['returned_at'] = data['returned_at'].fillna(0)

# Delete null values in brand and name 
data = data.dropna(axis=0)

# Check again data info and null values
# take a look at each column type and number of null values
data.isnull().sum()

sns.boxplot(data['order_id'])

sns.boxplot(data['user_id'])

sns.boxplot(data['product_id'])

sns.boxplot(data['sale_price'])

sns.boxplot(data['num_of_item'])

sns.boxplot(data['cost'])

"""### Add New Columns"""

# Add total_revenue column
data['total_revenue'] = data['sale_price'] * data['num_of_item']

# Add total_cost column
data['total_costs'] = data['cost'] * data['num_of_item']

# Add revenue column
data['profit'] = data['total_revenue'] - data['total_costs']

data.head()

data.describe()

"""# 2. Data Preparation

### First, take a look at correlation of each variable
"""

corr = data.corr()
plt.figure(figsize=(10, 5))
sns.heatmap(corr, vmin=-1, vmax=1, cmap = "coolwarm", annot=True, annot_kws={"size":8}, fmt='.2f', linewidths=0.1, square = True)
plt.title("Korelasi Antar Variabel")
plt.show()

"""### How long is the period in days?"""

print("Datafile starts with timepoint {}".format(data.created_at.min()))
print("Datafile ends with timepoint {}".format(data.created_at.max()))

"""### How many different order, user, and product do we have?"""

# unique order
n_order = data['order_id'].nunique()
print('Number of order placed in The Look:', n_order, 'out of 180.508 rows')

# Unique user
n_user = data['user_id'].nunique()
print('Number of user placed an order or orders in The Look:', n_user, 'out of 180.508 rows')

# Unique product
n_product = data['product_id'].nunique()
print('Number of product in The Look:', n_product, 'out of 180.508 rows')

"""From above, we can conclude that:
1. 1 user_id, could place more than 1 order_id
2. 1 order_id, could place more than 1 product_id
3. 1 order_id, could be created by user at different times
4. Every order_id have 1 status

### Which user are most common?
"""

user_id_counts = data.user_id.value_counts().sort_values(ascending=False).iloc[0:20] 
plt.figure(figsize=(20,5))
sns.barplot(user_id_counts.index, user_id_counts.values, order=user_id_counts.index)
plt.ylabel("Counts")
plt.xlabel("user_id")
plt.title("Which users are most common?");
#plt.xticks(rotation=90);

"""### Which product_id are most common?"""

product_id_counts = data.product_id.value_counts().sort_values(ascending=False)
fig, ax = plt.subplots(2,1,figsize=(20,15))
sns.barplot(product_id_counts.iloc[0:20].index,
            product_id_counts.iloc[0:20].values,
            ax = ax[0], palette="Set1")
ax[0].set_ylabel("counts")
ax[0].set_xlabel("product_id")
ax[0].set_title("Which product_id are most common?");
sns.distplot(np.round(product_id_counts/data.shape[0]*100,2),
             kde=False,
             bins=20,
             ax=ax[1], color="Orange")
ax[1].set_title("How seldom are product_id?")
ax[1].set_xlabel("% of data with this product_id")
ax[1].set_ylabel("Frequency");

"""### How many status do we have?"""

# Status in The Look 
n_status = data['status'].nunique()
print('There is', n_status, 'status in The Look sales processing. It contains:', pd.unique(data['status']))

status_counts = data.status.value_counts().sort_values(ascending=False)
fig, ax = plt.subplots(2,1,figsize=(20,15))
sns.barplot(status_counts.iloc[0:20].values,
            status_counts.iloc[0:20].index,
            ax = ax[0], palette="Set1")
ax[0].set_ylabel("Status")
ax[0].set_xlabel("Counts")
ax[0].set_title("Which status are most common?");

"""### How various the sale price?

"""

# How many item could in a row?
max_sale_price = max(data['sale_price'])
print('The most expensive price of products is:', max_sale_price)

# The least amount of item could in a row?
min_sale_price = min(data['sale_price'])
print('The mcheapest price of product is:', min_sale_price)

sale_price_counts = data.sale_price.value_counts().sort_values(ascending=False).T
fig, ax = plt.subplots(2,1,figsize=(20,15))
sns.barplot(sale_price_counts.iloc[0:20].values,
            sale_price_counts.iloc[0:20].index,
            ax = ax[0], palette="Set1")
ax[0].set_ylabel("sale_price")
ax[0].set_xlabel("counts")
ax[0].set_title("Which sale_price are most common?");
sns.distplot(np.round(sale_price_counts/data.shape[0]*100,2),
             kde=False,
             bins=20,
             ax=ax[1], color="Orange")
ax[1].set_title("How seldom are sale_price?")
ax[1].set_xlabel("% of data with this sale_price")
ax[1].set_ylabel("Frequency");

"""### How many gender do we have?"""

# Gender in The Look
n_gender = data['gender'].nunique()
print('There is', n_gender, 'gender in The Look sales processing. It contains:', pd.unique(data['gender']))

gender_counts = data.gender.value_counts().sort_values(ascending=False).T
fig, ax = plt.subplots(2,1,figsize=(20,15))
sns.barplot(gender_counts.iloc[0:20].values,
            gender_counts.iloc[0:20].index,
            ax = ax[0], palette="Set1")
ax[0].set_ylabel("Gender")
ax[0].set_xlabel("Counts")
ax[0].set_title("Which gender are most common?");

"""### How many number of item, user do usually buy?"""

n_num_of_item = data['num_of_item'].nunique()
print('There is', n_num_of_item, 'number of number of item in The Look sales processing.')

"""### Max and Min Number of Item"""

# Max Number of Item
max_num_of_item = max(data['num_of_item'])
print('The highest number of item in a row is:', max_num_of_item)

# Min Number of Item
min_num_of_item = min(data['num_of_item'])
print('The least number of item in a row is:', min_num_of_item)

"""### Max and Min Cost of Product"""

# Max Cost of Product
max_cost = max(data['cost'])
print('The most expensive cost of products is:', max_cost)

# Min Cost of Product
min_cost = min(data['cost'])
print('The most cheapest cost of product is:', min_cost)

"""### Which category is the most common among user?"""

category_counts = data.category.value_counts().sort_values(ascending=False).T
fig, ax = plt.subplots(2,1,figsize=(20,15))
sns.barplot(category_counts.iloc[0:20].values,
            category_counts.iloc[0:20].index,
            ax = ax[0], palette="Set1")
ax[0].set_ylabel("Category")
ax[0].set_xlabel("Counts")
ax[0].set_title("Which category are most common?");
sns.distplot(np.round(category_counts/data.shape[0]*100,2),
             kde=False,
             bins=20,
             ax=ax[1], color="Orange")
ax[1].set_title("How seldom are category?")
ax[1].set_xlabel("% of data with this category")
ax[1].set_ylabel("Frequency");

"""### Which brand is the most common among user?"""

brand_counts = data.brand.value_counts().sort_values(ascending=False).T
fig, ax = plt.subplots(2,1,figsize=(20,15))
sns.barplot(brand_counts.iloc[0:20].values,
            brand_counts.iloc[0:20].index,
            ax = ax[0], palette="Set1")
ax[0].set_ylabel("Brand")
ax[0].set_xlabel("Counts")
ax[0].set_title("Which brand are most common?");
sns.distplot(np.round(category_counts/data.shape[0]*100,2),
             kde=False,
             bins=20,
             ax=ax[1], color="Orange")
ax[1].set_title("How seldom are brand?")
ax[1].set_xlabel("% of data with this brand")
ax[1].set_ylabel("Frequency");

"""### Which name is the most common among user?"""

name_counts = data.name.value_counts().sort_values(ascending=False).T
fig, ax = plt.subplots(2,1,figsize=(20,15))
sns.barplot(name_counts.iloc[0:20].values,
            name_counts.iloc[0:20].index,
            ax = ax[0], palette="Set1")
ax[0].set_ylabel("Name")
ax[0].set_xlabel("Counts")
ax[0].set_title("Which brand are most common?");
sns.distplot(np.round(name_counts/data.shape[0]*100,2),
             kde=False,
             bins=20,
             ax=ax[1], color="Orange")
ax[1].set_title("How seldom are name?")
ax[1].set_xlabel("% of data with this name")
ax[1].set_ylabel("Frequency");

"""### Highest and Lowest Profit"""

# Highest Profit
max_profit = max(data['profit'])
print('The most expensive cost of products is:', max_profit)

# Lowest Profit
min_profit = min(data['profit'])
print('The most cheapest cost of product is:', min_profit)

# Highest Revenue
max_revenue = max(data['total_revenue'])
print('Highest revenue is:', max_revenue)

# Lowest Revenue
min_revenue = min(data['total_revenue'])
print('Lowest revenue:', min_revenue)

from sklearn.preprocessing import LabelEncoder

labelencoder = LabelEncoder()

# Assigning numerical values and storing in another column
data['status'] = labelencoder.fit_transform(data['status'])
data['gender'] = labelencoder.fit_transform(data['gender'])
data['category'] = labelencoder.fit_transform(data['category'])
data['name'] = labelencoder.fit_transform(data['name'])
data['brand'] = labelencoder.fit_transform(data['brand'])

"""### Converting datetime to Year, Quarter, Month, Week, Weekday, Day, DayofYear"""

data['created_at'] = pd.to_datetime(data.created_at, format='%Y-%m-%d %H:%M:%S')

data["Year"] = data.created_at.dt.year
data["Quarter"] = data.created_at.dt.quarter
data["Month"] = data.created_at.dt.month
data["Week"] = data.created_at.dt.week
data["Weekday"] = data.created_at.dt.weekday
data["Day"] = data.created_at.dt.day
data["Dayofyear"] = data.created_at.dt.dayofyear
data["Hour"] = data.created_at.dt.hour
data["Date"] = pd.to_datetime(data[['Year', 'Month', 'Day']])

# Add total_revenue column
data['total_revenue'] = data['sale_price'] * data['num_of_item']

# Add total_cost column
data['total_costs'] = data['cost'] * data['num_of_item']

# Add revenue column
data['profit'] = data['total_revenue'] - data['total_costs']

data.head()

data.to_csv('sales_new.csv')

from google.colab import files
data.to_csv('sales_new.csv')
files.download('sales_new.csv')

"""### Analysing sales (total_revenue) over time

As we can see, every created_at has it's own timestamp (definitely based on time the order was made). We can resample time data by, for example weeks, and try see if there is any patterns in our sales.
"""

sns.lineplot(x=data.groupby(data.index).mean()['Year'],
             y=data.groupby(data.index).mean()['total_revenue'])

sns.lineplot(x=data.groupby(data.index).mean()['Quarter'],
             y=data.groupby(data.index).mean()['total_revenue'])

sns.lineplot(x=data.groupby(data.index).mean()['Month'],
             y=data.groupby(data.index).mean()['total_revenue'])

sns.lineplot(x=data.groupby(data.index).mean()['Week'],
             y=data.groupby(data.index).mean()['total_revenue'])

sns.lineplot(x=data.groupby(data.index).mean()['Weekday'],
             y=data.groupby(data.index).mean()['total_revenue'])

sns.lineplot(x=data.groupby(data.index).mean()['Day'],
             y=data.groupby(data.index).mean()['total_revenue'])

sns.lineplot(x=data.groupby(data.index).mean()['Dayofyear'],
             y=data.groupby(data.index).mean()['total_revenue'])

sns.lineplot(x=data.groupby(data.index).mean()['Hour'],
             y=data.groupby(data.index).mean()['total_revenue'])

"""# 3. Modelling with Prophet"""

! pip install prophet

from fbprophet import Prophet

from sklearn.metrics import mean_squared_error, mean_absolute_error

plt.style.use('fivethirtyeight') # for plots

"""### Focus on daily product sales

#### As we like to product the daily amount of product sales, we need to compute a daily aggregation of this data. FOr this purpose we need to extract temporal features out of the created_at.

So, we have to split our data into train-test data to be able to tain our model and validate its capabilities.
"""

data.Date.min()

data.Date.max()

data.head()

def create_features(data, label=None):
  X = data[["Year", "Quarter", "Month", "Week", "Weekday",
            "Day", "Dayofyear", "Hour"]]
  if label:
    y = data[label]
    return X, y
  return X

X, y = create_features(data, label='total_revenue')

features_and_target = pd.concat([X, y], axis=1)

# See our features and target
features_and_target.head()

features_and_target.info()

# Create sales table for forecasting
sales = data.loc[:, {'Date': 'ds',
                    'total_revenue': 'y'}]
sales = sales.set_index(['Date'])
sales = sales.sort_index()
sales = sales.groupby('Date').sum()

sales.head()

sales.tail()

sales.info()

# Color pallete for plotting
color_pal = ["#F8766D", "#D39200", "#93AA00",
             "#00BA38", "#00C19F", "#00B9E3",
             "#619CFF", "#DB72FB"]
sales.plot(style='.', figsize=(15,5), color=color_pal[0], title='Sales')
plt.show()

"""## Train/Test Split"""

sales.index.min()

sales.index.max()

train_size = int(len(sales.index) * 0.8)
train, test = sales[0:train_size], sales[train_size:len(sales.index)]

print('The length of observation is', len(sales.index))
print('The length of training set is', len(train))
print('The length of test set is', len(test))

split_date = sales.index[989]
split_date

sales_train = sales.loc[sales.index <= split_date].copy()
sales_test = sales.loc[sales.index > split_date].copy()

print('The length of training set is', len(sales_train))
print('The length of test set is', len(sales_test))

sales_train.info()

# Plot train and test so you can see where we have split
sales_test \
    .rename(columns={'total_revenue': 'TEST SET'}) \
    .join(sales_train.rename(columns={'total_revenue': 'TRAINING SET'}),
          how='outer') \
    .plot(figsize=(15,5), title='Sales', style='.')
plt.show()

"""## Prophet Modelling"""

# Format data for prophet model using ds and y
sales_train.reset_index() \
    .rename(columns={'Date':'ds',
                     'total_revenue':'y'}).head()

# Setup and train model and fit
model = Prophet(interval_width=0.95)
model.fit(sales.reset_index() \
              .rename(columns={'Date':'ds',
                               'total_revenue':'y'}))

# Predict on training set with model
sales_test_fcst = model.predict(df=sales_test.reset_index() \
                                   .rename(columns={'Date':'ds'}))

# Plot the forecast
f, ax = plt.subplots(1)
f.set_figheight(5)
f.set_figwidth(15)
fig = model.plot(sales_test_fcst,
                 ax=ax)
plt.show()

# Plot the components of the model
fig = model.plot_components(sales_test_fcst)

"""### Compare Forecast to Actuals"""

# Plot the forecast with the actuals
f, ax = plt.subplots(1)
f.set_figheight(5)
f.set_figwidth(15)
ax.scatter(sales_test.index, sales_test['total_revenue'], color='r')
fig = model.plot(sales_test_fcst, ax=ax)

"""Black dots: Actuals train set, 
Red dots: Actuals test set, 
Blue line: Forecast test set


"""

# dataframe that extends into future 12 months
future_dates = model.make_future_dataframe(periods = 12, freq='M')
print('First week to forecast.')
future_dates.tail()

future_dates.head()

# predictions
forecast = model.predict(future_dates)

# predictions for last week
forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail(7)

fc = forecast[['ds', 'yhat']].rename(columns = {'Date': 'ds', 'Forecast': 'yhat'})
fc.head()

# visualizing predictions
sales_forecast = model.plot(forecast);

model.plot_components(forecast)

"""## Error Metrics"""

mean_squared_error(y_true=sales_test['total_revenue'],
                   y_pred=sales_test_fcst['yhat'])

mean_absolute_error(y_true=sales_test['total_revenue'],
                   y_pred=sales_test_fcst['yhat'])

def mean_absolute_percentage_error(y_true, y_pred): 
    """Calculates MAPE given y_true and y_pred"""
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

mean_absolute_percentage_error(y_true=sales_test['total_revenue'],
                   y_pred=sales_test_fcst['yhat'])

"""## Adding Holidays

Next we will see if adding holiday indicators will help the accuracy of the model. Prophet comes with a Holiday Effects parameter that can be provided to the model prior to training.

We will use the built in pandas USFederalHolidayCalendar to pull the list of holidays
"""

from pandas.tseries.holiday import USFederalHolidayCalendar as calendar

cal = calendar()
train_holidays = cal.holidays(start=sales_train.index.min(),
                              end=sales_train.index.max())
test_holidays = cal.holidays(start=sales_test.index.min(),
                             end=sales_test.index.max())

# Create a dataframe with holiday, ds columns
sales.index = pd.to_datetime(sales.index)

sales['date'] = sales.index.date
sales['is_holiday'] = sales.date.isin([d.date() for d in cal.holidays()])
holiday_df = sales.loc[sales['is_holiday']] \
    .reset_index() \
    .rename(columns={'Date':'ds'})
holiday_df['holiday'] = 'USFederalHoliday'
holiday_df = holiday_df.drop(['total_revenue','date','is_holiday'], axis=1)
holiday_df.head()

# Setup and train model with holidays
model_with_holidays = Prophet(holidays=holiday_df)
model_with_holidays.fit(sales_train.reset_index() \
                            .rename(columns={'Date':'ds',
                                             'total_revenue':'y'}))

"""### Predict with Holidays"""

# Predict on training set with model
sales_test_fcst_with_hols = \
    model_with_holidays.predict(df=sales_test.reset_index() \
                                    .rename(columns={'Date':'ds'}))

"""### Plot Holiday Effect"""

fig2 = model_with_holidays.plot_components(sales_test_fcst_with_hols)

"""### Error Metrics Holiday Added"""

mean_squared_error(y_true=sales_test['total_revenue'],
                   y_pred=sales_test_fcst_with_hols['yhat'])

mean_absolute_error(y_true=sales_test['total_revenue'],
                   y_pred=sales_test_fcst_with_hols['yhat'])

def mean_absolute_percentage_error(y_true, y_pred): 
    """Calculates MAPE given y_true and y_pred"""
    y_true, y_pred = np.array(y_true), np.array(y_pred)
    return np.mean(np.abs((y_true - y_pred) / y_true)) * 100

mean_absolute_percentage_error(y_true=sales_test['total_revenue'],
                   y_pred=sales_test_fcst_with_hols['yhat'])

"""The error getting worse, when the holiday is added.

### Cross Validation
"""

from fbprophet.diagnostics import cross_validation

sales.shape

cv = cross_validation(model, initial='900 days', period='90 days', horizon='30 days')

cv.head()

"""### Performance Metrics"""

from fbprophet.diagnostics import performance_metrics

sales_pm = performance_metrics(cv)

sales_pm

"""### Visualizing Performance Metrics"""

from fbprophet.plot import plot_cross_validation_metric

plot_cross_validation_metric(cv,metric='mape')

plot_cross_validation_metric(cv,metric='rmse')

plot_cross_validation_metric(cv,metric='mse')

plot_cross_validation_metric(cv,metric='mdape')

plot_cross_validation_metric(cv,metric='mae')

"""# Modelling with XGBoost"""

import xgboost as xgb
from xgboost import plot_importance, plot_tree
plt.style.use('fivethirtyeight')
from sklearn.model_selection import RandomizedSearchCV, GridSearchCV, train_test_split
from sklearn.model_selection import cross_val_score, KFold

sales = data.loc[:, {'Date': 'ds',
                    'total_revenue': 'y'}]
sales = sales.set_index(['Date'])
sales = sales.sort_index()
sales = sales.groupby('Date').sum()
sales

# Color pallete for plotting
color_pal = ["#F8766D", "#D39200", "#93AA00",
             "#00BA38", "#00C19F", "#00B9E3",
             "#619CFF", "#DB72FB"]
sales.plot(style='.', figsize=(15,5), color=color_pal[0], title='Sales')
plt.show()

"""### Train/Test Split"""

train_size = int(len(sales.index) * 0.8)
train, test = sales[0:train_size], sales[train_size:len(sales.index)]

print('The length of observation is', len(sales.index))
print('The length of training set is', len(train))
print('The length of test set is', len(test))

split_date = sales.index[989]
split_date

sales_train = sales.loc[sales.index <= split_date].copy()
sales_test = sales.loc[sales.index].copy()

print('The length of training set is', len(sales_train))
print('The length of test set is', len(sales_test))

sales_train.head()

sales_test.head()

def create_features(data, label=None):
  """
  Create time series features from datetime index
  """
  data["Date"] = data.index
  data["Year"] = data["Date"].dt.year
  data["Quarter"] = data["Date"].dt.quarter
  data["Month"] = data["Date"].dt.month
  data["Week"] = data["Date"].dt.week
  data["Weekday"] = data["Date"].dt.weekday
  data["Day"] = data["Date"].dt.day
  data["Dayofyear"] = data["Date"].dt.dayofyear
  data["Hour"] = data["Date"].dt.hour
  
  X = data[["Hour", "Quarter", "Month", "Year", "Dayofyear", 
            "Week", "Weekday", "Day"]]
  if label:
    y = data[label]
    return X, y
  return X

X_train, y_train = create_features(sales_train, label='total_revenue')
X_test, y_test = create_features(sales_test, label='total_revenue')

"""### XGBoost Modelling"""

reg = xgb.XGBRegressor(n_estimators=1000, max_depth=6, eta=0.1, subsample=0.7, colsample_bytree=0.8, learning_rate=0.1)
reg.fit(X_train, y_train,
        eval_set=[(X_train, y_train), (X_test, y_test)],
        early_stopping_rounds=10,
        verbose=False) # Change verbose to True if you want to see it train

score = reg.score(X_train, y_train)
print("Training score: ", score)

scores = cross_val_score(reg, X_train, y_train,cv=10)
print("Mean cross-validation score: %.2f" % scores.mean())

kfold = KFold(n_splits=10, shuffle=True)
kf_cv_scores = cross_val_score(reg, X_train, y_train, cv=kfold )
print("K-fold CV average score: %.2f" % kf_cv_scores.mean())

"""### Plot Feature Importance"""

feature_importance = plot_importance(reg, height=0.9)

"""#### Forecast on Test Set"""

sales_test['sales_prediction'] = reg.predict(X_test)

sales_all = pd.concat([sales_test, sales_train], sort=False)

sales_plot = sales_all[['total_revenue', 'sales_prediction']].plot(figsize=(15,5))

# Plot the forecast with the actuals
f, ax = plt.subplots(1)
f.set_figheight(5)
f.set_figwidth(15)
sales_plot1 = sales_all[['sales_prediction','total_revenue']].plot(ax=ax,
                                              style=['-','.'])
ax.set_xbound(lower='10-03-2021', upper='11-03-2021')
ax.set_ylim(0, 60000)
plot = plt.suptitle('October 2021 Forecast vs Actuals')

# Plot the forecast with the actuals
f, ax = plt.subplots(1)
f.set_figheight(5)
f.set_figwidth(15)
sales_plot2 = sales_all[['sales_prediction','total_revenue']].plot(ax=ax,
                                              style=['-','.'])
ax.set_xbound(lower='10-03-2021', upper='10-11-2021')
ax.set_ylim(0, 60000)
plot = plt.suptitle('First Week of October Forecast vs Actuals')

f, ax = plt.subplots(1)
f.set_figheight(5)
f.set_figwidth(15)
sales_plot3 = sales_all[['sales_prediction','total_revenue']].plot(ax=ax,
                                              style=['-','.'])
ax.set_ylim(0, 60000)
ax.set_xbound(lower='04-03-2022', upper='04-11-2022')
plot = plt.suptitle('First Week of April 2022 Forecast vs Actuals')

"""### Error Metrics on Test Set"""

mean_squared_error(y_true=sales_test['total_revenue'],
                   y_pred=sales_test['sales_prediction'])

mean_absolute_error(y_true=sales_test['total_revenue'],
                   y_pred=sales_test['sales_prediction'])

mean_absolute_percentage_error(y_true=sales_test['total_revenue'],
                   y_pred=sales_test['sales_prediction'])

"""### Look at Worst and Best Predicted Days"""

sales_test['error'] = sales_test['total_revenue'] - sales_test['sales_prediction']
sales_test['abs_error'] = sales_test['error'].apply(np.abs)
error_by_day = sales_test.groupby(['Year','Month','Day']) \
    .mean()[['total_revenue','sales_prediction','error','abs_error']]

# Over forecasted days
error_by_day.sort_values('error', ascending=True).head(10)

"""Over forecasted days:
1. June 6th 2022
2. October 14th 2021
"""

# Worst absolute predicted days
error_by_day.sort_values('abs_error', ascending=False).head(10)

# Best predicted days
error_by_day.sort_values('abs_error', ascending=True).head(10)

"""The best predicted days seem to be a lot of in October. """

f, ax = plt.subplots(1)
f.set_figheight(5)
f.set_figwidth(10)
error_plot = sales_all[['sales_prediction','total_revenue']].plot(ax=ax,
                                              style=['-','.'])
ax.set_ylim(0, 60000)
ax.set_xbound(lower='05-31-2021', upper='06-30-2021')
plot = plt.suptitle('May 31, 2021 - Worst Predicted Day')

f, ax = plt.subplots(1)
f.set_figheight(5)
f.set_figwidth(10)
best_predicted_day = sales_all[['sales_prediction','total_revenue']].plot(ax=ax,
                                              style=['-','.'])
ax.set_ylim(0, 60000)
ax.set_xbound(lower='10-08-2021', upper='11-08-2021')
plot = plt.suptitle('October 8th, 2021 - Best Predicted Day')

f, ax = plt.subplots(1)
f.set_figheight(5)
f.set_figwidth(10)
best_predicted_day = sales_all[['sales_prediction','total_revenue']].plot(ax=ax,
                                              style=['-','.'])
ax.set_ylim(0, 60000)
ax.set_xbound(lower='10-31-2021', upper='11-30-2021')
plot = plt.suptitle('October 31th, 2021 - Best Predicted Day')

"""# Conclusion

Based on Modelling forecast using XGBoost and Prophet. We can conclude that Prophet modelling is way better than XGBoost. As we can see that Prophet MAPE score is: 14.18%, while XGBoost MAPE is: 26.73%.

Therefore, the valid forecast for The Look Sales Prediction is forecast using Prophet.
"""