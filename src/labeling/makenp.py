import os, sys, copy
import argparse
import logging
from typing import Tuple, List, Dict
import datetime
import numpy as np
from labeling.database import DBMS, get_filter_list

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(BASE_DIR, "..", "..")

now = datetime.datetime.now().strftime('%y-%m-%d-%H-%M')
logger = logging.getLogger('make_numpy')


def show_and_pick_filters(filter_list):
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
    filter_keys = list(filter7_list.keys())
    # print(filter_keys)

    picked = []
    print('\n------- selected filters -------')
    for filter_id in filter_ids:
        key = filter_keys[filter_id - 1]
        print('[{}] {}'.format(filter_id, key))
        picked.append(key)
    print('--------------------------------\n')

    return picked


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


def make_npy(db, keys: List[str], width: int, height: int,
             grayscale: bool, output_dir: str, filename_prefix=''):

    xs, ys = db.get_npy(keys, width, height, grayscale)
    
    # npy file name convention
    x_name = os.path.join(output_dir, filename_prefix + '_x.npy')
    y_name = os.path.join(output_dir, filename_prefix + '_y.npy')

    print(x_name)
    logger.info("saving at " + x_name)
    np.save(x_name, xs)
    logger.info("saving at " + y_name)
    np.save(y_name, ys)


def make_npy_file(args):
    data_dir = os.path.join(BASE_DIR, args.dataset_dir)

    db = DBMS(data_dir)
    db.load_database()
    filter_list = get_filter_list()

    if args.cross_val:
        logger.info('Generating train/test numpy files with a ratio'
                    'of {}'.format(args.ratio))
        train_keys, val_keys = db.get_train_val_keys(args.ratio)
        make_npy(db, train_keys, args.width, args.height, args.grayscale,
                 args.output_dir, now + '-train')
        make_npy(db, val_keys, args.width, args.height, args.grayscale,
                 args.output_dir, now + '-val')
    else:
        selected_filters = show_and_pick_filters(filter_list)
        logger.info("Selected filters: " + str(selected_filters))
        keys = db.filter_data(selected_filters)
        make_npy(db, keys, args.width, args.height, args.grayscale,
                 args.output_dir, 'filter{}-{}'.format(len(selected_filters), now))
    logger.info('Finished at ' + str(now))


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

