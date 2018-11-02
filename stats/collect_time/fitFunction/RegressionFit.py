from pandas import DataFrame
from sklearn import linear_model
import csv

result_file_path = 'results.csv'

Results = {
    'threads_number': [],
    'size': [],
    'collect_time': []
}
with open(result_file_path, 'r') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        Results['threads_number'].append(row['threads_number'])
        Results['size'].append(row['size'])
        Results['collect_time'].append(row['collect_time'])

df = DataFrame(Results, columns=['threads_number', 'size', 'collect_time'])

X = df[['threads_number',
        'size']]
Y = df['collect_time']

# with sklearn
regr = linear_model.LinearRegression()
regr.fit(X, Y)

print(regr.score(X, Y))
print('Intercept: \n', regr.intercept_)
print('Coefficients: \n', regr.coef_)

x = DataFrame
regr.predict()
