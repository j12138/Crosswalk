import json
import yaml

def loadyaml():
    with open('./config.yaml', 'r') as stream: 
        options = yaml.load(stream)
    return options

def load_DB(options):
    with open(options['db_file'], "r") as db_file:
        db = json.load(db_file).values()
    return db

def show_total_stat(db):
    cnt = 0
    invalid = 0
    for item in db:
        cnt = cnt + 1

        if item['invalid'] == 1:
                invalid = invalid + 1

    print('total_#: ', cnt)
    print('invalid: ', invalid)
    print('*valid: ', cnt - invalid)

    pass

def show_manualmeta_stat(db):
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

    print('obs_car: ', obs_car)
    print('obs_human: ', obs_human)
    print('shadow: ', shadow)
    print('column: [1]', one_column, ' [2]', two_column)
    print('old: ', old)
    print('zebra_ratio: (~20)', under_20, ' (~40)', under_40, ' (~60)', under_60)
    print('             (~80)', under_80, ' (80~)', over_80)
    
    pass

def show_exifmeta_stat(db):
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

    print('Make: [Samsung] ', Samsung, '  [Apple] ', Apple)
    print('')

    pass

def main():
    options = loadyaml()
    db = load_DB(options)
    print('\n--------- total ---------\n')
    show_total_stat(db)
    print('\n--------- manual metadata ---------\n')
    show_manualmeta_stat(db)
    print('\n--------- exif metadata ---------\n')
    show_exifmeta_stat(db)
    

if __name__ == '__main__':
    main()
