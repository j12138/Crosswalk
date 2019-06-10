import json
import yaml
from math import ceil
import matplotlib.pyplot as plt
import glob
import os


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


def loadyaml():
    with open('./config.yaml', 'r') as stream:
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

    bar = '█' * blocks + '░' * (25 - blocks) + ' [ ' + str(target) + ' / ' + str(total) + ' ]'

    return bar


def show_label_scatter_plot(db):
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
                pit.append(item['pit'])
                roll.append(item['roll'])
        except:
            continue

    plt.figure(figsize=(10,4))
    # loc, ang
    plt.subplot(121)
    plt.scatter(loc, ang)
    plt.xlim((-2.0, 2.0))
    plt.ylim((-90, 90))
    plt.xlabel('loc')
    plt.ylabel('ang')
    plt.title('location ─ angle')

    # pit, roll
    plt.subplot(122)
    plt.scatter(pit, roll)
    plt.xlim((0.0, 1.0))
    plt.ylim((-90, 90))
    plt.xlabel('pit')
    plt.ylabel('roll')
    plt.title('pitch ─ roll')

    plt.show()

    pass


def show_total_stat(db):
    cnt = 0
    labeled = 0
    invalid = 0
    for item in db:
        if item['is_input_finished']:
            labeled = labeled + 1
            if item['invalid'] == 1:
                invalid = invalid + 1
        cnt = cnt + 1

    print('total_#: ', cnt)
    print('labeled: ', labeled)
    print('invalid: ', invalid)
    print('*valid(labeled): ' + show_proportion_bar(labeled-invalid, labeled))

    return cnt, labeled


def show_manualmeta_stat(db, total):
    obs_car = 0
    obs_human = 0
    shadow = 0
    one_column = 0
    two_column = 0
    under_20 = 0
    under_40 = 0
    under_60 = 0
    under_80 = 0
    over_80 = 0
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
            if item['old'] == 1:
                old = old + 1

        except:
            print('Fail: ' + item['filehash'])
            continue

    print('obs_car:  ', show_proportion_bar(obs_car, total))
    print('obs_human:', show_proportion_bar(obs_human, total))
    print('shadow:   ', show_proportion_bar(shadow, total))
    print('old:      ', show_proportion_bar(old, total), '\n')

    print('column:')
    print('  └─ [1]  ', show_proportion_bar(one_column, total))
    print('  └─ [2]  ', show_proportion_bar(two_column, total), '\n')

    print('zebra_ratio:')
    print(' └─ [~20] ', show_proportion_bar(under_20, total))
    print(' └─ [~40] ', show_proportion_bar(under_40, total))
    print(' └─ [~60] ', show_proportion_bar(under_60, total))
    print(' └─ [~80] ', show_proportion_bar(under_80, total))
    print(' └─ [80~] ', show_proportion_bar(over_80, total))

    pass


def show_exifmeta_stat(db, total):
    horizontal = 0
    Samsung = 0
    Apple = 0

    for item in db:
        try:
            if item['is_horizontal']:
                horizontal = horizontal + 1
            if item['Make'] == 'samsung':
                Samsung = Samsung + 1
            if item['Make'] == 'Apple':
                Apple = Apple + 1

        except:
            print('Fail: ' + item['filehash'])
            continue

    print('horizontal:', show_proportion_bar(horizontal, total))
    print('\nMake')
    print('└─Samsung:', show_proportion_bar(Samsung, total))
    print('└─Apple:  ', show_proportion_bar(Apple, total))

    pass


def show_db_stat(options):
    db = load_DB(options)
    db2 = collect_all_db(options['data_dir'])
    db = db2.values()

    print('\n--------- total ---------\n')
    total, labeled = show_total_stat(db)

    print('\n--------- exif metadata ---------\n')
    show_exifmeta_stat(db, total)

    if total == 0:
        print('There are no data!')
        return

    print('\n--------- manual metadata (labeled) ---------\n')
    show_manualmeta_stat(db, labeled)

    show_label_scatter_plot(db)

    print('')


def labeling_progress_for_each_dir(db, dir):
    total = 0
    labeled = 0
    for name in db.values():
        total = total + 1
        if name['is_input_finished']:
            labeled = labeled + 1

    dir_name = os.path.basename(dir)
    print(dir_name, ':', show_proportion_bar(labeled, total))

    return total, labeled


def show_labeling_progress(options):
    print('----------------------------------------------')
    child_dirs = glob.glob(os.path.join(options['data_dir'], '*'))
    total = 0
    labeled = 0

    for dir in child_dirs:
        db_file = os.path.join(dir, 'db.json')
        try:
            with open(db_file, 'r') as f:
                loaded = json.load(f)
        except Exception as e:
            print('Failed to open database file {}: {}'.format(db_file, e))
        else:
            tot, lab = labeling_progress_for_each_dir(loaded, dir)
            total = total + tot
            labeled = labeled + lab

    print('')
    print('* TOTAL *')
    print(show_proportion_bar(labeled, total))
    print('----------------------------------------------')

    return


def main():
    options = loadyaml()

    print('\n[1] Show total DB statistics')
    print('[2] Show labeling progress\n')
    mode = input('Choose mode: ')

    if mode == '1':
        show_db_stat(options)
    elif mode == '2':
        show_labeling_progress(options)
    else:
        print('Wrong input!\n')

    
if __name__ == '__main__':
    main()
