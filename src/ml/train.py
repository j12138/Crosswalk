"""
Batoners Inc.

Jan 2019
"""

import tensorflow as tf
import numpy as np
import tensorflow.keras
from tensorflow.keras.callbacks import ModelCheckpoint, TensorBoard, CSVLogger, LearningRateScheduler
from tensorflow.python.keras.utils.data_utils import Sequence
from tensorflow.keras.optimizers import SGD, Adam
import yaml
import os
from shutil import copyfile

import argparse
from Models.Simplified import SimpleModel
from Models.MobileNetV2 import MobileNetV2
from Models.loss import smoothL1
from Generator.augmentation import BatchGenerator
import wandb


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(BASE_DIR, "..", "..")
labeling_dir = os.path.join(ROOT_DIR, 'src', 'labeling')
config_file = os.path.join(BASE_DIR, 'config.yaml')
train_npy_idx = -1


def mae0(y_true, y_pred):
    return tensorflow.keras.losses.mae(y_true[:,0], y_pred[:,0])

def mae1(y_true, y_pred):
    return tensorflow.keras.losses.mae(y_true[:,1], y_pred[:,1])

def mse0(y_true, y_pred):
    return tensorflow.keras.losses.mse(y_true[:,0], y_pred[:,0])

def mse1(y_true, y_pred):
    return tensorflow.keras.losses.mse(y_true[:,1], y_pred[:,1])

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('exp_name', type=str)
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


args = parse_args()
opt = loadyaml(config_file)

wandb.init(project="crosswalk", name=args.exp_name, id=args.exp_name,
           config=config, sync_tensorboard=True)

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

exp_name = args.exp_name
nb_epoch = opt['epochs']
batch_size = opt['batch_size']
learning_rate = opt['learning_rate']
sgd_momentum = opt['sgd_momentum']
step_decay = opt['step_decay']
epochs_until_drop = opt['epochs_until_drop']


# Make directories if needed
if not os.path.exists('./trainings/'):
    os.makedirs('./trainings/')

if not os.path.exists('./trainings/'+exp_name):
    os.makedirs('./trainings/'+exp_name)

copyfile(config_file, './trainings/'+exp_name+'/'+os.path.basename(config_file))


# Build data generators if applying augmentation
if opt['augmentation']:
    train_gen = BatchGenerator(x_train, y_train, batch_size,
                affine=opt['affine_augs'], height=height, width=width)
else:
    train_gen = BatchGenerator(x_train, y_train, batch_size, noaugs=True,
            height=height, width=width)

val_gen = BatchGenerator(x_val, y_val, batch_size, noaugs=True, height=height,
        width=width)

# Initialize a model
model = None
if opt['network'].lower() == 'simplified':
    model = SimpleModel(input_shape=(height, width, channel),
                        momentum=opt['batch_momentum'],
                        weight_penalty=opt['weight_decay'])
elif opt['network'].lower() = 'mobilenetv2':
    model = MobileNetV2(input_shape=(height, width, channel),
                        momentum=opt['batch_momentum'],
                        weight_penalty=opt['weight_decay'])
else:
    raise Exception("Network", opt['network'], "is undefined.")
model.summary() 

if opt['optimizer'] == 'SGD':
    optim = SGD(lr=learning_rate, momentum=sgd_momentum, nesterov=True)
    # , clipnorm=1.)
if opt['optimizer'] == 'Adam':
    optim = Adam(lr=learning_rate)
    # smoothL1
model.compile(loss=smoothL1, optimizer=optim,
        metrics=['mae', mae0, mae1, 'mse', mse0, mse1])

tensorboard = TensorBoard(log_dir='./trainings/'+exp_name,
        histogram_freq=0, write_graph=True, write_images=False,
        embeddings_freq=10)
model_path = os.path.join('.', 'trainings', exp_name, opt['network'] + '.h5')
checkpoint = ModelCheckpoint(model_path, monitor='val_mae', verbose=1,
                             save_best_only=True, mode='min')
checkpoint2 = ModelCheckpoint(os.path.join(wandb.run_dir, opt['network'] + '.h5'),
                             monitor='val_mae', verbose=1, save_best_only=True,
                             mode='min')
csv_logger = CSVLogger('./trainings/'+exp_name+'/training_log.csv')
callbacks = [tensorboard, checkpoint, checkpoint2, csv_logger]

if step_decay:
    # Decay function for the learning rate

    def step_decay(epoch):
        initial_lrate = learning_rate
        drop = opt['drop_factor']
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
                    epochs=opt['nb_epoch'],
                    workers=2,
                    callbacks=callbacks)

