"""
Taxi Net Model Training
Supports single or multigpu training
By: Tyler Staudinger
Copyright 2018 The Boeing Company
Note: On certain machines multiprocessing will cause errors, consider disabling if this occurs
"""

#from Models.MobileNetV2 import MobileNetV2
from Models.Simplified import SimpleModel
from keras.callbacks import Callback,ModelCheckpoint,TensorBoard,CSVLogger,LearningRateScheduler
from keras.utils.training_utils import multi_gpu_model
from keras.optimizers import SGD, Adam
import tensorflow as tf
import numpy as np
import yaml
import os
from shutil import copyfile
from Generator.augmentation import BatchGenerator
import argparse
from Models.loss import smoothL1

def parseArgs():
    parser = argparse.ArgumentParser()
    parser.add_argument('-yaml',default='train.yaml',
                    help='Name of yaml config file for experiments') 
    args = parser.parse_args()
    return args

#Load the training configuration file
def loadyaml(filename):
    with open(filename, 'r') as stream: 
        options = yaml.load(stream)
    return options

args= parseArgs()
options=loadyaml(args.yaml)    
print('Training Configuration')
print('*************************************')
print(yaml.dump(options,default_flow_style=False, default_style=''))
x_train=np.load(options['train_imgs'])
y_train=np.load(options['train_labels'])
x_val=np.load(options['val_imgs'])
y_val=np.load(options['val_labels'])
experiment_name=options['experiment_name']
num_gpus=options['num_gpus']
height, width= options['height'],options['width']
network=options['network']
nb_epoch=options['epochs']
batch_size=options['batch_size']
learning_rate=options['learning_rate']
sgd_momentum=options['sgd_momentum']
step_decay=options['step_decay']
drop_factor=options['drop_factor']
epochs_until_drop=options['epochs_until_drop']
optimizer=options['optimizer']
batch_momentum=options['batch_momentum']
weight_decay=options['weight_decay']
augmentation=options['augmentation']
affine_augs=options['affine_augs']
print('*************************************')


#Make directories if needed
if not os.path.exists('./Training_Runs/'):
    os.makedirs('./Training_Runs/')

if not os.path.exists('./Training_Runs/'+experiment_name):
    os.makedirs('./Training_Runs/'+experiment_name)

copyfile(args.yaml,'./Training_Runs/'+experiment_name+'/'+args.yaml)

#Decay function for the learning rate
if step_decay:
    def step_decay(epoch):
        initial_lrate = learning_rate
        drop = drop_factor
        epochs_drop = epochs_until_drop
        lrate = initial_lrate * np.power(drop, np.floor((1+epoch)/epochs_drop))
        print('Current Learning Rate is '+str(lrate))
        return lrate
'''
#Multigpu Checkpoint saves the cpu version of the model every N epochs
class MultiGPUCheckpoint(Callback):

    def __init__(self, model, path, N):

        self.path = path
        self.N=N
        self.model_for_saving = model
        self.epoch=0

    def on_epoch_end(self, epoch, logs=None):
        
        if self.epoch % self.N ==0:
            loss = logs['val_loss']
            # Here we save the original one
            print("\nSaving model to : {}".format(self.path.format(epoch=epoch, val_loss=loss)))
            self.model_for_saving.save(self.path.format(epoch=epoch, val_loss=loss), overwrite=True)
        self.epoch+=1   
''' 
#Choose the model                
def select_model(network):
    new_model = SimpleModel(input_shape=(height,width,3), 
                    momentum=batch_momentum,weight_penalty=weight_decay)  
    return new_model
    
#Build data generators if applying augmentation
if augmentation:
    train_gen=BatchGenerator(x_train,y_train,batch_size,affine=affine_augs,height=height, width=width)
    
    val_gen=BatchGenerator(x_val,y_val,batch_size,noaugs=True,height=height, width=width)
else:
    train_gen=BatchGenerator(x_train,y_train,batch_size,noaugs=True, height=height, width=width)
    val_gen=BatchGenerator(x_val,y_val,batch_size,noaugs=True,height=height, width=width)
'''
#If we are using multple gpus
if num_gpus>1:
    print('******Multi GPU Training Active******')
    #Create CPU Model, the weights of this model are updated from the computations on the GPUs                    
    with tf.device("/cpu:0"):
        model=select_model(network)
        model.summary() 
    
    #Set up the multigpu model
    multi_gpu=multi_gpu_model(model,gpus=num_gpus)
    if optimizer=='SGD':
        optim= SGD(lr=learning_rate, momentum=sgd_momentum, nesterov=True, clipnorm=1.)
    if optimizer=='Adam':
        optim= Adam(lr=learning_rate, clipnorm=1.)
    multi_gpu.compile(loss=smoothL1,optimizer=optim,metrics=['mae'])   
    
    # Setting the callback function
    checkpointsString = './Training_Runs/'+experiment_name+'/'+network+'_{epoch:02d}_{val_loss:.2f}'+'.h5'
    tensorboard = TensorBoard(log_dir='./Training_Runs/'+experiment_name, histogram_freq=0, write_graph=True, write_images=False)
    csv_logger = CSVLogger('./Training_Runs/'+experiment_name+'/training_log.csv')
    checkpoint=MultiGPUCheckpoint(model, checkpointsString,3)
    callbacks = [checkpoint,tensorboard,csv_logger]
    if step_decay:
        lrate = LearningRateScheduler(step_decay)
        callbacks.append(lrate)

    multi_gpu.fit_generator(train_gen,steps_per_epoch=int(np.floor(len(x_train)/batch_size)),validation_data=val_gen,
    validation_steps=int(np.floor(len(x_val)/batch_size)),epochs=nb_epoch,
    callbacks=callbacks, use_multiprocessing=True,workers=8)
 ''' 
#Single gpu training  

print('******Single GPU Training Active******')

model=select_model(network) 
model.summary() 
if optimizer=='SGD':
    optim= SGD(lr=learning_rate, momentum=sgd_momentum, nesterov=True)
    #, clipnorm=1.)
if optimizer=='Adam':
    optim= Adam(lr=learning_rate) #, clipnorm=1.)
model.compile(loss=smoothL1,optimizer=optim,metrics=['mae'])        

tensorboard = TensorBoard(log_dir='./Training_Runs/'+experiment_name, histogram_freq=0, write_graph=True, write_images=False)
checkpoint = ModelCheckpoint('./Training_Runs/'+experiment_name+'/'+network+'.h5', monitor='val_loss', verbose=1, save_best_only=True, mode='min', period=1)
csv_logger = CSVLogger('./Training_Runs/'+experiment_name+'/training_log.csv')
callbacks=[tensorboard,checkpoint,csv_logger]

if step_decay:
    lrate = LearningRateScheduler(step_decay)
    callbacks.append(lrate)

#print (int(np.floor(len(x_val)/batch_size)))

model.fit_generator(train_gen,
        steps_per_epoch=int(np.floor(len(x_train)/batch_size)),
        validation_data=val_gen,
        validation_steps=5,
        epochs=nb_epoch,
        callbacks=callbacks)

