from argparse import ArgumentParser
import torch
import os
import model
import random
import numpy as np




def data_process(file_name):
#change the length of training sequence here
    seq_len = 10
#change length of training sequence here
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
        end = seq_len
        while end <= len(line):
            start = end-seq_len
            time_data[i].append(np.array(line[start:end]))
            end += 1
    time_data = np.array(time_data)

    time_duration = np.diff(time_data, axis=-1, prepend=time_data[:,:,:1])
    return time_data, time_duration

def type_process(file_name):
#change the length of training sequence here
    seq_len = 10
#change length of training sequence here
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
        end = seq_len
        while end <= len(line):
            start = end-seq_len
            time_data[i].append(np.array(line[start:end]))
            end += 1
    type_data = np.array(time_data)
    return type_data

if __name__ == "__main__":
    """The code below is used to set up command line inputs. """
    parser = ArgumentParser()
    parser.add_argument("--n_class",
                        help="Number of types in the dataset, default is 2", type=int, default=6)
    parser.add_argument("--hid_dim", type=int, default=1)
    parser.add_argument("--n_layers", type=int, default=1)
    parser.add_argument("--lr", type=float, default=0.01)
    parser.add_argument("--momentum", type=float, default=0.01)
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--opt", type=str, default='Adam')
    parser.add_argument("--read_model", type=bool, default=False)
    parser.add_argument("--seq_len", type=int, default=10)

    config = parser.parse_args()


    """The code below is to get the training data"""
    time_train, time_duration = data_process('data/cod_time.txt')
    type_data = type_process("data/cod_event.txt")

    print("training file processed.")


    """The code below is used to set up customized training device on computer"""
    if torch.cuda.is_available():
        device = torch.device('cuda')
        print("You are using GPU acceleration.")
        print("Number of CUDAs(cores): ", torch.cuda.device_count())
    else:
        device = torch.device("cpu")
        print("CUDA is not Available. You are using CPU only.")
        print("Number of cores: ", os.cpu_count())


    """decide whether to used pred-trained model to train again"""
    if config.read_model:
        model = torch.load("model.pt")
    else:
        model = model.RMTPP(config, device)
        for parameter in model.parameters():
            parameter.data.fill_(random.uniform(0.4, 0.5))


    """Trianing process"""
    for epc in range(config.epochs):
        c = list(zip(time_train, type_data))
        random.shuffle(c)
        time_train, type_data = zip(*c)
        loss_total = 0
        loss_type = 0
        loss_time = 0
        for index in range(len(time_train)):
            batch = (torch.tensor(time_duration[index], dtype=torch.float32), torch.tensor(type_data[index]))
            loss, loss1, loss2 = model.train(batch, device)
            loss_total += loss
            loss_type += loss1
            loss_time += loss2
        print("In epochs {0}, total loss: {1}, type loss: {2}, time loss: {3}".format(
            epc, loss_total/len(time_train), loss_type/len(time_train), loss_time/len(time_train)
        ))
        print("saving model")
        torch.save(model, "model.pt")
    print("training done!")