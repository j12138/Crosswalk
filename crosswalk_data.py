# A pseudo-code for managing crosswalk data (and its metadata)

import cv2
import csv
import hashlib
import json

class CrosswalkData:

    def __init__(self, img_file):
        self.img_file = img_file
        self.hashname = self.__hash_img_name()
        self.img = cv2.imread(img_file)
        self.meta = { # value is 3rd elem
                'obs_car': [0, 1, 0],
                'obs_human': [0, 1, 0],
                'shadow': [0, 1, 0],
                'column': [1, 2, 1],
                'zebra_ratio': [0, 100, 0],
                # not zebra
                'out_of_range' : [0, 1, 0],
                'old' : [0, 1, 0]
                }
        self.labels = {
            'loc': 0.0,
            'ang': 0.0
        }

    def display_manual_meta(self):
        for name in self.meta:
            print(name, self.meta[name][2])
    
    def display_labels(self):
        for name in self.labels:
            print(name, self.labels[name])

    def make_trackbar(self, winname):
        for name in self.meta:
            cv2.createTrackbar(name, winname, self.meta[name][0], self.meta[name][1], lambda x: x)

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
        with open('Crosswalk_Database.json', 'r') as db_json:
            db = json.load(db_json)

            print(self.hashname)
        
        for name in self.meta:
            #print(db[self.hashname][name])
            db[self.hashname][name] = self.meta[name][2]
        
        for label in self.labels:
            db[self.hashname][label] = self.labels[label]

        
    
    def __hash_img_name(self):
        print(self.img_file)
        img_name = (self.img_file).split('\\')[1]
        print(img_name)
        hashed = hashlib.md5(img_name.encode()).hexdigest()
        print(hashed)
        return str(hashed)

        