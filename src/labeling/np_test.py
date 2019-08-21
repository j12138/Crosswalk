import numpy as np
import cv2
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(BASE_DIR, "..", "..")
npy_log_file = os.path.join(BASE_DIR, 'makenp_log.txt')


def select_npy_data(npy_log_file):
    """ show existing npy files, allows user to pick 1 pair
    :param npy_log_file: .txt log file containing npy file info
    :return x_npy, y_npy: paths of X, Y npy files
    :return img_spec: img specification parameter (width, height, grayscale)
    """

    with open(npy_log_file, "r") as f:
        lines = f.readlines()
        cnt = 0

        print('\n---------- npy list ----------')
        for line in lines:
            if line[:2] == '//':
                continue
            cnt = cnt + 1
            print('['+str(cnt)+']', line.strip())
            pass
        print('------------------------------')

        picked_num = input('select npy: ')
        picked_line = (lines[int(picked_num)].rstrip()).split('\t')
        picked_npy_file = picked_line[0]
        print(picked_npy_file)
        img_spec = picked_line[-1].strip('(').strip(')').split(', ')

        path_prefix = os.path.join(BASE_DIR, 'npy', picked_npy_file)
        x_npy = path_prefix + '_X.npy'
        y_npy = path_prefix + '_Y.npy'

    return x_npy, y_npy, img_spec


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
    x_npy, y_npy, img_spec = select_npy_data(npy_log_file)
    print(img_spec)
    check_npy(x_npy, y_npy)


if __name__ == '__main__':
    main()