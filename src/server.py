import pysftp
import os
import yaml


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.join(BASE_DIR, "..")

cnopts = pysftp.CnOpts()
cnopts.hostkeys = None
config_file = 'server_config.yaml'


def load_yaml():
    with open(config_file, 'r') as stream:
        options = yaml.load(stream)
    return options


def upload_all_npy(sftp, npy_dir, server_log, local_log):
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


def main():
    options = load_yaml()
    npy_dir = os.path.join(ROOT_DIR, options['npy_dir'])
    server_npy_log = options['server_npy_log']
    local_npy_log = os.path.join(ROOT_DIR, options['local_npy_log'])

    with pysftp.Connection(host=options['host'],
                           username=options['username'],
                           password=options['password'],
                           cnopts=cnopts) as sftp:

        sftp.chdir('..')
        sftp.chdir('..')
        sftp.chdir('crosswalk')

        print('\nChoose mode:')
        print('[1] Upload all npy files')
        print('[2] Download all npy files')
        mode = int(input('>> '))

        if mode == 1:  # Upload npy
            upload_all_npy(sftp, npy_dir, server_npy_log, local_npy_log)
        elif mode == 2:
            download_all_npy(sftp, npy_dir, server_npy_log, local_npy_log)
        else:
            print('invalid mode!\n')


if __name__ == "__main__":
    main()
