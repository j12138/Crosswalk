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
from datetime import datetime
import wandb


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(BASE_DIR, "..", "..")
labeling_dir = os.path.join(ROOT_DIR, 'src', 'labeling')
config_file = os.path.join('.', 'ml_config.yaml')
train_npy_idx = -1


def mae0(y_true, y_pred):
    return tensorflow.keras.losses.mae(y_true[:,0], y_pred[:,0])

def mae1(y_true, y_pred):
    return tensorflow.keras.losses.mae(y_true[:,1], y_pred[:,1])

def parse_args():
    parser = argparse.ArgumentParser()
    expname = datetime.strftime(datetime.now(), '%y%m%d-%H%M%S')
    parser.add_argument('--exp_name', type=str, default=expname)
    parser.add_argument('--network', type=str)
    parser.add_argument('--optimizer', type=str)
    parser.add_argument('--epochs', type=int)
    parser.add_argument('--batch_size', type=int)
    parser.add_argument('--learning_rate', type=float)
    parser.add_argument('--sgd_momentum', type=float)
    parser.add_argument('--step_decay', type=bool)
    parser.add_argument('--drop_factor', type=float)
    parser.add_argument('--epochs_until_drop', type=int)
    parser.add_argument('--batch_momentum', type=float)
    parser.add_argument('--weight_decay', type=float)
    parser.add_argument('--augmentation', type=bool)
    parser.add_argument('--affine_augs', type=str)
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
args_dict = vars(args)
opt = loadyaml(config_file)
for key in opt:
    if key in args_dict and args_dict[key] is not None:
        opt[key] = args_dict[key]

wandb.init(project="crosswalk", name=args.exp_name, config=opt,
           sync_tensorboard=True)

print('Training Configuration')
print(yaml.dump(opt, default_flow_style=False, default_style=''))

#npy_log_file = os.path.join(labeling_dir, opt['npy_log_file'])

x_train = np.load(opt['x_train'])
y_train = np.load(opt['y_train'])
x_val = np.load(opt['x_val'])
y_val = np.load(opt['y_val'])
print('# train: {}, # val: {}'.format(len(x_train), len(x_val)))

width, height, grayscale = opt['width'], opt['height'], opt['grayscale']
if width <= 0:
    width = opt['width']
if height <= 0:
    height = opt['height']
channel = 1 if grayscale else 3

print("width: ", width, ", height: ", height)

exp_name = args.exp_name
batch_size = opt['batch_size']
learning_rate = opt['learning_rate']
sgd_momentum = opt['sgd_momentum']
step_decay = opt['step_decay']
epochs_until_drop = opt['epochs_until_drop']


# Make directories if needed
if not os.path.exists('./trainings/'):
    os.makedirs('./trainings/')

if not os.path.exists(os.path.join('.', 'trainings', exp_name)):
    os.makedirs(os.path.join('.', 'trainings', exp_name))

config_file_dst = os.path.join('.', 'trainings', exp_name,
                               os.path.basename(config_file))
copyfile(config_file, config_file_dst)
wandb.save(config_file_dst)


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
elif opt['network'].lower() == 'mobilenetv2':
    model = MobileNetV2(input_shape=(height, width, channel),
                        momentum=opt['batch_momentum'],
                        weight_penalty=opt['weight_decay'])
else:
    raise Exception("Network", opt['network'], "is undefined.")
#model.summary() 

if opt['optimizer'] == 'SGD':
    optim = SGD(lr=learning_rate, momentum=sgd_momentum, nesterov=True)
    # , clipnorm=1.)
if opt['optimizer'] == 'Adam':
    optim = Adam(lr=learning_rate)
    # smoothL1
model.compile(loss=smoothL1, optimizer=optim,
        metrics=['msle', 'mae', mae0, mae1])

tensorboard = TensorBoard(log_dir=os.path.join('.', 'trainings', exp_name),
                          write_graph=True, update_freq='epoch',
                          write_images=True, embeddings_freq=10)

model_path = os.path.join('.', 'trainings', exp_name, exp_name + '.h5')
checkpoint = ModelCheckpoint(model_path, monitor='val_mae', verbose=1,
                             save_best_only=True, mode='min')
csv_logger = CSVLogger(os.path.join('.', 'trainings', exp_name, 'training_log.csv'))
callbacks = [tensorboard, checkpoint, csv_logger]

if step_decay:
    # Decay function for the learning rate

    def step_decay(epoch):
        initial_lrate = learning_rate
        drop = opt['drop_factor']
        epochs_drop = epochs_until_drop
        lrate = initial_lrate * np.power(drop, np.floor((1+epoch)/epochs_drop))
        print('\nCurrent Learning Rate is {}\n'.format(lrate))
        return lrate

    lrate = LearningRateScheduler(step_decay, verbose=True)
    callbacks.append(lrate)

model.fit_generator(train_gen,
                    steps_per_epoch=int(np.floor(len(x_train)/batch_size)),
                    validation_data=val_gen,
                    validation_steps=int(np.floor(len(x_val)/batch_size)),
                    epochs=opt['epochs'],
                    use_multiprocessing=True,
                    workers=2,
                    callbacks=callbacks)

converted = tf.lite.TFLiteConverter.from_keras_model(model).convert()
open(os.path.join('.', 'trainings', exp_name, exp_name + '.tflite'), "wb").write(converted)
wandb.save(os.path.join('trainings', exp_name))
#open(os.path.join(wandb.run.dir, exp_name + '.tflite'), 'wb').write(converted)

