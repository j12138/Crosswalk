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

preprocessed_folder = 'preprocessed_data'
labeled_folder = 'labeled'


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

    return parser.parse_args()


def load_yaml():
    with open('./labeling/config.yaml', 'r') as stream:
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
    # os.remove(os.path.join(input_dir, img_path))


def preprocess_images(input_dir: str, save_dir: str):
    """ Preprocess all the images
    :param input_dir: original image file directory
    :param save_dir: output directory to which the re-sized images are saved
    """
    files = os.listdir(input_dir)
    print("Resizing {} images".format(len(files)))

    os.mkdir(save_dir)
    output_dir = os.path.join(save_dir, 'preprocessed')
    os.mkdir(output_dir)

    Parallel(n_jobs=-1)(
        delayed(resize_and_save)(input_dir, output_dir, img)
        for img in tqdm(files))


def extract_metadata(input_dir: str, exifmeta_to_extract: list, widgets):
    """ For each image in the given directory, extract image metadata of
    interest.
    :param input_dir: A directory where image are stored
    :param exifmeta_to_extract: A list of exif metadata to extract
    :return: A dictionary (indexed by hashed key) of dictionary (metadata
             name: value)
    """
    metadata_all = {}

    for img_name in os.listdir(input_dir):
        if(img_name == ".DS_Store"):
            continue
        metadata_per_each = {}
        img = Image.open(os.path.join(input_dir, img_name))
        height, width = img.size
        assert width != height, "The image (unexpectedly) square!"
        metadata_per_each["is_horizontal"] = True if width > height else False

        for tag, value in img._getexif().items():
            # e.g. 'ImageWidth'
            exif_meta_name = TAGS.get(tag, tag)
            if exif_meta_name in exifmeta_to_extract:
                metadata_per_each[exif_meta_name] = str(value)

        # Hash the image name
        hashed = get_hash_name(img_name)
        # TODO: Please take a look, Dain. is it necessary to keep the original
        #   name ? --TJ
        # img_name = img_name + '.png'
        # meta['originalname'] = str(img_name)
        metadata_per_each['filehash'] = hashed

        init_labeling_status(metadata_per_each, widgets)

        metadata_all[hashed] = metadata_per_each

    return metadata_all


def init_labeling_status(metadata_per_each, widgets):
    metadata_per_each['is_input_finished'] = False
    metadata_per_each['current_point'] = [0, [0, 0]]
    metadata_per_each['all_points'] = [(0, 0)] * 6
    metadata_per_each['is_line_drawn'] = [False, False, False]
    for name in widgets:
        metadata_per_each[name] = widgets[name]


def update_database(metadata, save_dir):
    # create an empty README.md file
    readme_file = os.path.join(save_dir, 'README.txt')
    with open(readme_file, 'w') as f:
        f.write("#_data: " + str(len(metadata)))

    # create an empty JSON file
    db_file = os.path.join(save_dir, 'db.json')
    with open(db_file, 'w') as f:
        f.write("{}")

    try:
        with open(db_file, 'r') as f:
            loaded = json.load(f)
    except Exception as e:
        print('Failed to open database file {}: {}'.format(db_file, e))
    else:
        load = {**loaded, **metadata}
        with open(db_file, "w") as f:
            json.dump(load, f)
        print('Successfully updated!')


def preprocess_img(args, options):
    """ the actual 'main' function. Other modules that import this module shall
    call this as the entry point. """

    # e.g. exifmeta: {'ImageWidth', 'ImageLength', 'Make', 'Model', 'GPSInfo',
    #                 'DateTimeOriginal', 'BrightnessValue'}

    folder_name = os.path.basename(args.input_dir.strip('/\\'))
    save_dir = os.path.join(os.getcwd(), preprocessed_folder, folder_name)
    print('save_dir: ', save_dir)

    metadata = extract_metadata(args.input_dir, list(options['exifmeta']),
                                options['widgets'])
    preprocess_images(args.input_dir, save_dir)
    update_database(metadata, save_dir)

    os.mkdir(os.path.join(save_dir, labeled_folder))


def make_readme_file(input_dir):
    pass


def get_folder_name(input_dir):
    folder = os.path.dirname(input_dir)


def main():
    options = load_yaml()
    args = parse_args(options)
    preprocess_img(args, options)


if __name__ == '__main__':
    main()
