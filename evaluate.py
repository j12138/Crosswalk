from keras.models import load_model 
import numpy as np
import matplotlib.pyplot as plt 
from Models.loss import smoothL1
import time
import argparse
import cv2

parser = argparse.ArgumentParser()
parser.add_argument('-e', '--eval_folder', help="path to folder of data to evaluate", 
                    default='./preprocessed_data/eval/')    
parser.add_argument('-m', '--model_path', help="path to model", 
                    default='./trainings/Crosswalk_guide/SimpleModel.h5')
args = parser.parse_args()

#Load the data (change path as needed')
x_test=np.load(args.eval_folder+'X.npy')
y_test=np.load(args.eval_folder+'Y.npy') #Truth


model=load_model(args.model_path,custom_objects={'smoothL1':smoothL1}) 
print('Running Evaluation Now Please Wait')

outputs_test=[]
inference_time=[]
cnt = 0

for img in x_test:
    cnt = cnt + 1
    t=time.time()
    outputs_test.append(model.predict(np.expand_dims(img/255.0,axis=0)))
    inference_time.append((1/(time.time()-t)))
        
outputs_test=np.squeeze(np.asarray(outputs_test))
print('# of imgs : ', cnt)
print('--- prediction ---')
print(outputs_test)
print('----- Truth -----')
print(y_test)
inference_time=np.squeeze(np.asarray(inference_time))

#Scale the predictions
outputs_cte=outputs_test[:,0]*8.0

#Plot the predictions vs truth
plt.figure()
truth,=plt.plot(y_test[:,0],label='Truth')
predictions,=plt.plot(outputs_cte,label='Predictions')
plt.legend(handles=[truth,predictions])
plt.title('Test Cross Track Error')
plt.xlabel('sample number')
plt.ylabel('distance in meters')
plt.show()

#Plot the model error histogram
error_test=np.squeeze(y_test[:,0])-outputs_cte

#Print error metrics
print(" ")
print("Cross Track Error")
abs_error_test=np.abs(error_test)
print('MeanAbsoluteError: '+str(np.mean(abs_error_test)))
print('MedianAbsoluteError: '+str(np.median(abs_error_test)))
print('StandardDeviation: '+str(np.std(abs_error_test)))
print('MeanInferenceTime: '+str(np.mean(inference_time)))
print('MaxAbsoluteError: '+str(np.max(abs_error_test)))

#Scale the prediction
outputs_heading=outputs_test[:,1]*35.0

#Plot the predictions vs truth
plt.figure()
truth,=plt.plot(y_test[:,1],label='Truth')
predictions,=plt.plot(outputs_heading,label='Predictions')
plt.legend(handles=[truth,predictions])
plt.title('Test Heading Error')
plt.xlabel('sample number')
plt.ylabel('degrees')
plt.show()

#Plot the model error histogram
error_test=np.squeeze(y_test[:,1])-outputs_heading

print(" ")
print("Heading Error")
#Print error metrics
abs_error_test=np.abs(error_test)
print('MeanAbsoluteError: '+str(np.mean(abs_error_test)))
print('MedianAbsoluteError: '+str(np.median(abs_error_test)))
print('StandardDeviation: '+str(np.std(abs_error_test)))
print('MaxAbsoluteError: '+str(np.max(abs_error_test)))

