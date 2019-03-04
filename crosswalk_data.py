# A pseudo-code for managing crosswalk data (and its metadata)

import cv2
import csv
import hashlib
import json
import yaml

def loadyaml():
    with open('./config.yaml', 'r') as stream: 
        options = yaml.load(stream)
    return options

class CrosswalkData:

    def __init__(self, img_file):
        options = loadyaml()
        self.img_file = img_file
        self.hashname = self.__parse_img_name()
        self.img = cv2.imread(img_file)
        self.meta = options['manualmeta']
        self.labels = {
            'loc': 0.0,
            'ang': 0.0
        }
        self.db = options['db_file']

    def display_manual_meta(self):
        for name in self.meta:
            print(name, self.meta[name][2])
    
    def display_labels(self):
        for name in self.labels:
            print(name, self.labels[name])

    def make_trackbar(self, winname):
        for name in self.meta:
            cv2.createTrackbar(name, winname, self.meta[name][0], self.meta[name][1], lambda x: x)
        cv2.setTrackbarPos('zebra_ratio', winname, 60)

    def input_manual_meta(self, winname):
        for name in self.meta:
            self.meta[name][2] = cv2.getTrackbarPos(name, winname)

    def input_labels(self, loc, ang):
        self.labels['loc'] = loc
        self.labels['ang'] = ang

    def write_on_csv(self):
        with open('annotation.csv', 'a', newline='') as csvfile:
            mywriter = csv.writer(csvfile)
            mywriter.writerow([self.img_file, self.labels['loc'], self.labels['ang']])

    def write_on_db(self):
        with open(self.db, 'r+') as db_json:
            db = json.load(db_json)
        
        for name in self.meta:
            db[self.hashname][name] = self.meta[name][2]
        
        for label in self.labels:
            db[self.hashname][label] = self.labels[label]

        with open(self.db, "w") as db_json:
            json.dump(db, db_json)

    def set_invalid(self):
        for name in self.meta:
            self.meta[name][2] = -1

        self.meta['invalid'][2] = 1

    def __parse_img_name(self):
        print(self.img_file)
        img_name = (self.img_file).split('\\')[-1]
        print(img_name)
        return img_name
