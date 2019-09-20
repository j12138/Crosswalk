import json
import yaml
from math import ceil
import matplotlib
import matplotlib.pyplot as plt
import glob
import os
import argparse
import pandas as pd
import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(BASE_DIR, "..")
config_file = os.path.join(BASE_DIR, 'config.yaml')


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--visualize', action="store_true")
    parser.add_argument('-c', '--cron', action="store_true")
    return parser.parse_args()


def collect_all_db(data_dir):
    """ collect and combine all existing DBs in preprocessed_data folder.
    :param data_dir: directory path of preprocessed data
    :return: combined DB
    """

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


def loadyaml():
    with open(config_file, 'r') as stream:
        options = yaml.load(stream)
    return options


def load_DB(options):
    with open(options['db_file'], "r") as db_file:
        db = json.load(db_file).values()
    return db


def show_proportion_bar(target, total):
    # 100% / 25 blocks -> 1% / 0.25 block
    if total == 0:
        blocks = 0
    else:
        proportion = 100 * float(target) / total
        blocks = ceil(proportion * 0.25)

    bar = '=' * blocks + '.' * (25 - blocks) + ' [ ' + str(target) +\
          ' / ' + str(total) + ' ]'

    return bar

def show_label_scatter_plot(db,cron=False):

    """ show scatter plots for computed labels.
        2 plots: loc - ang / pit - roll
    """


    matplotlib.use('Agg')

    loc = []
    ang = []
    pit = []
    roll = []
    cnt = 0

    for item in db:
        try:
            if item['invalid'] == 0:
                loc.append(item['loc'])
                ang.append(item['ang'])

                pit.append(item['pit'] - 0.5)
                roll.append(item['roll'])
        except:
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
        figure_path = os.path.join('figure', 'label_' + nowDatetime + '.png')
        plt.savefig(figure_path)
    else:
        plt.savefig('stats_label_figure.png')
        plt.show()


def show_total_stat(db):
    """ show overall statistics. (irrelevant to metadata, labels)
    :param db: combined DB
    :return cnt: total number of data
    :return labeled: number of labeled data
    """

    cnt = 0
    labeled = 0
    invalid = 0
    for item in db:
        if item['is_input_finished']:
            labeled = labeled + 1
            try:
                if item['invalid'] == 1:
                    invalid = invalid + 1
            except:
                pass
        cnt = cnt + 1

    print('total_#: ', cnt)
    print('labeled: ', labeled)
    print('invalid: ', invalid)
    print('valid(labeled): ' + show_proportion_bar(labeled-invalid, labeled))

    return cnt, labeled


def show_manual_meta_stat(db, total):
    """ show proportions of all manual metadata
    :param db: combined DB
    :param total: total number of data
    :return: None
    """

    obs_car = 0
    obs_human = 0
    shadow = 0
    one_column = 0
    two_column = 0
    odd_2column = 0

    old = 0

    for item in db:
        if not item['is_input_finished']:
            continue
        try:
            if item['obs_car'] == 1:
                obs_car = obs_car + 1
            if item['obs_human'] == 1:
                obs_human = obs_human + 1
            if item['shadow'] == 1:
                shadow = shadow + 1
            if item['column'] == 1:
                one_column = one_column + 1
            if item['column'] == 2:
                two_column = two_column + 1

            '''
            if 0 <= item['zebra_ratio'] <= 20:
                under_20 = under_20 + 1
            if 20 < item['zebra_ratio'] <= 40:
                under_40 = under_40 + 1
            if 40 < item['zebra_ratio'] <= 60:
                under_60 = under_60 + 1
            if 60 < item['zebra_ratio'] <= 80:
                under_80 = under_80 + 1
            if 80 < item['zebra_ratio']:
                over_80 = over_80 + 1
            '''

            if item['column'] == 2.5:
                odd_2column = odd_2column + 1
            if item['old'] == 1:
                old = old + 1
        except Exception as e:
            print('Fail: ' + item['filehash'])
            continue

    print('obs_car:  ', show_proportion_bar(obs_car, total))
    print('obs_human:', show_proportion_bar(obs_human, total))
    print('shadow:   ', show_proportion_bar(shadow, total))
    print('old:      ', show_proportion_bar(old, total), '\n')

    print('column:')
    print('  └─ [1]  ', show_proportion_bar(one_column, total))
    print('  └─ [2]  ', show_proportion_bar(two_column, total), '\n')
    print('  [1.5]', show_proportion_bar(odd_2column, total), '\n')
    

