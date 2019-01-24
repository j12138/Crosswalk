import numpy as np
import cv2
import os
import scipy.misc
import argparse
from PIL import Image
from PIL.ExifTags import TAGS
from matplotlib import pyplot as plt
import hashlib
from pymongo import MongoClient
import pymongo

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
    metadata = []

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
        hashed = hashlib.md5()
        hashed.update(img_name.encode())
        meta['originalfname'] = str(img_name)
        meta['filehash'] = str(hashed.hexdigest())
        #img_name = hashed.hexdigest()
        metadata.append(meta)

    return metadata

def annotate_additional_metadata():
    pass

def populate_metadata_db(db, metadata):
    pass
    

def connect_to_db():
    client = MongoClient('localhost', 27017)
    db = client["Batoners"]
    collection = db.Crosswalk
    return collection

def example():
    metadata = []
    meta = {}
    meta['filename'] = '3f7sfee'
    meta['horizontal_offset'] = 0.3
    metadata.append(meta)
    #....

def main():
    # Connect ot DB
    #db = connect_to_db()
    client = MongoClient()
    db = client["Batoners"]
    collection = db.Crosswalk

    args = parse_args()

    # Extract metadata of JPG images
    metadata = extract_metadata(args)

    # Preprocess images saving PNG
    preprocess_images(args)

    # Populating metadata to DB
    collection.insert(metadata)
    print(db.collection_names)
    print(collection.find_one({'Make':'Apple'}))

    #metadata.append(annotate_additional_metadata())
    #populate_metadata_db(db, metadata)
    

if __name__ == '__main__':
    main()

