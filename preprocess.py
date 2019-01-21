import numpy as np
import cv2
import os
import scipy.misc
import argparse
from PIL import Image
from matplotlib import pyplot as plt

def parse_args():
    # python preprocess.py data --w 300 --h 240
    parser = argparse.ArgumentParser()
    parser.add_argument('data_path', help = 'Path of folder containing images', type = str)
    parser.add_argument('-W', '--width', dest = 'width', default = 300, type = int)
    parser.add_argument('-H', '--height', dest = 'height', default = 240, type = int)
    parser.add_argument('-c', '--color', dest = 'color', default = False, type = bool)
    return parser.parse_args()


def preprocess_images(data_path)
    if args.color:
        path_of_outputs = "preprocessed_data\\above\\"
    else:
        path_of_outputs = "preprocessed_data\\"

    out_width, out_height = args.width, args.height

    for img_name in os.listdir(data_path):
        load_name = os.path.join(data_path, img_name)
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
        #TODO: hash the image name. e.g: hased = md5(img_name)
        cv2.imwrite(path_of_outputs + img_name + '.png', eq)
        #np.save(path_of_outputs + img_name + '.npy', eq)


def extract_metadata():
    pass

def annotate_additional_metadata():
    pass

def populate_metadata_db():
    pass

def connect_to_db():
    db = None
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
    metadata = extract_metadata()
    metadata.append(annotate_additional_metadata())
    preprocess_images(args.data_path)
    populate_metadata_db(metadata)
    example() 


if __name__ == '__main__':
    main()

