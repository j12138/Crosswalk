import numpy as np
import cv2

X = np.load('./X.npy')

cv2.namedWindow('np_test')

print('total: ', len(X))

for img in X:
    #print(img)

    #print('Truth : ', y_val[cnt])
    #print('Prediction : ', scaled_prediction)

    while True:
        cv2.imshow('np_test', img)
        if cv2.waitKey(10) == 32:
            break # press 'spacebar' -> turn to next image