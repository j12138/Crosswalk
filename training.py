from sample_models.Simplified import SimpleModel
from keras.preprocessing.image import ImageDataGenerator
import numpy as np


train_datagen = ImageDataGenerator(rescale=1./255)
train_generator = train_datagen.flow_from_directory(
        'preprocessed_data/train',
        target_size=(300, 240),
        batch_size=3,
        class_mode='binary')

train_datagen = ImageDataGenerator(rescale=1./255)
train_generator = train_datagen.flow_from_directory(
        'preprocessed_data/test',
        target_size=(300, 240),
        batch_size=3,
        class_mode='categorical')