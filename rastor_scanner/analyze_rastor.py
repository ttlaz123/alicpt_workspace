import csv
from PIL.Image import new
import matplotlib
from sklearn.datasets import make_regression
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
from sklearn.linear_model import LinearRegression
from scipy.interpolate import interp1d 
import pandas as pd
import os
import argparse
def find_differences(readings):
    #readings is a list
    differences = []

    for i in range(1, len(readings)):
        differences.append(float(readings[i])-float(readings[i-1]))

    print('Differences: ' + str(differences))

    return differences

def perform_rastor_interpolation(x_pos, x_times, y_pos, y_times, volts, v_times, min_y, max_y, min_x, max_x):
    '''
    produces a function that provides times as a function of x and y
    assumes the data is split into specific chunks
    x_pos scans up and down while y_pos shifts one at a time
    assumes we start at y = min_y
    '''
    y_pos = np.round(y_pos, decimals=2)
    x_pos = np.round(x_pos, decimals=2)

    x_range = max_x-min_x 
    y_range = max_y-min_y 
    print('Minimum (x,y): (' + str(min_x) + ', ' + str(min_y) + ')')
    print('Maximum (x,y): (' + str(max_x) + ', ' + str(max_y) + ')')
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
    #print('y_dict: ' + str(y_dict))
    print('y_dict keys: ' + str(y_dict.keys()))
    for y in range(min_y, max_y):
        #print('processing y = ' +str(y))
        #print('y_dict[y] = ' + str(y_dict[y]))
        if y not in y_dict:
            continue
        y_indices = y_dict[y]
        
        ts = [y_times[i] for i in y_indices]
        min_t = min(ts)
        max_t = max(ts)
        #print(min_t)
        #print(max_t)

        while(x_times[x_count] < min_t):
            x_count += 1

        lower_x_bound = x_count 

        #print("min x_count:")
        #print(x_count)

        while(x_times[x_count] < max_t):
            x_count += 1
        upper_x_bound = x_count + 1

        #print("max x_count:")
        #print(x_count)

        xs = x_pos[lower_x_bound: upper_x_bound+1]
        #print('min(xs)' + str(min(xs)))
        #print('max(xs)' + str(max(xs)))
        
        txs = x_times[lower_x_bound: upper_x_bound+1]
        interpx = interp1d(xs, txs)
        y_ind = y-min_y
        #print(y_ind)
        #for x in range(int(min(xs)), int(max(xs))):
        for x in range(min_x, max_x):
            #print(x)
            try:
                t = interpx(x)
            except ValueError:
                raise ValueError('Value x=' + str(x) + ' is outside of range: ' + str(min(xs)) + ' ' + str(max(xs)))
            rastor_t[x-min_x, y_ind] = t


    interpv = interp1d(v_times, volts)
    rastor = np.zeros((x_range, y_range))

    print('Completed 2D gridding')
    for x in range(x_range):
        for y in range(y_range):
            t = rastor_t[x,y]
            rastor[x,y] = interpv(t)

    return rastor

def matrix_to_list(rastor, max_v=9999, max_x=9999, min_x=-9999, min_y=-9999, max_y=9999):
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
    meas_rastor = convert_to_rastor(x_pos, y_pos, meas_volts, conv_factor=1/5)
    new_rastor = convert_to_rastor(x_pos, y_pos, new_volts, conv_factor=1/5)
    
    return new_volts, new_rastor, meas_rastor

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

def convert_to_rastor(x_pos, y_pos, volts, conv_factor=1):
    max_y = max(y_pos)
    max_x = max(x_pos)
    min_y = min(y_pos)
    min_x = min(x_pos)
    x_range = int(max_x-min_x)+1
    y_range = int(max_y-min_y)+1

    rastor = np.zeros((x_range, y_range))
    for i in range(len(x_pos)):
        rastor[int(x_pos[i]-min_x), int(y_pos[i]-min_y)] = volts[i] * conv_factor

    return rastor

def delete_empty_rows(file_path, new_file_path):
    data = pd.read_csv(file_path, skip_blank_lines=True)
    data.dropna(how="all", inplace=True)
    data.to_csv(new_file_path, header=True, index=False)

def read_files(folder = '.', prefix='front'):
    xfile = str(prefix) + '_x_pos.csv'
    yfile = str(prefix) + '_y_pos.csv'
    vfile = str(prefix) + '_volts.csv'
    x = pd.read_csv(os.path.join(folder, xfile))
    y = pd.read_csv(os.path.join(folder,yfile))
    v = pd.read_csv(os.path.join(folder,vfile))

    x_pos = list(x['x_pos'])
    x_times = list(x['x_pos times'])
    y_pos = list(y['y_pos'])
    y_times = list(y['y_pos times'])
    volts = list(v['volts'])
    v_times = list(v['nida reading times'])
    print('here')
    
    return x_pos, x_times, y_pos, y_times, volts, v_times

def show_scan(rastor, title, c_title, norm = None):
    plt.imshow(rastor, cmap = 'rainbow', norm = norm)
    cb = plt.colorbar()
    cb.set_label(c_title)
    plt.xlabel('Length (mm)')
    plt.ylabel('Width (mm)')
    plt.title(title)
    plt.show()

def main():
    #delete_empty_rows('x_pos.csv', 'x_pos_fixed.csv')
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--folder', default='.',
                        help='/path/to/folder where scans are stored')
    
    parser.add_argument('-p', '--prefix', default='front',
                        help='prefix of scan names')
    args = parser.parse_args()

    min_y = -125
    max_y = 135
    min_x = -120
    max_x = 145
    crop_max_v = 10
    crop_max_x = 240
    crop_min_x = 15
    crop_min_y = 15
    crop_max_y = 240
    x_pos, x_times, y_pos, y_times, volts, v_times = read_files(args.folder, args.prefix)
    rastor = perform_rastor_interpolation(x_pos, x_times, y_pos, y_times, volts, v_times, min_y, max_y, min_x, max_x)

    title = 'Before Cropping'
    scale_name = 'Heights (mm)'
    show_scan(rastor, title, scale_name)
    pos, volt_readings = matrix_to_list(rastor, max_v=crop_max_v, max_x=crop_max_x, min_x=crop_min_x, min_y=crop_min_y, max_y=crop_max_y)
    coeff, error = find_least_squares_regression(np.array(pos), np.array(volt_readings))
    pos_uncropped, volt_readings_uncropped = matrix_to_list(rastor)
    
    #Cropped Version:
    #new_volts, new_rastor, meas_rastor = subtract_plane(pos, volt_readings, coeff)
    
    #Uncropped Version:
    new_volts, new_rastor, meas_rastor = subtract_plane(pos_uncropped, volt_readings_uncropped, coeff)


    title = 'Raw Heights Topology Map'
    show_scan(meas_rastor, title , scale_name)

    scale_name = 'Height Deviation from Plane (mm)'
    title = 'Subtracted Plane Topology Map'

    vmin = -0.035
    vmax = 0.025
    show_scan(new_rastor, title ,scale_name, norm = matplotlib.colors.Normalize(vmin=vmin, vmax=vmax))
    return
    
if __name__ == '__main__':
    main()