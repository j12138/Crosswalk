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
labeling_dir = os.path.join(ROOT_DIR, 'src', 'labeling')
config_file = os.path.join(BASE_DIR, 'config.yaml')
train_npy_idx = -1


def parse_args():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()
    return args


# Load the training config file
def loadyaml(filename):
    with open(filename, 'r') as stream: 
        opt = yaml.load(stream)
    return opt


def select_npy_data(npy_log_file, picked_train_npy):
    """ show existing npy files, allows user to pick 1 pair
    :param npy_log_file: .txt log file containing npy file info
    :return x_npy, y_npy: paths of X, Y npy files
    :return img_spec: img specification parameter (width, height, grayscale)
    """

    with open(npy_log_file, "r") as f:
        lines = f.readlines()
        cnt = 0

        print('---------- npy list ----------')
        for line in lines:
            if line[:2] == '//':
                continue
            cnt = cnt + 1
            if cnt == picked_train_npy:
                print('[*]', line.strip())
            else:
                print('['+str(cnt)+']', line.strip())
            pass
        print('------------------------------')

        picked_num = input('select npy: ')
        picked_line = (lines[int(picked_num)].rstrip()).split('\t')
        picked_npy_file = picked_line[0]
        print(picked_npy_file)
        img_spec = picked_line[-1].strip('(').strip(')').split(', ')

        path_prefix = os.path.join(labeling_dir, 'npy', picked_npy_file)
        x_npy = path_prefix + '_X.npy'
        y_npy = path_prefix + '_Y.npy'

    return x_npy, y_npy, img_spec, int(picked_num)


opt = loadyaml(config_file)

print('Training Configuration')
print(yaml.dump(opt, default_flow_style=False, default_style=''))

#npy_log_file = os.path.join(labeling_dir, opt['npy_log_file'])

x_train = np.load(opt['x_train'])
y_train = np.load(opt['y_train'])
x_val = np.load(opt['x_val'])
y_val = np.load(opt['y_val'])

width, height, grayscale = opt['width'], opt['height'], opt['grayscale']
if width <= 0:
    width = opt['width']
if height <= 0:
    height = opt['height']
channel = 1 if grayscale else 3

print("width: ", width, ", height: ", height)

experiment_name = opt['experiment_name']
num_gpus = opt['num_gpus']
network = opt['network']
nb_epoch = opt['epochs']
batch_size = opt['batch_size']
learning_rate = opt['learning_rate']
sgd_momentum = opt['sgd_momentum']
step_decay = opt['step_decay']
drop_factor = opt['drop_factor']
epochs_until_drop = opt['epochs_until_drop']
optimizer = opt['optimizer']
batch_momentum = opt['batch_momentum']
weight_decay = opt['weight_decay']
augmentation = opt['augmentation']
affine_augs = opt['affine_augs']


# Make directories if needed
if not os.path.exists('./trainings/'):
    os.makedirs('./trainings/')

if not os.path.exists('./trainings/'+experiment_name):
    os.makedirs('./trainings/'+experiment_name)

copyfile(config_file, './trainings/'+experiment_name+'/'+os.path.basename(config_file))


# Build data generators if applying augmentation
if augmentation:
    train_gen = BatchGenerator(x_train, y_train, batch_size,
                affine=affine_augs, height=height, width=width)
else:
    train_gen = BatchGenerator(x_train, y_train, batch_size, noaugs=True,
            height=height, width=width)
val_gen = BatchGenerator(x_val, y_val, batch_size, noaugs=True, height=height,
        width=width)

model = SimpleModel(input_shape=(height,width,channel), momentum=batch_momentum,
        weight_penalty=weight_decay)
model.summary() 

if optimizer == 'SGD':
    optim = SGD(lr=learning_rate, momentum=sgd_momentum, nesterov=True)
    # , clipnorm=1.)
if optimizer == 'Adam':
    optim = Adam(lr=learning_rate)
    # smoothL1
model.compile(loss=smoothL1, optimizer=optim, metrics=['mae'])

tensorboard = TensorBoard(log_dir='./trainings/'+experiment_name,
        histogram_freq=0, write_graph=True, write_images=False)
checkpoint = ModelCheckpoint('./trainings/'+experiment_name+'/'+network+'.h5',
                             monitor='val_mean_absolute_error', verbose=1,
                             save_best_only=True, mode='min', period=1)
csv_logger = CSVLogger('./trainings/'+experiment_name+'/training_log.csv')
callbacks = [tensorboard, checkpoint, csv_logger]

if step_decay:
    # Decay function for the learning rate

    def step_decay(epoch):
        initial_lrate = learning_rate
        drop = drop_factor
        epochs_drop = epochs_until_drop
        lrate = initial_lrate * np.power(drop, np.floor((1+epoch)/epochs_drop))
        print('Current Learning Rate is '+str(lrate))
        return lrate

    lrate = LearningRateScheduler(step_decay, verbose=True)
    callbacks.append(lrate)

model.fit_generator(train_gen,
                    steps_per_epoch=int(np.floor(len(x_train)/batch_size)),
                    validation_data=val_gen,
                    validation_steps=5,
                    epochs=nb_epoch,
                    callbacks=callbacks)