def show_exifmeta_stat(db, total):
    """ show exif metadata (internal info from imgs)
    :param db: combined DB
    :param total: total number of data
    :return: None
    """

    horizontal = 0
    Samsung = 0
    Apple = 0
    make_other = 0

    for item in db:
        try:
            if item['is_horizontal']:
                horizontal = horizontal + 1

            if item['Make'] == 'samsung':
                Samsung = Samsung + 1
            elif item['Make'] == 'Apple':
                Apple = Apple + 1
            else:
                make_other = make_other + 1

        except:
            print('Fail: ' + item['filehash'])
            continue

    print('horizontal:', show_proportion_bar(horizontal, total))
    print('\nMake')
    print('  Samsung:', show_proportion_bar(Samsung, total))
    print('  Apple:  ', show_proportion_bar(Apple, total))
    print('  Others: ', show_proportion_bar(make_other, total))


def show_db_stat(db):
    print('\n--------- total ---------\n')
    total, labeled = show_total_stat(db)

    print('\n--------- exif metadata ---------\n')
    show_exifmeta_stat(db, total)

    if total == 0:
        print('There are no data!')
        return

    print('\n--------- manual metadata (labeled) ---------\n')
    show_manual_meta_stat(db, labeled)
    show_label_scatter_plot(db)

    print('')


def labeling_progress_for_each_dir(db, dir, idx):
    total = 0

    for name in db.values():
        total = total + 1

    labeled = len(os.listdir(os.path.join(dir, 'labeled')))

    dir_name = os.path.basename(dir)
    print('[' + str(idx) + ']', dir_name, ':', show_proportion_bar(labeled, total))

    return total, labeled


def show_labeling_progress(data_dir):
    """ show labeling progress of all preprocessed datasets.
        = for each dataset, show how many imgs are labeled.
    :param data_dir: directory path for preprocessed data
    :return: children directories of data_dir
    """

    print('----------------------------------------------')
    child_dirs = glob.glob(os.path.join(data_dir, '*'))
    total = 0
    labeled = 0
    idx = 0

    for dir in child_dirs:
        idx = idx + 1
        db_file = os.path.join(dir, 'db.json')
        try:
            with open(db_file, 'r') as f:
                loaded = json.load(f)
        except Exception as e:
            print('Failed to open database file {}: {}'.format(db_file, e))
        else:
            tot, lab = labeling_progress_for_each_dir(loaded, dir, idx)
            total = total + tot
            labeled = labeled + lab

    print('')
    print('* TOTAL *')
    print(show_proportion_bar(labeled, total), '\n')
    print('----------------------------------------------')

    return child_dirs


def show_db_stats(db, cron):
    now = datetime.datetime.now()
    nowDatetime = now.strftime('%Y-%m-%d')

    df = pd.DataFrame.from_dict(db)
    columns = ['date', 'total', 'labeled', 'invalid', 'obs_car', 'obs_human',
               'shadow', 'old', '1col', '2col', 'odd2col']
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

        show_label_scatter_plot(db, cron)

        with open('trend.csv', 'r') as f:
            df_trend = pd.read_csv(f)
            df_trend[['date', 'labeled']].plot.bar(x='date', y='labeled',
                                                   rot=0)

            figure_path = os.path.join('figure', 'num_labeled.png')
            plt.savefig(figure_path)

    else:
        print(df_stats)

    pass


def main(args):
    options = loadyaml()
    data_dir = os.path.join(BASE_DIR, 'dataset')
    db = collect_all_db(data_dir).values()

    if args.visualize:
        print('\n[1] Show total DB statistics')
        print('[2] Show labeling progress\n')
        mode = input('Choose mode: ')

        if mode == '1':
            show_db_stat(db)
        elif mode == '2':
            show_labeling_progress(data_dir)
        else:
            print('Wrong input!\n')
    else:
        show_db_stats(db, args.cron)


if __name__ == '__main__':
    args = parse_args()
    main(args)

