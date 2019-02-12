import json
import numpy as np
import os
import yaml
import cv2

def loadyaml():
    with open('./config.yaml', 'r') as stream: 
        options = yaml.load(stream)
    return options

class DBMS(object):
    def __init__(self, json_file):
        self.__load(json_file)
		
    def __load(self, json_file):
        with open(json_file, "r") as read_file:
            #list of metadata dictionaries
            self.db = json.load(read_file).values()
		
    def query(self, custom_filter):
        return [item for item in self.db if custom_filter(item)]
	
    def make_npy(self, entries: list):
        train_hash = []
        y_train = []

        for item in entries:
            hash = item['filehash'] #wrong method

            try:
                img = cv2.imread('./preprocessed_data/' + hash)
                cv2.namedWindow('tool')
                cv2.imshow('tool', img)
            except :
                print('Fail: ' + hash)
                continue

            print('Success: ' + hash)
            label = [item['loc'], item['ang']]

            train_hash.append(img)
            y_train.append(label)

        #TODO: let name include filter info
        np.save('./X.npy', train_hash)
        np.save('./Y.npy', y_train)

def get_entries(db, filterlist, fil1, fil2):
    entries = db.query(filterlist[fil1]and filterlist[fil2])
    return entries

def merge_list(list):
    merged = []
    for elem in list:
        merged = merged + elem
    return merged

def make_npy_file(options):
    """ the actual 'main' function. Other modules that import this module shall
    call this as the entry point. """
    db = DBMS(options['dp_file'])
    entries = get_entries(db, options['filterlist'], 'no_obs_not_old', 'not_out_of_range')
    db.make_npy(entries)


def main():
    options = loadyaml()
    make_npy_file(options)

if __name__ == "__main__":
    main()