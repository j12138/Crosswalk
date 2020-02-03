import json, yaml, csv
import pandas as pd
import numpy as np
import scipy
import cv2, hashlib
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
from tqdm import tqdm
from typing import Tuple, List, Dict
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))
from ml.evaluate import predict_by_model, load_model
from labeling.compute_label_lib import compute_all_labels

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(BASE_DIR, "..", "..")

now = datetime.datetime.now().strftime('%y-%m-%d-%H-%M')
makenp_logger = logging.getLogger('make_numpy')
stats_logger = logging.getLogger('DB_stats')


filter_list = {
    'all': lambda x: True,
    'shadow': lambda x: x['shadow'] == 1,
    'obstacle': lambda x: x['obs_car'] == 1 and x['obs_human'] == 1,
    'car': lambda x: x['obs_car'] == 1,
    'human': lambda x: x['obs_human'] == 1,
    'onecol': lambda x: x['column'] == 1,
    'twocol': lambda x: x['column'] == 2,
    'odd2col': lambda x: x['column'] == 2.5,
    'old': lambda x: x['old'] == 1,
    'right_top': lambda x: x['loc'] >= 0.5 and x['ang'] >= 20.0,
    'left_bottom': lambda x: x['loc'] <= -0.8 and x['ang'] <= -20.0,
    'loc_out': lambda x: x['loc'] >= 8.0 and x['loc'] <= 100.0,
    'ang_out': lambda x: x['ang'] >= 70.0 or x['ang'] <= -70.0,
    'good_eval': lambda df: df[df['diff_loc'] <= 1.0][df['diff_loc'] >= -1.0][df['in_loc'] <= 1.5][df['in_loc'] >= -1.5],
    'custom': lambda x: x['filehash'] in ['4a0ca30e6da6eda9bddd52eccfcad541'],
    'except_left_bot': lambda x: x['loc'] > -0.5 or x['ang'] > -20,
    'except_right_top': lambda x: x['loc'] < 1.0 or x['ang'] < 20,
    'clip_loc': lambda x: x['loc'] <= 2.0 and x['loc'] >= -2.0,
    'except_corner': lambda x: x['corner-case'] == 0 and x['invalid'] == 0,
    'corner_invalid': lambda x: x['corner-case'] == 1 or x['invalid'] == 1,
    'high_roll': lambda x: x['roll'] >= 40 and x['roll'] < 50,
    'except_high_roll': lambda x: x['roll'] <= 30
}


def get_filter_list():
    return filter_list


def show_and_pick_filters(filter_list):
    """ show pre-declared(AT TOP) filter lists and get user's choice.
    :return: list of picked filters
    """
    print('\n------- filter lists -------')
    print(enumerate(filter_list))
    for i, filter_name in enumerate(filter_list):
        print('[{}] {}'.format(i + 1, filter_name))

    print('----------------------------')
    print('- You can get certain data group which meets the selected filters')
    print('- Multiple filters are allowed with blank(space) intervals')
    print('select filters (ex: 1 2 3 4 5)')
    
    picked_num = input('* here: ')
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


