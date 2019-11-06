import json
import pandas as pd
import numpy as np
import scipy
import cv2
import matplotlib
import matplotlib.pyplot as plt
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

now = datetime.datetime.now().strftime('%y-%m-%d-%H-%M')
makenp_logger = logging.getLogger('make_numpy')
stats_logger = logging.getLogger('DB_stats')


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


def get_filter_list():
    return filter_list


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

    def get_npy(self, keys: List[str], width: int, height: int,
                grayscale: bool):
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
                assert len(img.shape) >= 2
            except Exception as e:
                fail_cnt += 1
                continue
            if not ('loc' in entry and 'ang' in entry):
                fail_cnt += 1
                continue
            xs.append(self.__process_img(img, width, height, grayscale))
            ys.append((entry['loc'], entry['ang']))
        if fail_cnt > 0:
            makenp_logger.error('Failed to process {} out of {} entries'.format(
                fail_cnt, len(keys)))

        return xs, ys

    def show_statistics(self, cron=False):
        now = datetime.datetime.now()
        nowDatetime = now.strftime('%Y-%m-%d')

        df = pd.DataFrame.from_dict(self.entries.values())

        columns = ['date', 'total', 'labeled', 'invalid', 'obs_car',
                   'obs_human', 'shadow', 'old', '1col', '2col', 'odd2col']
        label_range = {'loc': [-2.5, 2.5], 'ang': [-90, 90],
                       'pit': [-0.25, 1.25], 'roll': [-30, 30]}
        labels = ['loc', 'ang', 'pit', 'roll']

        stats = pd.DataFrame(index=range(1), columns=columns)
        stats['date'] = nowDatetime

        stats['total'] = df.shape[0]
        stats['labeled'] = df[df['is_input_finished']].shape[0]
        stats['invalid'] = df[df['invalid'] == 1].shape[0]
        # horizontal = df[df['horizontal'] == 1].shape[0]
        stats['obs_car'] = df[df['obs_car'] == 1].shape[0]
        stats['obs_human'] = df[df['obs_human'] == 1].shape[0]
        stats['shadow'] = df[df['shadow'] == 1].shape[0]
        stats['old'] = df[df['old'] == 1].shape[0]
        stats['1col'] = df[df['column'] == 1].shape[0]
        stats['2col'] = df[df['column'] == 2].shape[0]
        stats['odd2col'] = df[df['column'] == 2.5].shape[0]

        for label in labels:
            interval = (label_range[label][1] - label_range[label][0]) / 10.0

            for i in range(10):
                bucket = label + '_' + str(i)
                columns.append(bucket)
                b_range = [label_range[label][0] + i * interval,
                           label_range[label][0] + (i + 1) * interval]

                test = (df[label] >= b_range[0]) & (df[label] < b_range[1])
                stats[bucket] = df[test].shape[0]

        df_stats = pd.DataFrame(stats)

        if cron:
            with open('trend.csv', 'a', newline='') as f:
                df_stats.to_csv(f, header=False)

            self.show_label_scatter_plot(cron)

            with open('trend.csv', 'r') as f:
                df_trend = pd.read_csv(f)
                df_trend[['date', 'labeled']].plot.bar(x='date', y='labeled',
                                                       rot=0)

                figure_path = os.path.join('figure', 'num_labeled.png')
                plt.savefig(figure_path)

        else:
            print(df_stats)

        pass

    def show_label_scatter_plot(self, cron):
        """ show scatter plots for computed labels.
        2 plots: loc - ang / pit - roll
        """
        matplotlib.use('Agg')

        loc = []
        ang = []
        pit = []
        roll = []
        cnt = 0

        for item in self.entries.values():
            try:
                if item['invalid'] == 0:
                    loc.append(item['loc'])
                    ang.append(item['ang'])

                    pit.append(item['pit'] - 0.5)
                    roll.append(item['roll'])
            except Exception as e:
                continue

        '''
        print('loc', max(loc), min(loc))
        print('ang', max(ang), min(ang))
        print('pit', max(pit), min(pit))
        print('roll', max(roll), min(roll))
        '''

        plt.figure(figsize=(20, 8))
        # loc, ang
        plt.subplot(121)
        plt.scatter(loc, ang, s=3)
        plt.xlim((-2.5, 2.5))
        plt.ylim((-90, 90))
        plt.xlabel('loc')
        plt.ylabel('ang ($^{\circ}$)')
        plt.title('location ─ angle')

        # pit, roll
        plt.subplot(122)

        plt.scatter(pit, roll, s=3)
        plt.xlim((-0.75, 0.75))
        plt.ylim((-30, 30))

        # plt.axis(option='auto')
        plt.xlabel('pit')
        plt.ylabel('roll ($^{\circ}$)')
        plt.title('pitch ─ roll')

        if cron:
            now = datetime.datetime.now()
            nowDatetime = now.strftime('%Y-%m-%d')

            if not os.path.exists(os.path.join(BASE_DIR, 'figure')):
                os.mkdir(os.path.join(BASE_DIR, 'figure'))

            figure_path = os.path.join('figure', 'label_' + nowDatetime + '.png')
            plt.savefig(figure_path)
        else:
            plt.savefig('stats_label_figure.png')
            plt.show()

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

    @staticmethod
    def show_proportion_bar(target, total):
        # 100% / 25 blocks -> 1% / 0.25 block
        if total == 0:
            blocks = 0
        else:
            proportion = 100 * float(target) / total
            blocks = math.ceil(proportion * 0.25)

        bar = '=' * blocks + '.' * (25 - blocks) + ' [ ' + str(target) +\
            ' / ' + str(total) + ' ]'


def setup_logger(logger, log_file_path: str):
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


def show_statistics(args):
    return


def main():
    parser = argparse.ArgumentParser()
    # parser.add_argument('dataset_dir', type=str, help="dataset directory")
    parser.add_argument('--stats', '-s', action='store_true')
    parser.add_argument('--stats_visualize', '-sv', action='store_true')
    parser.add_argument('--stats_cron', '-sc', action="store_true")

    args = parser.parse_args()
    data_dir = os.path.join(BASE_DIR, 'dataset')
    db = DBMS(data_dir)
    db.load_database()

    if args.stats:
        setup_logger(stats_logger, os.path.join(BASE_DIR, str(now) + '.log'))
        db.show_statistics()
    elif args.stats_cron:
        setup_logger(stats_logger, os.path.join(BASE_DIR, str(now) + '.log'))
        db.show_statistics(args.stats_cron)
    elif args.stats_visualize:
        pass


if __name__ == "__main__":
    main()