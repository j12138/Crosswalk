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

def hashing(name):
    hashed = hashlib.md5(name.encode()).hexdigest()
    hashname = str(hashed)
    return hashname

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
        img_name = img_name + '.png'
        hashname = hashing(img_name)
        cv2.imwrite(path_of_outputs + img_name, eq)
        os.rename(path_of_outputs + img_name, path_of_outputs + hashname)
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
        img_name = img_name + '.png'
        hashname = hashing(img_name)
        meta['originalname'] = str(img_name)
        metadata[hashname] = meta
        
    return metadata

def updateJSON(metadata):
    try:
        with open("Crosswalk_Database.json", "r") as read_file:
            loaddata = json.load(read_file)
    except:
        print('Database Loading Error')
        
    else:
        updatedata = {**loaddata, **metadata}
        with open("Crosswalk_Database.json", "w") as write_file:
            json.dump(updatedata, write_file)
        print('Successfully upload database!')

def main():
    args = parse_args()

    # Extract metadata of JPG images
    metadata = extract_metadata(args)

    # Preprocess images saving PNG
    preprocess_images(args)

    # Upload metadata database in JSON form
    updateJSON(metadata)


if __name__ == '__main__':
    main()

