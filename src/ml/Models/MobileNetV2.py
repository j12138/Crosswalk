"""
By: Tyler Staudinger 
Copyright 2018 The Boeing Company

MobileNet v2 models for Keras.
# Reference
- [Inverted Residuals and Linear Bottlenecks Mobile Networks for
   Classification, Detection and Segmentation]
   (https://arxiv.org/abs/1801.04381)
   
This model is the variant in table 2 of the paper 
"""


from keras.models import Model
from keras.layers import Input, Conv2D, GlobalAveragePooling2D, Dropout
from keras.layers import Activation, add, Dense
from keras.layers import DepthwiseConv2D, BatchNormalization
from keras.regularizers import l2 
from keras import backend as K


def conv_block(inputs, filters, kernel, strides,name,featuremap='',weight_penalty=0.0,momentum=.9):
    """Convolution Block
    This function defines a 2D convolution operation with BN and relu6.
    # Arguments
        inputs: Tensor, input tensor of conv layer.
        filters: Integer, the dimensionality of the output space.
        kernel: An integer or tuple/list of 2 integers, specifying the
            width and height of the 2D convolution window.
        strides: An integer or tuple/list of 2 integers,
            specifying the strides of the convolution along the width and height.
            Can be a single integer to specify the same value for
            all spatial dimensions.
    # Returns
        Output tensor.
    """

    x = Conv2D(filters, kernel, padding='same', strides=strides,name='conv_a_'+name,use_bias=False,kernel_regularizer=l2(weight_penalty))(inputs)
    
    x = BatchNormalization(axis=3,name='bn_a_'+name,momentum=momentum)(x)

    if featuremap!='':
        x=Activation('elu',name=featuremap)(x)
    else:
        x=Activation('elu',name='act_a_'+name)(x)
    return x


def bottleneck(inputs, filters, kernel, t, s, r=False,name='',featuremap='', weight_penalty=0.0,momentum=.9):
    """Bottleneck
    This function defines a basic bottleneck structure.
    # Arguments
        inputs: Tensor, input tensor of conv layer.
        filters: Integer, the dimensionality of the output space.
        kernel: An integer or tuple/list of 2 integers, specifying the
            width and height of the 2D convolution window.
        t: Integer, expansion factor.
            t is always applied to the input size.
        s: An integer or tuple/list of 2 integers,specifying the strides
            of the convolution along the width and height.Can be a single
            integer to specify the same value for all spatial dimensions.
        r: Boolean, Whether to use the residuals.
    # Returns
        Output tensor.
    """

    channel_axis = 1 if K.image_data_format() == 'channels_first' else -1
    tchannel = K.int_shape(inputs)[channel_axis] * t

    x = conv_block(inputs, tchannel, (1, 1), (1, 1),name=name,featuremap=featuremap, weight_penalty=weight_penalty)


    x = DepthwiseConv2D(kernel, strides=(s, s), depth_multiplier=1, use_bias=False, padding='same',name='depthconv_'+name,kernel_regularizer=l2(weight_penalty))(x)

    x = BatchNormalization(axis=3,name='bn_b_'+name,momentum=momentum)(x)
        
    x = Activation('elu',name='act_b_'+name)(x)

    x = Conv2D(filters, (1, 1), strides=(1, 1), padding='same',name='conv_b_'+name,use_bias=False,kernel_regularizer=l2(weight_penalty))(x)
    
    x = BatchNormalization(axis=3,name='bn_c_'+name,momentum=momentum)(x)
    
    if r:
        x = add([x, inputs],name='add_'+name)
    return x


def inverted_residual_block(inputs, filters, kernel, t, strides, n,block,featuremap='',weight_penalty=0.0,momentum=.9,freeze=False):
    """Inverted Residual Block
    This function defines a sequence of 1 or more identical layers.
    # Arguments
        inputs: Tensor, input tensor of conv layer.
        filters: Integer, the dimensionality of the output space.
        kernel: An integer or tuple/list of 2 integers, specifying the
            width and height of the 2D convolution window.
        t: Integer, expansion factor.
            t is always applied to the input size.
        s: An integer or tuple/list of 2 integers,specifying the strides
            of the convolution along the width and height.Can be a single
            integer to specify the same value for all spatial dimensions.
        n: Integer, layer repeat times.
    # Returns
        Output tensor.
    """

    x = bottleneck(inputs, filters, kernel, t, strides,featuremap=featuremap,name=str(block)+'_0', weight_penalty=weight_penalty)

    for i in range(1, n):
        x = bottleneck(x, filters, kernel, t, 1, True,name=str(block)+'_'+str(i), weight_penalty=weight_penalty)
      
    return x


def MobileNetV2(input_shape=(224,224,3),weight_penalty=0.0001,momentum=.9):
    ''' Creates a MobileNetV2 model with specified parameters
    Args:        input_shape: shape of the input tensor


    Returns: a Keras Model
    '''

    img_input = Input(shape=input_shape,name='input_layer')
    x = conv_block(img_input, 32, (3, 3), strides=(2, 2),weight_penalty=weight_penalty,name='conv1',momentum=momentum)

    x = inverted_residual_block(x, 16, (3, 3), t=1, strides=1, n=1,block=1, weight_penalty=weight_penalty,momentum=momentum)
    x = inverted_residual_block(x, 24, (3, 3), t=6, strides=2, n=2,block=2, weight_penalty=weight_penalty,momentum=momentum)
    x = inverted_residual_block(x, 32, (3, 3), t=6, strides=2, n=3,block=3,featuremap='C2Features', weight_penalty=weight_penalty,momentum=momentum)
    x = inverted_residual_block(x, 64, (3, 3), t=6, strides=2, n=4,block=4,featuremap='C3Features', weight_penalty=weight_penalty,momentum=momentum)
    x = inverted_residual_block(x, 96, (3, 3), t=6, strides=1, n=3,block=5, weight_penalty=weight_penalty,momentum=momentum)
    x = inverted_residual_block(x, 160, (3, 3), t=6, strides=2, n=3,block=6,featuremap='C4Features', weight_penalty=weight_penalty,momentum=momentum)
    x = inverted_residual_block(x, 320, (3, 3), t=6, strides=1, n=1,block=7, weight_penalty=weight_penalty,momentum=momentum)

    x = conv_block(x, 1280, (1, 1), strides=(1, 1),featuremap='C5Features',name='conv2', weight_penalty=weight_penalty,momentum=momentum)
    x = GlobalAveragePooling2D()(x)
    x = Dropout(.3)(x) 
    x=Dense(100, activation='elu',kernel_initializer='he_normal',bias_regularizer=l2(weight_penalty),kernel_regularizer=l2(weight_penalty))(x)
    x=Dense(50, activation='elu',kernel_initializer='he_normal',bias_regularizer=l2(weight_penalty),kernel_regularizer=l2(weight_penalty))(x)
    x=Dense(10, activation='elu',kernel_initializer='he_normal',bias_regularizer=l2(weight_penalty),kernel_regularizer=l2(weight_penalty))(x)
    x=Dense(2,activation='softsign',kernel_initializer='he_normal')(x)
    model = Model(img_input, x, name='MobileNetV2')
    return model

if __name__ == '__main__':
    model=MobileNetV2()
    model.summary()
