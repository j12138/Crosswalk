import json
import numpy as np
import yaml
import scipy
import cv2
from scipy.misc import imread
import datetime
import glob
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(BASE_DIR, "..")
config_file = os.path.join(BASE_DIR, 'labeling', 'config.yaml')


# coding=utf-8

filterlist = {'Apple': lambda x: x['Make'] == 'Apple',
              'Samsung': lambda x: x['Make'] == 'samsung',
              'shadow': lambda x: x['shadow'] == 1,
              'obstacle': lambda x: x['obs_car'] == 1 and x['obs_human'] == 1,
              'car': lambda x: x['obs_car'] == 1,
              'human': lambda x: x['obs_human'] == 1,
              'onecol': lambda x: x['column'] == 1,
              'twocol': lambda x: x['column'] == 2,
              'boundary': lambda x: abs(float(x['loc'])) > 0.8,
              'old': lambda x: x['old'] == 1,
              'not_out_of_range': lambda x: x['out_of_range'] == 0,
              'no_obs_not_old_over_60':
                  lambda x: (x['obs_car'] == 0 and x['obs_human'] == 0 and x[
                      'old'] == 0 and x['zebra_ratio'] >= 60)
              }


def load_yaml():
    with open(config_file, 'r') as stream:
        options = yaml.load(stream)
    return options


def collect_all_db(data_dir):
    total_db = {}
    child_dirs = glob.glob(os.path.join(data_dir, '*'))

    for dir in child_dirs:
        db_file = os.path.join(dir, 'db.json')
        try:
            with open(db_file, 'r') as f:
                loaded = json.load(f)
        except Exception as e:
            print('Failed to open database file {}: {}'.format(db_file, e))
        else:
            total_db = {**total_db, **loaded}

    count = 0
    for name in total_db:
        count = count + 1

    return total_db


def merge_list(list):
    merged = []
    for elem in list:
        merged = merged + elem
    return merged


def choose_process():
    print('\n------- additional process -------')
    print('* Just Enter for skip each process')
    print('[1] Resize with fixed ratio')
    resize_width = input('  width: ')
    print('[2] Cut off upper img')
    cut_height = input('  lower height: ')
    print('[3] Grayscale')
    grayscale = input('  Yes = 1: ')

    if len(resize_width) > 0:
        resize_width = int(resize_width)
    if len(cut_height) > 0:
        cut_height = int(cut_height)
    if grayscale == '1':
        grayscale == 1

    print(resize_width, cut_height, grayscale)
    return resize_width, cut_height, grayscale


def show_and_pick_filters(filterlist):
    picked = []
    cnt = 0
    print('\n------- filter lists -------')

    for fil in filterlist:
        cnt = cnt + 1
        print('[' + str(cnt) + '] ', fil)

    print('----------------------------')
    print('select filters (ex: 1 2 3 4 5)')
    picked_num = input('└─ here: ')
    picked_num_list = picked_num.split(' ')

    filter_keys = list(filterlist.keys())
    # print(filter_keys)

    print('\n------- selected filters -------')
    for num in picked_num_list:
        key = filter_keys[int(num) - 1]
        print('[' + num + ']', key)
        picked.append(key)
    print('--------------------------------\n')

    return picked


#   This function is copy-pasted from preprocess.py. Adapt it appropriately in
#   the context of this feature so that additional resizing, contrasting,
#   gray-scaling, etc. can be done in this step. -- TJ

def process(img, processes):
    width, height, gray = processes
    # resizing
    if width > 0:
        img = scipy.misc.imresize(img, (int(width * 1.3333), width))
        H, W = img.shape[:2]
    # cut
    if height > 0:
        img = img[int(H - height):, :]
    # adjust
    if gray == 1:
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        img = cv2.equalizeHist(gray_img)

    return img


class DBMS(object):
    def __init__(self, data_dir, picked_filters, picked_process):
        self.child_dirs = glob.glob(os.path.join(data_dir, '*'))
        self.filters = picked_filters  # keys
        self.processes = picked_process
        self.query_list = {}

    def __load(self, dir):
        db_file = db_file = os.path.join(dir, 'db.json')
        try:
            with open(db_file, "r") as read_file:
                # list of metadata dictionaries
                return json.load(read_file).values()
        except Exception as e:
            print('Failed to open database file {}: {}'.format(db_file, e))

    def query(self):
        print(self.filters)
        for dir in self.child_dirs:
            for item in self.__load(dir):
                if not item['is_input_finished']:
                    continue

                suc = True
                try:
                    for filt in self.filters:
                        suc = suc and filterlist[filt](item)

                    if suc:
                        img_path = os.path.join(dir, 'labeled', item['filehash'])
                        print('Success: ' + img_path)

                        self.query_list[img_path] = (item['loc'], item['ang'])

                except:
                    print('Fail: ' + item['filehash'])
                    continue

            # print(query_list)
            print('Selected data: ', len(self.query_list))

    def make_npy(self):
        train_hash = []
        y_train = []
        cv2.namedWindow('tool')

        for item in self.query_list:
            img_path = item

            try:
                img = imread(img_path, mode='RGB')
                cv2.imshow('tool', img)
            except Exception:
                # print('Fail: ' + hash)
                continue

            # print('Success: ' + hash)
            label = [float(self.query_list[item][0]), float(self.query_list[item][1])]

            # additional process (resize, cut, grayscale)
            img = process(img, self.processes)
            train_hash.append(img)
            y_train.append(label)

        cnt = len(train_hash)
        print('Packed data: ', cnt)

        nowDatetime = self.__write_log(cnt)
        save_prefix = os.path.join(ROOT_DIR, 'npy', nowDatetime)
        print(save_prefix)
        np.save(save_prefix + '_X.npy', train_hash)
        np.save(save_prefix + '_Y.npy', y_train)

    def __write_log(self, num):
        now = datetime.datetime.now()
        nowDatetime = now.strftime('%Y-%m-%d__%H-%M-%S')

        with open('./makenp_log.txt', "a") as f:
            f.write(
                nowDatetime + '\t' + str(num) + '\t' + str(self.filters) + '\n')

        return nowDatetime


def make_npy_file(options, picked_filters, picked_process):
    """ the actual 'main' function. Other modules that import this module shall
    call this as the entry point. """
    data_dir = os.path.join(ROOT_DIR, options['data_dir'])
    db = DBMS(data_dir, picked_filters, picked_process)
    db.query()
    db.make_npy()


def main():
    options = load_yaml()
    picked_filters = show_and_pick_filters(filterlist)  # key
    picked_process = choose_process()
    make_npy_file(options, picked_filters, picked_process)


if __name__ == "__main__":
    main()