import numpy as np
import cv2
import os
import argparse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(BASE_DIR, "..", "..")
npy_log_file = os.path.join(BASE_DIR, 'makenp_log.txt')


def check_npy(x_npy, y_npy):
    """ show each packed img and its shape(size)
    :param x_npy: X npy file for check
    :param y_npy: Y npy file for check
    :return: None
    """
    X = np.load(x_npy)
    cv2.namedWindow('np_test')
    print('total: ', len(X))

    for img in X:
        h, w = img.shape[:2]
        print(w, h)

        while True:
            cv2.imshow('np_test', img)
            if cv2.waitKey(10) == 32:
                break  # press 'spacebar' -> turn to next image


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('npy_path', type=str, help="path of npy file to see")
    args = parser.parse_args()

    x_npy = args.npy_path
    y_npy = x_npy[:-6] + 'y.npy'
    check_npy(x_npy, y_npy)


if __name__ == '__main__':
    main()