def display_selected(x, y, yp, filename):           
    """ Display selected input images in a grid.
    :param xs: prioritized inputs                                         
    :param ys: predictions                                                      
    :param dims: tuple of length 2 with (#row, #column) for images grid        
    """                                                                        
                                  
    assert len(x) == len(y) == len(yp)

    # determine grid size
    total_num = len(x)
    print('total:', total_num)
    if total_num < 15:
        dims = [1, total_num]
    else:
        dims = [int(total_num / 15), 15]
                                                                                
    # Annotate                                                                 
    imgs = copy.copy(x[:dims[0] * dims[1]])                                    
    FONT = cv2.FONT_HERSHEY_SIMPLEX
    for i in range(dims[0] * dims[1]):                                         
        text = "P: {:1.3f}, {:1.3f}".format(yp[i][0], yp[i][1])   
        cv2.putText(imgs[i], text, (10,15), FONT, 0.4, (180,0,0), 2,            
                2) 
        cv2.putText(imgs[i], text, (10,15), FONT, 0.4, (255,255,255), 1,            
                2) 
        text = "T: {:1.3f}, {:1.3f}".format(y[i][0], y[i][1])              
        cv2.putText(imgs[i], text, (10,30), FONT, 0.4, (180,0,0), 2,            
                2)
        cv2.putText(imgs[i], text, (10,30), FONT, 0.4, (255,255,255), 1,            
                2)
                
    # Stack                                                                    
    stacked = []                                                               
    for i in range(10):                                                        
        # horizontally                                                         
        try:                                                                   
            row = np.concatenate(imgs[dims[1]*i:dims[1]*(i+1)], axis=1)        
            stacked.append(row)                                                
        except:                                                                
            break                                                              
    img = np.concatenate(stacked, axis=0)   # vertically                       
    cv2.imwrite(filename + '_' + now + '.png', img)


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
        if not os.path.isfile(db_file):
            makenp_logger.error('No such db file: ' + db_file)
            return
        try:
            new_entries = {}
            with open(db_file, "r") as read_file:
                # list of metadata dictionaries
                entries = json.load(read_file)
                id_num = 0

                for key in entries:
                    '''
                    id_num += 1
                    entry = entries[key].copy()
                    # re-hashing
                    new_string = os.path.basename(batch_path) + str(id_num)
                    new_hash = str(hashlib.md5(new_string.encode()).hexdigest())
                    img_path = batch_path
                    
                    '''
                    if os.path.isfile(os.path.join(batch_path, 'labeled', key)):
                        img_path = os.path.join(batch_path, 'labeled')
                    elif os.path.isfile(os.path.join(batch_path, 'preprocessed', key)):
                        img_path = os.path.join(batch_path, 'preprocessed')
                    else:
                        img_path = ''
                        print('No img file found! :', batch_path, key)
                        
                    entries[key]['img_path'] = os.path.join(img_path, key)

                    '''
                    if not 'invalid' in entries[key].keys():
                        entries[key]['invalid'] = 0 

                    if not 'corner-case' in entries[key].keys():
                        entries[key]['corner-case'] = 0 
                    '''
                    '''
                    os.rename(os.path.join(img_path, key), os.path.join(img_path, new_hash))

                    entry['id'] = id_num
                    entry['filehash'] = new_hash
                    entry['img_path'] = os.path.join(img_path, new_hash)
                    new_entries[new_hash] = entry
                    '''
            with open(db_file, "w") as write_file:
                json.dump(entries, write_file)
            

            return entries
        except Exception as e:
            print('Failed to open database file {}: {}'.format(db_file, e))

    def load_database(self) -> None:
        """ Load the whole database throughout all the batches """
        cnt = 0

        with open('DB_batch_stats.csv', 'w', newline='') as f:
            for batch_dir in self.batch_dirs:
                batch_db = {}
                batch_db = self.__load_db_in_batch(batch_dir)

                if batch_db:
                    '''
                    for key, entry in batch_db.items():
                        iter_key = key
                        while iter_key in self.entries:
                            print(self.entries[key]['img_path'], ' > ', entry['img_path'])
                            batch_db[iter_key + 'z'] = batch_db.pop(iter_key)
                            iter_key = iter_key + 'z'
                    '''

                    cnt = cnt + len(batch_db)
                    prev = len(self.entries)
                    self.entries.update(batch_db)
                    now = len(self.entries)
                    
                    if (now - prev) < len(batch_db):
                       print('!something overlapped')

                else:
                    print('db error:', batch_dir)

                num_img = len(glob.glob(os.path.join(batch_dir, 'labeled', '*')))
                wr = csv.writer(f)
                wr.writerow([os.path.basename(batch_dir), num_img, len(batch_db)])

        print(len(self.entries), cnt)
                

    def filter_data(self, filter_names: List[str]) -> List[str]:
        """ Collect filtered data at self.query_list.
        :param filter_names: A list of filter names
        :return: a list of keys for the DB entries that satisfy all the filter
        conditions
        """

        filtered = {}

        # iteratively apply selected filters
        '''
        filtered = {entry: filtered[entry] for entry in filtered if
                    (filtered[entry]['is_input_finished'] is True) and
                    (_filter(filtered[entry]) is True)}
        '''

        for key in self.entries:
            check = self.entries[key]['invalid'] == 0
            for filter_name in filter_names:
                _filter = filter_list[filter_name]
                try:
                    check = check and _filter(self.entries[key])
                except Exception as e:
                    makenp_logger.error(self.entries[key]['img_path'])
                    check = False
                    continue
            
            if check:
                filtered[key] = self.entries[key]

        print('Filtered data: {}'.format(len(filtered)))

        return filtered.keys()

    def get_train_val_keys(self, keys = None, ratio: float = 0.2) \
            -> Tuple[List[str], List[str]]:
        """ Randomly split the dataset into two (train/val) by the given ratio.
        The specified ratio is for the validation dataset.
        :param ratio: the ratio of the whole data to set aside for validation
        :return: a Tuple of two key lists, one for train and the other for val.
        """
        assert 0.0 < ratio <= 1.0
        if keys == None:
            labeled_entry_keys = [key for key, entry in self.entries.items()
                              if entry['is_input_finished'] is True]
        else:
            labeled_entry_keys = [key for key in keys
                              if self.entries[key]['is_input_finished'] is True]
        random.shuffle(labeled_entry_keys)
        cut_index = math.floor(len(labeled_entry_keys) * ratio)
        return labeled_entry_keys[cut_index:], labeled_entry_keys[:cut_index]

    def get_good_eval_keys(self, eval_df):

        good_eval = list(filter_list['good_eval'](eval_df)['hashname'])
        print(len(good_eval))

        # self.model_evaluation('./ml/trainings/2020-jan7/', 0.1, custom_keys=good_eval)
        train_key, val_key = self.get_train_val_keys(keys=good_eval, ratio=0.05)

        xs, ys, keys = self.get_npy(train_key, 150, 199, False)
        now = datetime.datetime.now()

        filename_prefix = now.strftime('%Y-%m-%d') + '_good_eval_train'
        x_name = os.path.join(BASE_DIR, 'npy', filename_prefix + '_x.npy')
        y_name = os.path.join(BASE_DIR, 'npy', filename_prefix + '_y.npy')
        np.save(x_name, xs)
        np.save(y_name, ys)

        xs, ys, keys = self.get_npy(val_key, 150, 199, False)

        filename_prefix = now.strftime('%Y-%m-%d') + '_good_eval_val'
        x_name = os.path.join(BASE_DIR, 'npy', filename_prefix + '_x.npy')
        y_name = os.path.join(BASE_DIR, 'npy', filename_prefix + '_y.npy')
        np.save(x_name, xs)
        np.save(y_name, ys)

        return

    def get_npy(self, keys: List[str], width: int, height: int,
                grayscale: bool, normalize=False):
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
        packed_keys = []
        fail_cnt = 0
        keys = list(keys)

        for i in tqdm(range(len(keys))):
            key = keys[i]
            entry = self.entries[key]
            try:  # is it valid img?
                img = imread(entry['img_path'], mode='RGB')
                assert len(img.shape) >= 2
            except Exception as e:
                print(e)
                fail_cnt += 1
                continue
            if not ('loc' in entry and 'ang' in entry):
                fail_cnt += 1
                continue
            xs.append(self.__process_img(img, width, height, grayscale))
            is_2col = int(entry['column'] != 1)
            if normalize:
                # clip (optional)
                n_loc = entry['loc'] / 2.0
                n_ang = entry['ang'] / 60.0
                ys.append((n_loc, n_ang, is_2col))
            else:
                ys.append((entry['loc'], entry['ang'], is_2col))
            packed_keys.append(key)

        if fail_cnt > 0:
            makenp_logger.error('Failed to process {} out of {} entries'.format(
                fail_cnt, len(keys)))

        return xs, ys, packed_keys

    def show_statistics(self, cron=False, visualize=False):
        now = datetime.datetime.now()
        nowDatetime = now.strftime('%Y-%m-%d')
        trend_file = os.path.join(BASE_DIR, 'trend.csv')

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
            with open(trend_file, 'a', newline='') as f:
                df_stats.to_csv(f, header=False)

            self.show_label_scatter_plot(cron)

            with open(trend_file, 'r') as f:
                df_trend = pd.read_csv(f)
                df_trend[['date', 'labeled']].plot.bar(x='date', y='labeled',
                                                       rot=0)

                figure_path = os.path.join(BASE_DIR, 'figure', 'num_labeled.png')
                plt.savefig(figure_path)

        else:
            print(df_stats)

        if visualize:
            matplotlib.use('Agg')
        return

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
        plt.scatter(loc, ang, s=2)
        #plt.xlim((-2.5, 2.5))
        plt.ylim((-90, 90))
        plt.xlabel('loc')
        plt.ylabel('ang ($^{\circ}$)')
        plt.title('location ─ angle')

        # pit, roll
        plt.subplot(122)

        plt.scatter(pit, roll, s=2)
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

            figure_path = os.path.join(BASE_DIR, 'figure', 'label_' + nowDatetime + '.png')
            plt.savefig(figure_path)
        else:
            figure_path = os.path.join(BASE_DIR, 'figure', 'label_' + nowDatetime + '.png')
            plt.savefig(figure_path)
            plt.show()

    def pick_out_filtered(self, filters, OUT=False):
        print(filters)
        outlier_keys = list(self.filter_data(filters))
        # outlier_keys.extend(list(self.filter_data(['apple'])))
        # print(outlier_keys)

        filtered_addr = []

        with open(os.path.join(BASE_DIR, 'outlier_addr.txt'), "w") as f:

            for key in outlier_keys:
                batch_name = self.entries[key]['img_path'].split('\\')[-3]

                #print(self.entries[key]['img_path'])
                filtered_addr.append((key, batch_name))
                f.write(key + ',' + batch_name + '\n')

        return filtered_addr

    def correct_labeling_order(self):
        for item in self.entries.values():
            self.__correct_points_order(item)
        return

    def __correct_points_order(self, db_item):
        if db_item['is_input_finished'] and \
            (db_item['column'] == 1 or db_item['column'] == 2):
            all_points = db_item['all_points']
            new_points = [[0, 0]] * 4
            
            if all_points[0] > all_points[2]:
                new_points[0] = all_points[2]
                new_points[1] = all_points[3]
                new_points[2] = all_points[0]
                new_points[3] = all_points[1]

                print(all_points, new_points)

        return new_points

    def evaluate_model(self, model, options, ratio=0.0, custom_keys=None, xs=None, ys=None):
        export = False

        if (xs != None) and (ys != None):
            export = True
            keys = None
        else:
            # 1. make all DB to np array (with normalization)
            xs, ys, keys = self.__make_all_db_npy(ratio, custom_keys, options)

        # 2. evaluation(from evaluation.py)
        predict = predict_by_model(np.asarray(xs), np.asarray(ys), model)

        # 3. make out file (csv/excell)
        df = self.__make_dataframe_from_evaluation(ys, predict, keys, export)
        if export:
            excel_name = 'train_eval_' + now + '.xlsx'
        else:
            excel_name = 'model_eval_' + now + '.xlsx'
        df.to_excel(os.path.join(BASE_DIR, excel_name))

        # filter outlier
        outlier_idx = self.__filter_evaluation_outlier(df)
        x_out = [xs[i] for i in outlier_idx]
        y_out = [ys[i] for i in outlier_idx]
        yp_out = [predict[i] for i in outlier_idx]
        display_selected(x_out, y_out, yp_out, 'grid')

        # correlation analysis
        df_corr = pd.DataFrame({'diff_loc': df.corrwith(df.diff_loc),
                                'diff_ang': df.corrwith(df.diff_ang),
                                'abs_diff_loc': df.corrwith(df.abs_diff_loc),
                                'abs_diff_ang': df.corrwith(df.abs_diff_ang)})
        print(df_corr)

        # visualization
        self.__save_evaluation_plot(df)

        return df

    def __make_all_db_npy(self, ratio, custom_keys, options):
        keys = self.filter_data(['except_corner'])
        print('except_corner', len(keys))

        if ratio > 0:
            assert 0.0 < ratio <= 1.0
            keys = self.get_train_val_keys(keys=keys, ratio=ratio)[1]
        else:
            keys = list(self.entries.keys())  # all keys in DB
        if custom_keys is not None:
            keys = custom_keys
        xs, ys, keys = self.get_npy(keys, options['width'], options['height'],
                              options['grayscale'], normalize=True)
        
        return xs, ys, keys

    def __make_dataframe_from_evaluation(self, ys, predict, keys, export=False):
        total_eval = []
        if export:
            columns = ['in_loc', 'in_ang', 'out_loc', 'out_ang']
        else:
            columns = ['hashname', 'in_loc', 'in_ang', 'out_loc', 'out_ang',
                        'column', 'obs_car',
                        'obs_human', 'shadow', 'old', 'pit', 'roll']

        for i in range(len(ys)):
            if export:
                item = [ys[i][0] * 2.0, ys[i][1] * 60.0,
                    predict[i][0], predict[i][1]]
                total_eval.append(item)
                continue
            hash = keys[i]
            data = self.entries[hash]
            item = [hash, ys[i][0] * 2.0, ys[i][1] * 60.0,
                    predict[i][0], predict[i][1],
                    data['column'], data['obs_car'],
                    data['obs_human'], data['shadow'], data['old'],
                    data['pit'], data['roll']]
            total_eval.append(item)

        df = pd.DataFrame(total_eval, columns=columns)
        df['diff_loc'] = df['out_loc'] - df['in_loc']
        df['diff_ang'] = df['out_ang'] - df['in_ang']
        df['abs_diff_loc'] = abs(df['out_loc'] - df['in_loc'])
        df['abs_diff_ang'] = abs(df['out_ang'] - df['in_ang'])

        return df

    def __filter_evaluation_outlier(self, df):
        # outliers = df[df['diff_loc'] >= 1.0]['hashname']
        print('bbbbb')
        over1 = list(df[df['diff_loc'] >= 1.0].index)
        under1 = list(df[df['diff_loc'] <= -1.0].index)
        outlier_idx = over1 + under1
        # print(outlier_idx)
        '''
        with open(os.path.join(BASE_DIR, 'eval_outlier_over1.txt'), "w") as f:
            for key in outliers:
                img_path = self.entries[key]['img_path']
                batch_name = self.__get_batch_name(img_path)
                f.write(key + ',' + batch_name + '\n')
        '''
        return outlier_idx

        # outliers = df[df['diff_loc'] < -1.0]['hashname']
        '''
        with open(os.path.join(BASE_DIR, 'eval_outlier_under-1.txt'), "w") as f:
            for key in outliers:
                img_path = self.entries[key]['img_path']
                batch_name = self.__get_batch_name(img_path)
                f.write(key + ',' + batch_name + '\n')
        '''

    def __save_evaluation_plot(self, df):
        matplotlib.use('Agg')
        plot_cols = ['in_loc', 'in_ang']

        n_col = len(plot_cols)
        fig, axes = plt.subplots(nrows=2, ncols=3)
        figsize = (12, 8)
        
        for i in range(n_col):
            df.plot.scatter(plot_cols[i], 'diff_loc', s=1, ax=axes[0][i], figsize=figsize)
            df.plot.scatter(plot_cols[i], 'diff_ang', s=1, ax=axes[1][i], figsize=figsize)
        df.plot.scatter('in_loc', 'out_loc', s=1, ax=axes[0][2], figsize=figsize)
        df.plot.scatter('in_ang', 'out_ang', s=1, ax=axes[1][2], figsize=figsize)

        fig.savefig(os.path.join(BASE_DIR, 'model_eval_' + now + '_.png'))

    def make_evaluation_plot(self, xs, ys, model_path):
        predict = predict_by_model(np.asarray(xs), np.asarray(ys), model_path)
        
        total_eval = []
        columns = ['in_loc', 'in_ang', 'out_loc', 'out_ang']
        for i in range(len(ys)):
            item = [ys[i][0] * 2.0, ys[i][1] * 60.0,
                    predict[i][0], predict[i][1]]
            total_eval.append(item)
        df = pd.DataFrame(total_eval, columns=columns)
        df['diff_loc'] = df['out_loc'] - df['in_loc']
        df['diff_ang'] = df['out_ang'] - df['in_ang']

        matplotlib.use('Agg')
        plot_cols = ['in_loc', 'in_ang']

        n_col = len(plot_cols)
        fig, axes = plt.subplots(nrows=2, ncols=3)
        figsize = (12, 8)
        
        for i in range(n_col):
            df.plot.scatter(plot_cols[i], 'diff_loc', s=1, ax=axes[0][i], figsize=figsize)
            df.plot.scatter(plot_cols[i], 'diff_ang', s=1, ax=axes[1][i], figsize=figsize)
        df.plot.scatter('in_loc', 'out_loc', s=1, ax=axes[0][2], figsize=figsize)
        df.plot.scatter('in_ang', 'out_ang', s=1, ax=axes[1][2], figsize=figsize)

        fig.savefig('evaluation_from_val.png')

    @staticmethod
    def __get_batch_name(img_path):
        return img_path.split('\\')[-3]

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


