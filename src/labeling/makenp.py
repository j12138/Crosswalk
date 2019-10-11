import json
import numpy as np
import yaml
import scipy
import cv2
from scipy.misc import imread
import datetime
import glob
import os, sys, copy
import random
import argparse
import math
import logging
from typing import Tuple, List, Dict

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(BASE_DIR, "..", "..")

now = datetime.datetime.now().strftime('%Y-%m-%d %H-%M-%S')
logger = logging.getLogger('make_numpy')


filter_list = {
    'apple': lambda x: x['Make'] == 'Apple',
    'samsung': lambda x: x['Make'] == 'samsung',
    'shadow': lambda x: x['shadow'] == 1,
    'obstacle': lambda x: x['obs_car'] == 1 and x['obs_human'] == 1,
    'car': lambda x: x['obs_car'] == 1,
    'human': lambda x: x['obs_human'] == 1,
    'onecol': lambda x: x['column'] == 1,
    'twocol': lambda x: x['column'] == 2,
    'odd2col': lambda x: x['column'] == 3,
    'boundary': lambda x: abs(float(x['loc'])) > 0.8,
    'old': lambda x: x['old'] == 1,
    'right_top': lambda x: x['loc'] >= 0.3 and x['ang'] >= 10.0,
    'left_bottom': lambda x: x['loc'] <= -0.2 and x['ang'] <= -30.0
}


def show_and_pick_filters():
    """ show pre-declared(AT TOP) filter lists and get user's choice.
    :return: list of picked filters
    """
    print('\n------- filter lists -------')
    print(enumerate(filter_list))
    for i, filter_name in enumerate(filter_list):
        print('[{}] {}'.format(i + 1, filter_name))

    print('----------------------------')
    print('select filters (ex: 1 2 3 4 5)')
    picked_num = input('└─ here: ')
    filter_ids = [int(i) for i in picked_num.split(' ')]
    filter_keys = list(filter_list.keys())
    # print(filter_keys)

    picked = []
    print('\n------- selected filters -------')
    for filter_id in filter_ids:
        key = filter_keys[filter_id - 1]
        print('[{}] {}'.format(filter_id, key))
        picked.append(key)
    print('--------------------------------\n')

    return picked


