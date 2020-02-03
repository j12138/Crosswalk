from keras.models import load_model, Model
import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import time
import os, sys, glob
import argparse
import cv2
from tqdm import tqdm
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from ml.Models.loss import smoothL1

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def mae0(y_true, y_pred):
    return tf.keras.losses.mae(y_true[:,0], y_pred[:,0])

def mae1(y_true, y_pred):
    return tf.keras.losses.mae(y_true[:,1], y_pred[:,1])

def mse0(y_true, y_pred):
    return tf.keras.losses.mse(y_true[:,0], y_pred[:,0])

def mse1(y_true, y_pred):
    return tf.keras.losses.mse(y_true[:,1], y_pred[:,1])

def load_model(model_path):
    model_file = None
    for file in glob.glob(os.path.join(model_path, '*')):
        if file.split('.')[-1] == 'h5':
            print('Model found: {}'.format(file))
            model_file = file
            break
    
    if not model_file:
        print("There are no h5 model file")
        return

    custom_objects = {'smoothL1': smoothL1,
                      'mae0': mae0,
                      'mae1': mae1,
                      'mse0': mse0,
                      'mse1': mse1,}
    model = tf.keras.models.load_model(model_file, custom_objects=custom_objects)

    return model


def predict_by_model(xs, ys, model, verbose=False):
    predicts = []
    cnt = 0

    for i in tqdm(range(len(xs))):
        img = xs[i]
        cnt = cnt + 1
        t = time.time()
        predict = model.predict(np.expand_dims(img / 255.0, axis=0))
        predict = [[predict[0][0] * 2.0, predict[0][1] * 60.0]]
        predicts.append(predict)
            
    predicts = np.squeeze(np.asarray(predicts))

    return predicts


def main():
    pass


if __name__ == "__main__":
    main()