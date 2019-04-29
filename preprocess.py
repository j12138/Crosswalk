import cv2
import os
import argparse
from PIL import Image
from PIL.ExifTags import TAGS
import hashlib
import json
import yaml
from tqdm import tqdm
from joblib import Parallel, delayed


def parse_args(options):
    """ Parse command-line arguments
    ex: $ python preprocess.py data --w 300 --h 240
    :param options: default values for the arguments; comes from the
        configuration file
    :return: parsed arguments
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('input_dir', help='Path of folder containing images',
                        type=str)
    parser.add_argument('db_file', default=options['db_file'], type=str,
                        nargs='?', help="JSON database file")

    return parser.parse_args()


def load_yaml():
    with open('./config.yaml', 'r') as stream:
        options = yaml.load(stream)
    return options


def get_hash_name(name):
    """ Hash the given filename to create a unique key
    :param name: file name
    :return: hashed value
    """
    return str(hashlib.md5(name.encode()).hexdigest())


def resize_and_save(input_dir, output_dir, img_path):
    """ A worker function for `preprocess_images`, which implements a
    Joblib-based parallelism. Re-sizes and saves each image.
    :param input_dir: original image directory
    :param output_dir: output base directory
    :param img_path: Path to an image to process
    :return: None
    """
    img = cv2.imread(os.path.join(input_dir, img_path))
    # compress the image size by .15 for saving the storage by 1/4
    resized = cv2.resize(img, None, fx=0.15, fy=0.15,
                         interpolation=cv2.INTER_AREA)
    # cv2.imwrite determines the format by the extension in the path
    save_path = os.path.join(output_dir, get_hash_name(img_path) + ".png")
    cv2.imwrite(save_path, resized)
    # remove the extension
    os.rename(save_path, save_path[:-4])


def preprocess_images(input_dir, output_dir):
    """ Preprocess all the images
    :param input_dir: original image file directory
    :param output_dir: output directory to which the re-sized images are saved
    """
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    files = os.listdir(input_dir)
    print("Resizing {} images".format(len(files)))
    Parallel(n_jobs=-1)(
        delayed(resize_and_save)(input_dir, output_dir, img)
        for img in tqdm(files))


def extract_metadata(input_dir, exifmeta):
    metadata = {}

    for img_name in os.listdir(input_dir):
        load_name = os.path.join(input_dir, img_name)

        meta = {}
        i = Image.open(load_name)
        info = i._getexif()

        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded in exifmeta:
                meta[decoded] = str(value)

        # Hash the image name
        hashed = get_hash_name(img_name)
        # TODO: Please take a look, Dain. is it necessary to keep the original
        #   name ? --TJ
        # img_name = img_name + '.png'
        # meta['originalname'] = str(img_name)
        meta['filehash'] = hashed
        metadata[hashed] = meta

    return metadata


def update_database(metadata, db_file):
    if not os.path.exists(db_file):
        # create an empty JSON file
        with open(db_file, 'w') as f:
            f.write("{}")
    try:
        # check if the db_file is a legitimate json file
        with open(db_file, "r") as f:
            loaded = json.load(f)
    except Exception as e:
        print('Failed to open database file {}: {}'.format(db_file, e))
    else:
        load = {**loaded, **metadata}
        with open(db_file, "w") as f:
            json.dump(load, f)
        print('Successfully updated!')


def get_output_dir(input_dir, data_dir):
    """ return path for preprocessed(and hashed) image
    :param input_dir: the name of the original image directory
    :return: expanded output directory path
    """
    if not (os.path.exists(data_dir) and os.path.isdir(data_dir)):
        os.mkdir(data_dir)
    dir_name = input_dir.strip('.').replace('/', '_').replace('\\', '_')
    return os.path.join(data_dir, dir_name)


def preprocess_img(args, options):
    """ the actual 'main' function. Other modules that import this module shall
    call this as the entry point. """

    output_dir = get_output_dir(args.input_dir, options["data_dir"])
    metadata = extract_metadata(args.input_dir, options['exifmeta'])
    preprocess_images(args.input_dir, output_dir)
    update_database(metadata, args.db_file)


def main():
    options = load_yaml()
    args = parse_args(options)
    preprocess_img(args, options)


if __name__ == '__main__':
    main()
