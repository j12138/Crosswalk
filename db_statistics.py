import json
import yaml
from math import ceil
import matplotlib.pyplot as plt

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
    proportion = 100 * float(target) / total
    blocks = ceil(proportion * 0.25)
    
    bar = '█' * blocks + '░' * (25 - blocks) + ' [ ' + str(target) + ' / ' + str(total) + ' ]'
    
    return bar

def show_label_scatter_plot(db):
    loc = []
    ang = []
    cnt = 0

    for item in db:
        if item['invalid'] == 0:
            loc.append(item['loc'])
            ang.append(item['ang'])
    
    plt.scatter(loc, ang)
    plt.xlim((-2.0, 2.0))
    plt.ylim((-90, 90))
    plt.xlabel('loc')
    plt.ylabel('ang')
    plt.title('Scatterplot of labels')
    plt.show()

    pass


def show_total_stat(db):
    cnt = 0
    invalid = 0
    for item in db:
        cnt = cnt + 1

        if item['invalid'] == 1:
                invalid = invalid + 1

    print('total_#: ', cnt)
    print('invalid: ', invalid)
    print('*valid: ' + show_proportion_bar(cnt-invalid, cnt))

    return cnt

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

        except :
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
    Samsung = 0
    Apple = 0

    for item in db:
        try:
            if item['Make'] == 'samsung':
                Samsung = Samsung + 1
            if item['Make'] == 'Apple':
                Apple = Apple + 1

        except :
            print('Fail: ' + item['filehash'])
            continue

    print('Make')
    print('└─Samsung:', show_proportion_bar(Samsung, total))
    print('└─Apple:  ', show_proportion_bar(Apple, total))
    print('\n')

    pass

def main():
    options = loadyaml()
    db = load_DB(options)
    print('\n--------- total ---------\n')
    total = show_total_stat(db)
    print('\n--------- manual metadata ---------\n')
    show_manualmeta_stat(db, total)
    print('\n--------- exif metadata ---------\n')
    show_exifmeta_stat(db, total)
    show_label_scatter_plot(db)
    

if __name__ == '__main__':
    main()
