"""
Batoners Inc.

Jan 2019
"""

import tensorflow as tf
import numpy as np
from keras.callbacks import ModelCheckpoint, TensorBoard, CSVLogger, LearningRateScheduler
from keras.optimizers import SGD, Adam
import yaml
import os
from shutil import copyfile

import argparse
from Models.Simplified import SimpleModel
from Models.loss import smoothL1
from Generator.augmentation import BatchGenerator

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(BASE_DIR, "..", "..")
config_file = os.path.join(BASE_DIR, 'config.yaml')


def parse_args():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    return args


#Load the training config file
def loadyaml(filename):
    with open(filename, 'r') as stream: 
        options = yaml.load(stream)
    return options


def select_npy_data(npy_log_file):
    with open(npy_log_file, "r") as f:
        lines = f.readlines()
        cnt = 0

        print('\n---------- npy list ----------')
        for line in lines:
            cnt = cnt + 1
            print('['+str(cnt)+']', line.strip())
            pass
        print('------------------------------')
        
        picked_num = input('select npy: ')
        picked_npy_file = (lines[int(picked_num) - 1].split('\t'))[0]
        print(picked_npy_file)

        x_npy = './npy/' + picked_npy_file + '_X.npy'
        y_npy = './npy/' + picked_npy_file + '_Y.npy'

    return x_npy, y_npy


options = loadyaml(config_file)    

print('Training Configuration')
print(yaml.dump(options, default_flow_style=False, default_style=''))

npy_log_file = os.path.join(ROOT_DIR, 'src', options['npy_log_file'])
x_npy, y_npy = select_npy_data(npy_log_file)

x_train = np.load(x_npy)
y_train = np.load(y_npy)
x_val = np.load(os.path.join(ROOT_DIR, options['val_imgs']))
y_val = np.load(os.path.join(ROOT_DIR, options['val_labels']))
experiment_name = options['experiment_name']
num_gpus = options['num_gpus']
height, width = options['height'],options['width']
network = options['network']
nb_epoch = options['epochs']
batch_size = options['batch_size']
learning_rate = options['learning_rate']
sgd_momentum = options['sgd_momentum']
step_decay = options['step_decay']
drop_factor = options['drop_factor']
epochs_until_drop = options['epochs_until_drop']
optimizer = options['optimizer']
batch_momentum = options['batch_momentum']
weight_decay = options['weight_decay']
augmentation = options['augmentation']
affine_augs = options['affine_augs']


# Make directories if needed
if not os.path.exists('./trainings/'):
    os.makedirs('./trainings/')

if not os.path.exists('./trainings/'+experiment_name):
    os.makedirs('./trainings/'+experiment_name)

copyfile(config_file,'./trainings/'+experiment_name+'/'+os.path.basename(config_file))


# Build data generators if applying augmentation
if augmentation:
    train_gen = BatchGenerator(x_train, y_train, batch_size,
                affine=affine_augs, height=height, width=width)
else:
    train_gen = BatchGenerator(x_train, y_train, batch_size, noaugs=True,
            height=height, width=width)
val_gen = BatchGenerator(x_val, y_val, batch_size, noaugs=True, height=height,
        width=width)

model = SimpleModel(input_shape=(height,width,3), momentum=batch_momentum,
        weight_penalty=weight_decay)
model.summary() 

if optimizer=='SGD':
    optim= SGD(lr=learning_rate, momentum=sgd_momentum, nesterov=True)
    #, clipnorm=1.)
if optimizer=='Adam':
    optim= Adam(lr=learning_rate)
model.compile(loss=smoothL1, optimizer=optim, metrics=['mae'])

tensorboard = TensorBoard(log_dir='./trainings/'+experiment_name,
        histogram_freq=0, write_graph=True, write_images=False)
checkpoint = ModelCheckpoint('./trainings/'+experiment_name+'/'+network+'.h5',
        monitor='mean_absolute_error', verbose=1, save_best_only=True, mode='min',
        period=1)
csv_logger = CSVLogger('./trainings/'+experiment_name+'/training_log.csv')
callbacks = [tensorboard, checkpoint, csv_logger]

if step_decay:
    #Decay function for the learning rate
    def step_decay(epoch):
        initial_lrate = learning_rate
        drop = drop_factor
        epochs_drop = epochs_until_drop
        lrate = initial_lrate * np.power(drop, np.floor((1+epoch)/epochs_drop))
        print('Current Learning Rate is '+str(lrate))
        return lrate
    lrate = LearningRateScheduler(step_decay)
    callbacks.append(lrate)

model.fit_generator(train_gen,
        steps_per_epoch=int(np.floor(len(x_train)/batch_size)),
        validation_data=val_gen,
        validation_steps=5,
        epochs=nb_epoch,
        callbacks=callbacks)

