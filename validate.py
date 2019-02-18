#evaluate 1 image for validation
from keras.models import load_model 
import numpy as np
import matplotlib.pyplot as plt 
from Models.loss import smoothL1
import time
import argparse
import cv2
import yaml

def parse_args(options):
    # python preprocess.py data --w 300 --h 240
    parser = argparse.ArgumentParser()
    #parser.add_argument('data_path', help = 'Path of folder containing images', type = str)
    parser.add_argument('-m', '--model_path', help="path to model", 
                    default='./trainings/Crosswalk_guide/SimpleModel.h5')
    parser.add_argument('-d', '--db_file', dest = 'db_file', default = options['db_file'], type = str)

    return parser.parse_args()

def loadyaml():
    with open('./config.yaml', 'r') as stream: 
        options = yaml.load(stream)
    return options

def load_validation_data():
    #TODO: change filename to input arguments
    #NOTE: Q. raw img or preprocessed img ??
    x_val=np.load('./X.npy')
    y_val=np.load('./Y.npy')
    return x_val, y_val

def load_our_model(model_path):
    model=load_model(model_path,custom_objects={'smoothL1':smoothL1}) 
    print('Running Evaluation Now Please Wait')
    return model

def scale_back_labels(label):
    return [format(label[0], '.3f'), format(label[1]*90.0, '.3f')]

def evaluate_by_model(model, x_val, y_val):
    outputs_test=[]
    cnt = 0
    cv2.namedWindow('validation')

    for img in x_val:
        cnt = cnt + 1
        prediction = model.predict(np.expand_dims(img/255.0,axis=0))
        outputs_test.append(prediction)
        scaled_prediction = scale_back_labels(prediction[0])

        print('Truth : ', y_val[cnt])
        print('Prediction : ', scaled_prediction)

        while True:
            cv2.imshow('validation', img)
            if cv2.waitKey(10) == 32:
                break # press 'spacebar' -> turn to next image


def main():
    options = loadyaml()
    args = parse_args(options)
    x_val, y_val = load_validation_data()
    model = load_our_model(args.model_path)
    evaluate_by_model(model, x_val, y_val)

if __name__ == '__main__':
    main()