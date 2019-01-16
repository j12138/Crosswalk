import numpy as np
import cv2
import csv


train_files = []
y_train = [] # labels

with open('annotation.csv', 'r') as reader:
    data = reader.read()
    lines = data.strip().split('\n')
    
    for line in lines:
        if line != 'path,loc,ang':
            info = line.split(',')
            
            try:
                img = cv2.imread(info[0])
                cv2.namedWindow('tool')
                cv2.imshow('tool', img)
            except :
                print(info[0])
                continue

            print(info)
            loc = float(info[1])
            ang = float(info[2])/90.0
            train_files.append(img)
            y_train.append([loc, ang])
            
#print(train_files)
#print(y_train)

size = len(train_files)
test_size = int(size/6)
np.save('./preprocessed_data/train/X.npy', train_files[test_size:])
np.save('./preprocessed_data/train/Y.npy', y_train[test_size:])
np.save('./preprocessed_data/test/X.npy', train_files[:test_size])
np.save('./preprocessed_data/test/Y.npy', y_train[:test_size])