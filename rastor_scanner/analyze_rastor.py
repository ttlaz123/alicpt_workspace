import csv
from PIL.Image import new
from sklearn.datasets import make_regression
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
from scipy.interpolate import interp1d 
import pandas as pd

def find_differences(readings):
    #readings is a list
    differences = []

    for i in range(1, len(readings)):
        differences.append(float(readings[i])-float(readings[i-1]))

    print(differences)

    return differences

def perform_rastor_interpolation(x_pos, x_times, y_pos, y_times, volts, v_times):
    '''
    produces a function that provides times as a function of x and y
    assumes the data is split into specific chunks
    x_pos scans up and down while y_pos shifts one at a time
    assumes we start at y = min_y
    '''
    y_pos = np.round(y_pos, decimals=2)
    x_pos = np.round(x_pos, decimals=2)

    min_y = int(min(y_pos))
    max_y = int(max(y_pos))
    min_x = int(min(x_pos))
    max_x = int(max(x_pos))

    x_range = max_x-min_x 
    y_range = max_y-min_y 
    print(min_y)
    print(max_y)
    print(min_x)
    print(max_x)
    rastor_t = np.zeros((x_range, y_range))

    y_dict = {}
    for i in range(len(y_pos)):
        y = y_pos[i]
        if(y == int(y)):
            if(y in y_dict):
                y_dict[y].append(i)
            else:
                y_dict[y] = [i]

    x_count = 0
    for y in range(min_y, max_y):
        #print('processing y = ' +str(y))
        y_indices = y_dict[y]
        
        ts = [y_times[i] for i in y_indices]
        min_t = min(ts)
        max_t = max(ts)
        #print(min_t)
        #print(max_t)

        while(x_times[x_count] < min_t):
            x_count += 1

        lower_x_bound = x_count 
        while(x_times[x_count] < max_t):
            x_count += 1
        upper_x_bound = x_count + 1

        xs = x_pos[lower_x_bound: upper_x_bound+1]
        #print(min(xs))
        #print(max(xs))
        
        txs = x_times[lower_x_bound: upper_x_bound+1]
        interpx = interp1d(xs, txs)
        y_ind = y-min_y
        #print(y_ind)
        for x in range(min_x, max_x ):
            t = interpx(x)
            rastor_t[x-min_x, y_ind] = t
    
               
    #plt.imshow(rastor_t)
    #plt.show()

    interpv = interp1d(v_times, volts)
    rastor = np.zeros((x_range, y_range))

    print('completed 2d gridding')
    for x in range(x_range):
        for y in range(y_range):
            t = rastor_t[x,y]
            rastor[x,y] = interpv(t)
    plt.imshow(rastor)
    plt.show()
    return rastor

def matrix_to_list(rastor, max_v=5, max_x=200, min_x=10, min_y=5, max_y=210):
    shape = rastor.shape
    pos = []
    volt_readings = []
    for x in range(shape[0]):
        if x > max_x or x < min_x:
            continue
        for y in range(shape[1]):
            v = rastor[x,y]
            if v >= max_v:
                continue
            if y > max_y or y < min_y:
                continue
            pos.append([x,y,1])
            volt_readings.append(v)
    return pos, volt_readings

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

def delete_empty_rows(file_path, new_file_path):
    data = pd.read_csv(file_path, skip_blank_lines=True)
    data.dropna(how="all", inplace=True)
    data.to_csv(new_file_path, header=True, index=False)

def read_files():
    xfile = 'x_pos_fixed.csv'
    yfile = 'y_pos_fixed.csv'
    vfile = 'volts_fixed.csv'
    x = pd.read_csv(xfile)
    y = pd.read_csv(yfile)
    v = pd.read_csv(vfile)

    x_pos = list(x['x_pos'])
    x_times = list(x['x_pos times'])
    y_pos = list(y['y_pos'])
    y_times = list(y['y_pos times'])
    volts = list(v['volts'])
    v_times = list(v['nida reading times'])
    print('here')
    
    return x_pos, x_times, y_pos, y_times, volts, v_times


def main():
    #delete_empty_rows('x_pos.csv', 'x_pos_fixed.csv')
    x_pos, x_times, y_pos, y_times, volts, v_times = read_files()
    rastor = perform_rastor_interpolation(x_pos, x_times, y_pos, y_times, volts, v_times)
    pos, volt_readings = matrix_to_list(rastor)
    coeff, error = find_least_squares_regression(np.array(pos), np.array(volt_readings))
    new_volts = subtract_plane(pos, volt_readings, coeff)
    return
    
if __name__ == '__main__':
    main()