def main():
    parser = argparse.ArgumentParser()
    # parser.add_argument('dataset_dir', type=str, help="dataset directory")
    parser.add_argument('data_dir', type=str)
    parser.add_argument('--stats', '-s', action='store_true')
    parser.add_argument('--stats-cron', '-sc', action="store_true")
    parser.add_argument('--stats-visualize', '-sv', action="store_true")
    parser.add_argument('--outlier', '-o', action="store_true")
    parser.add_argument('--filter', '-f', action="store_true")
    parser.add_argument('--model-eval', '-e', type=str,
                        help="get model evaluation w.r.t. whole DB \n" +
                        "model directory path should be passed")
    parser.add_argument('--eval-part', '-p', type=float)
    parser.add_argument('--good_eval', '-ge', type=str,
                        help="get npy with data which have good evaluation value\n" +
                            "conditions are hard-coded")

    args = parser.parse_args()
    # data_dir = os.path.join(BASE_DIR, 'dataset')
    data_dir = 'F:\\dataset'
    db = DBMS(data_dir)
    db.load_database()

    if args.stats:
        # setup_logger(stats_logger, os.path.join(BASE_DIR, str(now) + '.log'))
        db.show_statistics()
    elif args.stats_cron:
        # setup_logger(stats_logger, os.path.join(BASE_DIR, str(now) + '.log'))
        db.show_statistics(args.stats_cron)
    elif args.outlier:
        outlier_filters = ['right_top', 'left_bottom']
        db.pick_out_filtered(outlier_filters, True)
        # db.correct_labeling_order()
    elif args.filter:
        picked_filters = show_and_pick_filters(filter_list)
        db.pick_out_filtered(picked_filters)
    elif args.model_eval:
        print('-- model evaluation start --')
        config_file = os.path.join(args.model_eval, 'config.yaml')
        with open(config_file, 'r') as stream:
            options = yaml.load(stream)
        model = load_model(args.model_eval)

        if args.eval_part:
            db.evaluate_model(model, options, args.eval_part)
        else:
            db.evaluate_model(model, options)
    elif args.good_eval:
        if args.eval_part:
            eval_df = db.evaluate_model(args.good_eval, args.eval_part)
        else:
            eval_df = db.evaluate_model(args.good_eval)
        db.get_good_eval_keys(eval_df)
    elif args.stats_visualize:
        db.show_statistics(visualize=True)
    else:
        pass
        # db.correct_labeling_order()


if __name__ == "__main__":
    main()
