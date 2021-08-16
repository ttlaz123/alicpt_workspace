import csv
from PIL.Image import new
from sklearn.datasets import make_regression
from matplotlib import pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
from scipy.interpolate import interp1d 


def find_differences(readings):
    #readings is a list
    differences = []

    for i in range(1, len(readings)):
        differences.append(float(readings[i])-float(readings[i-1]))

    print(differences)

    return differences

def find_least_squares_regression(pos, volt_readings):
    num_col = pos.shape[1]
    rank = np.linalg.matrix_rank(pos)

    U, sigma, VT = np.linalg.svd(pos, full_matrices=False)
    D_plus = np.diag(np.hstack([1/sigma[:rank], np.zeros(num_col-rank)]))
    V = VT.T
    X_plus = V.dot(D_plus).dot(U.T)
    coeff = X_plus.dot(volt_readings)

    #print("Least-squares solution (coefficients for equation):")
    #print(coeff)

    error = np.linalg.norm(pos.dot(coeff) - volt_readings, ord=2) ** 2

    #print("Error of least-squares solution:")
    #print(error)

    #Checking that this is the corrext answer
    #print(np.linalg.lstsq(pos, volt_readings))

    return coeff, error

def subtract_plane(pos, meas_volts, coeff):
    x_pos = []
    y_pos = []
    model_volts = []
    new_volts = []
    for p in pos:
        model_volts.append(coeff[0]*p[0] + coeff[1]*p[1] + coeff[2]*p[2])
        x_pos.append(p[0])
        y_pos.append(p[1])
    
    for i in range(len(model_volts)):
        new_volts.append(meas_volts[i]-model_volts[i])

    save_to_csv(x_pos, y_pos, new_volts)
    convert_to_rastor(x_pos, y_pos, new_volts)
    return new_volts

def save_to_csv(x_pos, y_pos, volts):
    #all inputs are lists
    fields = ['X Position', 'Y Position', 'Subtracted Volts']
    rows = []
    for i in range(len(x_pos) - 1):
        rows.append([x_pos[i], y_pos[i], volts[i]])
    
    with open('subtracted_rastorplotdata.csv', 'w') as out:
        csv_out = csv.writer(out)
        csv_out.writerow(fields)
        csv_out.writerows(rows)

    print("saved to csv")

def convert_to_rastor(x_pos, y_pos, volts):
    max_y = max(y_pos)
    max_x = max(x_pos)
    min_y = min(y_pos)
    min_x = min(x_pos)
    x_range = int(max_x-min_x)+1
    y_range = int(max_y-min_y)+1

    rastor = np.zeros((x_range, y_range))
    for i in range(len(x_pos)):
        rastor[int(x_pos[i]-min_x), int(y_pos[i]-min_y)] = volts[i]
    plt.imshow(rastor)
    plt.show()

def main():
    
    f = open('rastorplotdata.csv')
    csv_f = csv.reader(f)
    next(csv_f)

    pos = []
    x_pos = []
    y_pos = []
    volt_readings = []

    for row in csv_f:
        if row[0] == '':
            continue
        #pos.append([float(row[1]), float(row[3]), 1])
        x_pos.append(float(row[1]))
        y_pos.append(float(row[3]))
        volt_readings.append(float(row[5]))

    convert_to_rastor(x_pos, y_pos, volt_readings)
'''
    pos = np.array(list(filter(lambda x: (x != [None,None]), pos)))
    volt_readings = np.array(list(filter(None, volt_readings)))

    coeff, error = find_least_squares_regression(pos, volt_readings)

    new_volts = subtract_plane(pos, volt_readings, coeff)
    print("subtracted plane")
    '''
if __name__ == '__main__':
    main()