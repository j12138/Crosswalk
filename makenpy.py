import numpy as np
import cv2
import csv


train_files = []
y_train = []
cv2.namedWindow('tool')

with open('annotation.csv', 'r') as reader:
    data = reader.read()
    lines = data.strip().split('\n')
    
    for line in lines:
        if line != 'path,loc,ang':
            info = line.split(',')
            print(info)

            img = cv2.imread(info[0])
            loc = float(info[1])
            ang = float(info[2])
            train_files.append(img)
            y_train.append([loc, ang])
            
size = len(train_files)
test_size = int(size/5)
np.save('./preprocessed_data/train/X.npy', train_files)
np.save('./preprocessed_data/train/Y.npy', y_train)
np.save('./preprocessed_data/test/X.npy', train_files[size-test_size:])
np.save('./preprocessed_data/test/Y.npy', y_train[size-test_size:])