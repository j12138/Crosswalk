import numpy as np
import cv2
import os
import scipy.misc
import argparse
from PIL import Image
from PIL.ExifTags import TAGS
from matplotlib import pyplot as plt
import hashlib
import json

# Selected components of metadata from exif
exifmeta = {'ImageWidth', 'ImageLength', 'Make', 'Model', 'GPSInfo', 'DateTimeOriginal', 'BrightnessValue'}

def parse_args():
    # python preprocess.py data --w 300 --h 240
    parser = argparse.ArgumentParser()
    parser.add_argument('data_path', help = 'Path of folder containing images', type = str)
    parser.add_argument('-W', '--width', dest = 'width', default = 300, type = int)
    parser.add_argument('-H', '--height', dest = 'height', default = 240, type = int)
    parser.add_argument('-c', '--color', dest = 'color', default = False, type = bool)
    return parser.parse_args()


def preprocess_images(args):
    if args.color:
        path_of_outputs = "preprocessed_data/above/"
    else:
        path_of_outputs = "preprocessed_data/"

    out_width, out_height = args.width, args.height

    for img_name in os.listdir(args.data_path):
        load_name = os.path.join(args.data_path, img_name)
        img = cv2.imread(load_name)
        
        # resizing
        img = scipy.misc.imresize(img, (int(out_width*1.3333), out_width))
        H, W = img.shape[:2]
        # cut
        img = img[int(H-out_height):, :]
        # adjust
        if args.color:
            eq = img
        else:
            gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            eq = cv2.equalizeHist(gray_img)
        # save
        cv2.imwrite(path_of_outputs + img_name + '.png', eq)
        #np.save(path_of_outputs + img_name + '.npy', eq)


def extract_metadata(args):
    metadata = {}

    for img_name in os.listdir(args.data_path):
        load_name = os.path.join(args.data_path, img_name)

        meta = {}
        i = Image.open(load_name)
        info = i._getexif()

        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded in exifmeta:
                meta[decoded] = str(value)
        
        # Hash the image name
        img_name += '.png'
        hashed = hashlib.md5()
        hashname = str(hashed.update(img_name.encode()))
        meta['originalfname'] = str(img_name)
        meta['filehash'] = hashname
        metadata[hashname] = meta

    return metadata

def example():
    metadata = []
    meta = {}
    meta['filename'] = '3f7sfee'
    meta['horizontal_offset'] = 0.3
    metadata.append(meta)
    #....

def main():
    args = parse_args()

    # Extract metadata of JPG images
    metadata = extract_metadata(args)

    # Upload metadata database in JSON form
    with open("Crosswalk_Database.json", "w") as write_file:
        json.dump(metadata, write_file)

    # Preprocess images saving PNG
    preprocess_images(args)


if __name__ == '__main__':
    main()

