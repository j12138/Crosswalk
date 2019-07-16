import pysftp
import os
import yaml
import glob


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(BASE_DIR, "..")

cnopts = pysftp.CnOpts()
cnopts.hostkeys = None
config_file = 'server_config.yaml'
private_key = os.path.join(ROOT_DIR, '..', '.ssh', 'id_rsa')


def load_yaml():
    with open(os.path.join(BASE_DIR, config_file), 'r') as stream:
        options = yaml.load(stream)
    return options


def upload_all_npy(sftp, npy_dir, server_log, local_log):
    """ upload all local npy files at server.
    :param sftp: server connection object
    :param npy_dir: local npy directory path
    :param server_log: current npy log file on server (npy_log.txt)
    :param local_log: local npy log file (makenp.txt)
    :return: None
    """
    sftp.chdir('npy')
    cnt = 0

    with open(local_log, "r") as f:
        lines = f.readlines()

        for line in lines:
            if line[:2] == '//':
                continue

            line_item = (line.rstrip()).split('\t')
            npy_file = line_item[0]
            # print(npy_file)

            if sftp.exists(npy_file + '_X.npy'):
                continue
            else:
                print(os.path.join(npy_dir, npy_file))
                sftp.put(os.path.join(npy_dir, npy_file) + '_X.npy')
                sftp.put(os.path.join(npy_dir, npy_file) + '_Y.npy')
                cnt = cnt + 1

                sftp.chdir('..')
                with sftp.open(server_log, 'a') as sf:
                    sf.write(line)
                sftp.chdir('npy')

    print('uploaded {} items\n'.format(cnt))


def download_all_npy(sftp, npy_dir, server_log, local_log):
    """ download all remote(on server) npy files to local
    :param sftp: server connection object
    :param npy_dir: local npy directory path
    :param server_log: current npy log file on server (npy_log.txt)
    :param local_log: local npy log file (makenp.txt)
    :return: None
    """
    cnt = 0
    with sftp.open(server_log, "r") as f:
        lines = f.readlines()
        sftp.chdir('npy')

        for line in lines:
            if line[:2] == '//':
                continue

            line_item = (line.rstrip()).split('\t')
            npy_file = line_item[0]
            # print(npy_file)

            if os.path.exists(os.path.join(npy_dir, npy_file) + '_X.npy'):
                continue
            else:
                print(npy_file)
                sftp.get(npy_file + '_X.npy', os.path.join(npy_dir, npy_file) + '_X.npy')
                sftp.get(npy_file + '_Y.npy', os.path.join(npy_dir, npy_file) + '_Y.npy')
                cnt = cnt + 1

                with open(local_log, 'a') as lf:
                    lf.write(line)

    print('downloaded {} items\n'.format(cnt))


def upload_datasets(sftp, data_dir):
    """ upload all local datasets at server.
    :param sftp: server connection object
    :param data_dir: local data directory (./preprocessed_data)
    :return: None
    """
    local_datasets = glob.glob(os.path.join(data_dir, '*'))
    sftp.chdir('dataset')

    print(os.path.normpath(data_dir))

    for dir in local_datasets:
        print(dir)
        dir_name = os.path.basename(dir)

        if sftp.exists(dir_name):
            sftp.chdir(dir_name)
            print('already exists')
        else:
            print('create new!')
            sftp.mkdir(dir_name)
            sftp.chdir(dir_name)
            sftp.mkdir('labeled')
            sftp.mkdir('preprocessed')

        sftp.put(os.path.join(dir, 'db.json'))
        sftp.put(os.path.join(dir, 'README.txt'))

        sftp.chdir('preprocessed')
        for img in glob.glob(os.path.join(dir, 'preprocessed', '*')):
            sftp.put(img)

        for img in glob.glob(os.path.join(dir, 'labeled', '*')):
            if sftp.exists(os.path.basename(img)):
                sftp.remove(os.path.basename(img))
            sftp.chdir('../labeled')
            sftp.put(img)
            sftp.chdir('../preprocessed')

        sftp.chdir('./../..')


def download_datasets(sftp, data_dir):
    """ download all datasets from server to local dir
    :param sftp: server connection object
    :param data_dir: local data directory (./preprocessed_data)
    :return: None
    """
    sftp.chdir('dataset')
    server_datasets = sftp.listdir()

    for dir in server_datasets:
        print(dir)
        local_dir = os.path.join(data_dir, dir)
        print(local_dir)
        sftp.chdir(dir)

        sftp.get('db.json', os.path.join(local_dir, 'db.json'))
        sftp.get('README.txt', os.path.join(local_dir, 'README.txt'))

        # download labeled data
        sftp.chdir('labeled')
        labeled_data = sftp.listdir()

        for img in labeled_data:
            sftp.get(img, os.path.join(local_dir, 'labeled', img))
            if os.path.exists(os.path.join(local_dir, 'preprocessed', img)):
                os.remove(os.path.join(local_dir, 'preprocessed', img))

        # download preprocessed data
        sftp.chdir('../preprocessed')
        preprocessed_data = sftp.listdir()

        for img in preprocessed_data:
            sftp.get(img, os.path.join(local_dir, 'preprocessed', img))

        sftp.chdir('./../..')


def main(is_imported, username, password, datadir):
    options = load_yaml()
    npy_dir = os.path.join(ROOT_DIR, options['npy_dir'])
    if is_imported:
        data_dir = datadir
    else:
        data_dir = os.path.join(ROOT_DIR, options['data_dir'])
    server_npy_log = options['server_npy_log']
    local_npy_log = os.path.join(ROOT_DIR, options['local_npy_log'])

    if is_imported:
        sftp = pysftp.Connection(host=options['host'],
                                 username=username,
                                 password=password,
                                 cnopts=cnopts)

    else:
        sftp = pysftp.Connection(host=options['host'],
                                 username='alal',
                                 private_key=private_key,
                                 private_key_pass='p@$phr4se',
                                 cnopts=cnopts)

    with sftp:
        sftp.chdir('..')
        sftp.chdir('..')
        sftp.chdir('crosswalk')

        print('\nChoose mode:')
        print('[1] Upload all npy files')
        print('[2] Download all npy files')
        print('[3] Upload all preprocessed datasets')
        print('[4] Download all preprocessed datasets')

        if is_imported:
            mode = 3
        else:
            mode = int(input('>> '))

        if mode == 1:  # Upload npy
            upload_all_npy(sftp, npy_dir, server_npy_log, local_npy_log)
        elif mode == 2:
            download_all_npy(sftp, npy_dir, server_npy_log, local_npy_log)
        elif mode == 3:
            upload_datasets(sftp, data_dir)
        elif mode == 4:
            download_datasets(sftp, data_dir)
        else:
            print('invalid mode!\n')


if __name__ == "__main__":
    main(False, None, None, None)