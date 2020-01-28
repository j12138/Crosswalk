from keras.models import load_model, Model
import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import time
import os, sys, glob
import argparse
import cv2
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from ml.Models.loss import smoothL1

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

'''
parser = argparse.ArgumentParser()
parser.add_argument('-e', '--eval_folder', help="path to folder of data to evaluate", 
                    default=os.path.join(BASE_DIR, './../labeling/npy/'))    
parser.add_argument('-m', '--model_path', help="path to model", 
                    default=os.path.join(BASE_DIR, './trainings/2020-jan7/MobileNetV2.h5'))
args = parser.parse_args()

#Load the data (change path as needed')
x_test=np.load(os.path.join(args.eval_folder, 'x.npy'))
y_test=np.load(os.path.join(args.eval_folder, 'y.npy')) #Truth


model = load_model(args.model_path, custom_objects = {'smoothL1':smoothL1}) 
print('Running Evaluation Now Please Wait')

outputs_test = []
inference_time = []
cnt = 0

for img in x_test:
    cnt = cnt + 1
    t = time.time()
    predict = model.predict(np.expand_dims(img / 255.0, axis=0))
    predict = [[predict[0][0] * 2.0, predict[0][1] * 60.0]]
    outputs_test.append(predict)
    inference_time.append((1 / (time.time() - t)))
        
outputs_test = np.squeeze(np.asarray(outputs_test))
print('# of imgs : ', cnt)
print('--- prediction ---')
print(outputs_test)
print('----- Truth -----')
print(y_test)
inference_time = np.squeeze(np.asarray(inference_time))

print(model.metrics_names)
print(model.evaluate(x=x_test,
                     y=y_test,
                     batch_size=64,
                     verbose=0,
                     sample_weight=None,
                     steps=None))
'''

def model_evaluate(xs, ys, model_path, verbose=False):
    model_file = None
    for file in glob.glob(os.path.join(model_path, '*')):
        if file.split('.')[-1] == 'h5':
            print('Model found: {}'.format(file))
            model_file = file
            break
    
    if not model_file:
        print("There are no h5 model file")
        return

    model = tf.keras.models.load_model(model_file, custom_objects={'smoothL1': smoothL1})
    
    predicts = []
    cnt = 0

    for img in xs:
        cnt = cnt + 1
        t = time.time()
        predict = model.predict(np.expand_dims(img / 255.0, axis=0))
        predict = [[predict[0][0] * 2.0, predict[0][1] * 60.0]]
        predicts.append(predict)
            
    predicts = np.squeeze(np.asarray(predicts))
    # print(len(xs), len(ys), len(predicts))

    evals = []
    for i in range(len(xs)):
        eval = model.evaluate(x=np.asarray([xs[i]]),
                            y=np.asarray([ys[i]]),
                            batch_size=64,
                            verbose=0,
                            sample_weight=None,
                            steps=None)
        evals.append(eval)

    return predicts, evals


def main():
    pass


if __name__ == "__main__":
    main()