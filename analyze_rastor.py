import csv
from sklearn.datasets import make_regression
from matplotlib import pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression

f = open('edited_rastorplotdata.csv')
csv_f = csv.reader(f)
next(csv_f)

def find_differences(readings):
    #readings is a list
    differences = []

    for i in range(1, len(readings)):
        differences.append(float(readings[i])-float(readings[i-1]))

    print(differences)

    return differences

def main():
    volt_readings = []

    for row in csv_f:
        volt_readings.append(row[5])

    volt_readings = list(filter(None, volt_readings))

    differences = find_differences(volt_readings)

if __name__ == '__main__':
    main()