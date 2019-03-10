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
import yaml

def parse_args(options):
    # python preprocess.py data --w 300 --h 240

    parser = argparse.ArgumentParser()
    parser.add_argument('data_path', help = 'Path of folder containing images', type = str)
    parser.add_argument('-W', '--width', dest = 'width', default = options['preprocess_width'], type = int)
    parser.add_argument('-H', '--height', dest = 'height', default = options['preprocess_height'], type = int)
    parser.add_argument('-c', '--color', dest = 'color', default = False, type = bool)
    parser.add_argument('-d', '--db_file', dest = 'db_file', default = options['db_file'], type = str)

    return parser.parse_args()

def loadyaml():
    with open('./config.yaml', 'r') as stream: 
        options = yaml.load(stream)
    return options

def namehashing(name):
    hashed = hashlib.md5(name.encode()).hexdigest()
    hashname = str(hashed)
    return hashname

def preprocess_images(args, save_path):
    #TODO: Do not write img at preprocessed_data

    #folder = args.data_path.split('/')[-1]
    #path_of_outputs = "preprocessed_data/" + args.data_path + "/"

    if not os.path.exists(save_path):
        os.mkdir(save_path)

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
        print(save_path + img_name + '.png')
        cv2.imwrite(save_path + img_name + '.png', eq)
        #np.save(path_of_outputs + img_name + '.npy', eq)

def hash_images(save_path):
    #TODO: manage '/' component (Regex)
    #folder = args.data_path.split('/')[-1]
    #origin_path = "preprocessed_data/" + args.data_path + "/"
    #path_of_outputs = "./hashed/"

    for img_name in os.listdir(save_path):
        hashname = namehashing(img_name)
        os.rename(save_path + img_name, save_path + hashname)
        print(save_path + hashname)

def extract_metadata(args, exifmeta):
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
        hashname = namehashing(img_name)
        meta['originalname'] = str(img_name)
        meta['filehash'] = hashname
        metadata[hashname] = meta
        
    return metadata

def updateDB(metadata, db_file):
    try:
        with open(db_file, "r") as read_file:
            loaddata = json.load(read_file)
    except:
        print('Database Loading Error >>> Fail to upload')
        
    else:
        updatedata = {**loaddata, **metadata}
        with open(db_file, "w") as write_file:
            json.dump(updatedata, write_file)
        print('Successfully update database!')


def get_save_path(args):
    #return path for preprocessed(and hashed) image

    origin_path = args.data_path
    removed_root = origin_path.strip('.')
    #print(removed_root)
    replaced_slash = removed_root.replace('/', '_')
    #print(replaced_slash)
    full = './preprocessed_data/' + replaced_slash + '/'

    return full


def preprocess_img(args,options):
    """ the actual 'main' function. Other modules that import this module shall
    call this as the entry point. """
    save_path = get_save_path(args)
    print(save_path)

    # Extract metadata of JPG images
    metadata = extract_metadata(args, options['exifmeta'])

    # Preprocess images saving PNG
    preprocess_images(args, save_path)

    # Hashing the preprocessed images
    hash_images(save_path)

    # Upload metadata database in JSON form
    updateDB(metadata, args.db_file)


def main():
    options = loadyaml()
    args = parse_args(options)
    preprocess_img(args, options)


if __name__ == '__main__':
    main()
