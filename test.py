from argparse import ArgumentParser
import torch
import os
import numpy as np
from scipy import integrate
from sklearn.metrics import mean_squared_error
from math import sqrt
import matplotlib.pyplot as plt

def data_process(file_name):
    f = open(file_name,'r')
    time_data = []
    file_data = f.readlines()
    f.close()
    for line in file_data:
        data = line.split(" ")
        a_list = []
        for i in range(len(data)):
            if data[i] != "\n":
                if (data[i]!=''):
                    a_list.append(float(data[i]))
        time_data.append(a_list)
    for i in range(len(time_data)):
        line = time_data[i]
        time_data[i] = []
        end = 1
        while end <= len(line):
            time_data[i].append(line[0:end])
            end += 1
    time_data = np.array(time_data)
    return time_data

def type_process(file_name):
    f = open(file_name,'r')
    time_data = []
    file_data = f.readlines()
    f.close()
    for line in file_data:
        data = line.split(" ")
        a_list = []
        for i in range(len(data)):
            if data[i] != "\n":
                if (data[i]!=''):
                    a_list.append(int(data[i]))
        time_data.append(a_list)
    for i in range(len(time_data)):
        line = time_data[i]
        time_data[i] = []
        end = 1
        while end <= len(line):
            time_data[i].append(line[0:end])
            end += 1
    time_data = np.array(time_data)
    return time_data

def equation(time_var, time_cif, w, b):
    time_guess = time_var*np.exp(time_cif+w*(time_var)+b+
                                 (np.exp(time_cif+b)-np.exp(time_cif+w*(time_var)+b))/w)
    return time_guess

def intensities(time_var, time_cif, w, b):
    ints = np.exp(time_cif+w*(time_var)+b)
    return ints

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--test_start",
                        help="Start of the prediction. For real data, we only predict the last one at -1",
                        type=int, default=56)
    config = parser.parse_args()

    if torch.cuda.is_available():
        device = torch.device('cuda')
        print("You are using GPU acceleration.")
        print("Number of CUDAs(cores): ", torch.cuda.device_count())
    else:
        device = torch.device("cpu")
        print("CUDA is not Available. You are using CPU only.")
        print("Number of cores: ", os.cpu_count())



    time_test = data_process("data/codtest_time.txt")
    type_test = type_process("data/codtest_event.txt")
    print("testing file processed.")


    #change this varible equal to the row on which we want to run the model
    indexed_row = 0
    
    time_test = time_test[indexed_row]
    type_test = type_test[indexed_row]

    model = torch.load("model.pt")

    index = 0

#    if config.test_start == -1:

#    else:
#        index = config.test_start



    actual_duration = []
    duration_pred = []
    intensity_pred = []
    event_pred = []
    while index < len(time_test):
        time_data = np.diff(time_test[index], axis=-1, prepend=time_test[0])
        actual_duration.append(time_data[-1])
        batch = (torch.tensor([time_data], dtype=torch.float32), torch.tensor([type_test[index]]))
        event, time_cif = model.predict(batch, device)
        time_cif = time_cif.item()
        intensity_w = model.intensity_w.item()
        intensity_b = model.intensity_b.item()
        func = lambda x: equation(x, time_cif, intensity_w, intensity_b)
        duration = integrate.quad(func,0, np.inf)[0]
        duration_pred.append(duration)
        inten = intensities(duration, time_cif, intensity_w, intensity_b)
        intensity_pred.append(inten)
        event_pred.append(event[0])
        index += 1

    print("prediction on duration: ", duration_pred)
    print("actual duration: ", actual_duration)
    print("prediction on types: ", event_pred)
    print("intensity: ",intensity_pred)
    print("calculating RMSE: ")
    rmse = sqrt(mean_squared_error(duration_pred, actual_duration))


    f = open("predict-duration.txt", "w")
    for t in duration_pred:
      f.write(str(t))
      f.write(" ")
    f.close()
    f = open("predict_type.txt", "w")
    for item in event_pred:
      f.write(str(item))
      f.write(" ")
    f.close()


    print("generating_time_interval_plot:")
    figure, ax = plt.subplots(2,2)
    ax[0,0].plot(range(100),actual_duration)
    ax[0,0].plot(range(100),duration_pred)
    ax[0,1].plot(range(100),intensity_pred)
    ax[1,0].bar(x=1, height=rmse)
    ax[1,0].annotate(str(round(rmse,3)),xy=[1, rmse])
    ax[1,1].set_visible(False)
    figure.tight_layout()
    plt.savefig("result.png")
