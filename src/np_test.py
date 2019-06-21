import numpy as np
import cv2
import os


def search(dirname):
    filenames = os.listdir(dirname)
    print('\n---------- npy lists ----------')
    cnt = 0

    for filename in filenames:
        full_filename = os.path.join(dirname, filename)
        ext = os.path.splitext(full_filename)[-1]

        if ext == '.npy': 
            cnt = cnt + 1 
            print('['+ str(cnt) + '] ' + os.path.split(full_filename)[-1])

    print('---------------------------------')


def check_npy():
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


def main():
    search(os.getcwd())
    picked_num = int(input('pick npy # : '))
    print(picked_num)


if __name__ == '__main__':
    main()