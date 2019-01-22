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
from pymongo import MongoClient
import pymongo

# Selected components of metadata from exif
components = {'ImageWidth', 'ImageLength', 'Make', 'Model', 'GPSInfo', 'DateTimeOriginal', 'BrightnessValue'}

def parse_args():
    # python preprocess.py data --w 300 --h 240
    parser = argparse.ArgumentParser()
    parser.add_argument('data_path', help = 'Path of folder containing images', type = str)
    parser.add_argument('-W', '--width', dest = 'width', default = 300, type = int)
    parser.add_argument('-H', '--height', dest = 'height', default = 240, type = int)
    parser.add_argument('-c', '--color', dest = 'color', default = False, type = bool)
    return parser.parse_args()


def preprocess_images(data_path):
    if args.color:
        path_of_outputs = "preprocessed_data\\above\\"
    else:
        path_of_outputs = "preprocessed_data\\"

    out_width, out_height = args.width, args.height
    
    metadata = []

    for img_name in os.listdir(data_path):
        load_name = os.path.join(data_path, img_name)
        img = cv2.imread(load_name)
        # extract metadata
        meta = get_exif(load_name)
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
        #TODO: hash the image name. e.g: hased = md5(img_name)
        hashed = hashlib.md5()
        hashed.update(img_name.encode())
        meta['filehash'] = hashed.hexdigest()
        #img_name = hashed.hexdigest()
        cv2.imwrite(path_of_outputs + img_name + '.png', eq)
        #np.save(path_of_outputs + img_name + '.npy', eq)
    return metadata


def get_exif(fn):
    meta = {}
    i = Image.open(fn)
    info = i._getexif()
    for tag, value in info.items():
        decoded = TAGS.get(tag, tag)
        if decoded in components:
            meta[decoded] = value
    return meta

def annotate_additional_metadata():
    pass

def populate_metadata_db(db, metadata):
    collection.insert(metadata)
    

def connect_to_db():
    client = MongoClient('localhost', 27017)
    db = connection["Batoners"]
    collection = db["Crosswalk"]
    return db

def example():
    metadata = []
    meta = {}
    meta['filename'] = '3f7sfee'
    meta['horizontal_offset'] = 0.3
    metadata.append(meta)
    #....

def main():
    db = connect_to_db()
    args = parse_args()
    metadata = preprocess_images(args.data_path)
    #metadata.append(annotate_additional_metadata())
    populate_metadata_db(db, metadata)
    #example() 


if __name__ == '__main__':
    main()