class DBMS(object):
    """ Database interface """

    def __init__(self, data_dir):
        """
        :param data_dir: path for preprocessed data
        """
        self.db_filename = 'db.json'
        self.entries = {} # DB entries. Dict[Dict]
        self.batch_dirs = glob.glob(os.path.join(data_dir, '*'))
        self.query_list = {}
        self.val_query_list = None

    # @staticmethod
    def __load_db_in_batch(self, batch_path: str) -> Dict[str, Dict]:
        """ A batch refers to a "batch" of dataset collected in a single
        burst. around 100 to a few hundreds of images are contained in a
        batch, typically.
        This function loads the dataset database stored in the given batch
        path directory.

        :param batch_path: current preprocessed dataset directory
        :return: Dict of db entries, where each entry is a dictionary.
        """
        db_file = os.path.join(batch_path, self.db_filename)
        try:
            with open(db_file, "r") as read_file:
                # list of metadata dictionaries
                entries = json.load(read_file)
                for key, entry in entries.items():
                    # recover the image path and add as a new column
                    entry['img_path'] = os.path.join(batch_path, 'labeled',
                                                     entry["filehash"])
                return entries
        except Exception as e:
            print('Failed to open database file {}: {}'.format(db_file, e))

    def load_database(self) -> None:
        """ Load the whole database throughout all the batches """
        for batch_dir in self.batch_dirs:
            self.entries.update(self.__load_db_in_batch(batch_dir))

    def filter_data(self, filter_names: List[str]) -> List[str]:
        """ Collect filtered data at self.query_list.

        :param filter_names: A list of filter names
        :return: a list of keys for the DB entries that satisfy all the filter
        conditions
        """
        filtered = copy.copy(self.entries)
        print(len(filtered))

        for filter_name in filter_names:

            # iteratively apply selected filters
            _filter = filter_list[filter_name]

            filtered = {entry: filtered[entry] for entry in filtered if
                        (filtered[entry]['is_input_finished'] is True) and
                        (_filter(filtered[entry]) is True)}

            print(len(filtered))

        return filtered.keys()

    def get_train_val_keys(self, ratio: float = 0.2) \
            -> Tuple[List[str], List[str]]:
        """ Randomly split the dataset into two (train/val) by the given ratio.
        The specified ratio is for the validation dataset.

        :param ratio: the ratio of the whole data to set aside for validation
        :return: a Tuple of two key lists, one for train and the other for val.
        """
        assert 0.0 < ratio <= 1.0
        labeled_entry_keys = [key for key, entry in self.entries.items()
                              if entry['is_input_finished'] is True]
        random.shuffle(labeled_entry_keys)
        cut_index = math.floor(len(labeled_entry_keys) * ratio)
        return labeled_entry_keys[cut_index:], labeled_entry_keys[:cut_index]

    def make_npy(self, keys: List[str], width: int, height: int,
                 grayscale: bool, output_dir: str, filename_prefix=''):
        """ Make npy files for training, from query_list

        :param keys: List of keys for the database entries
        :param width: width of the output image
        :param height: height of the output image. The proportion will be kept.
        :param grayscale: True to turn enable grayscale image
        :param output_dir: output directory
        :param filename_prefix: The file name prefix
        :return: None
        """
        xs, ys = [], []
        fail_cnt = 0

        for key in keys:
            entry = self.entries[key]
            try:  # is it valid img?
                img = imread(entry['img_path'], mode='RGB')
            except Exception as e:
                fail_cnt += 1
                continue
            xs.append(self.__process_img(img, width, height, grayscale))
            ys.append((entry['loc'], entry['ang']))
        if fail_cnt > 0:
            logger.warning('Failed to process {} out of {} entries'.format(
                fail_cnt, len(keys)))

        # npy file name convention
        x_name = os.path.join(output_dir, filename_prefix + '_x.npy')
        y_name = os.path.join(output_dir, filename_prefix + '_y.npy')

        print(x_name)
        logger.info("saving at " + x_name)
        np.save(x_name, xs)
        logger.info("saving at " + y_name)
        np.save(y_name, ys)

    @staticmethod
    def __process_img(img, width, height, grayscale):
        h, w = img.shape[:2]
        # resize
        if width > 0:
            img = scipy.misc.imresize(img, (int(width * 1.3333), width))
            h, w = img.shape[:2]
        # cut
        if height > 0:
            cutoff_upper = int((h - height) / 2)
            if cutoff_upper < 0:
                raise Exception('your height is shorter than resized height!')
            img = img[cutoff_upper:cutoff_upper + height, :]
        # adjust
        if grayscale == 1:
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            img = cv2.equalizeHist(gray_img)
            img = img[..., None]

        return img


def make_npy_file(args):
    data_dir = os.path.join(BASE_DIR, args.dataset_dir)

    db = DBMS(data_dir)
    db.load_database()

    if args.cross_val:
        logger.info('Generating train/test numpy files with a ratio'
                    'of {}'.format(args.ratio))
        train_keys, val_keys = db.get_train_val_keys(args.ratio)
        db.make_npy(train_keys, args.width, args.height, args.grayscale,
                    args.output_dir, 'train')
        db.make_npy(val_keys, args.width, args.height, args.grayscale,
                    args.output_dir, 'val')
    else:
        selected_filters = show_and_pick_filters()
        logger.info("Selected filters: " + str(selected_filters))
        keys = db.filter_data(selected_filters)
        db.make_npy(keys, args.width, args.height, args.grayscale,
                   'filter{}_{}'.format(len(selected_filters), now))
        db.make_npy(keys, args.width, args.height, args.grayscale,
                    args.output_dir)
    logger.info('Finished at ' + str(now))


def setup_logger(log_file_path: str):
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] : %(message)s')
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(filename=log_file_path)
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)
    logger.addHandler(sh)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('dataset_dir', type=str, help="dataset directory")
    parser.add_argument('output_dir', type=str, help="numpy output directory")
    parser.add_argument('--width', '-w', type=int, default=150,
                        help="image width")
    parser.add_argument('--height', '-H', type=int, default=200,
                        help="image height")
    parser.add_argument('--grayscale', '-g', action='store_true',
                        help="grayscale image")
    parser.add_argument('--cross-val', '-c', action='store_true',
                        help="Cross validation")
    parser.add_argument('--ratio', '-r', type=float, default=0.2,
                        help="Set-aside ratio")
    args = parser.parse_args()
    setup_logger(os.path.join(BASE_DIR, args.output_dir, str(now) + '.log'))
    make_npy_file(args)


if __name__ == "__main__":
    main()
