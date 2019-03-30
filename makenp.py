import json
import numpy as np
import os
import yaml
import cv2
from scipy.misc import imread
# coding=utf-8

filterlist = {'Apple':lambda x:x['Make']=='Apple',
             'Samsung':lambda x:x['Make']=='Samsung',
             'shadow':lambda x:x['shadow']==1,
             'obstacle':lambda x:x['obs_car']==1 and x['obs_human']==1,
             'car':lambda x:x['obs_car']==1,
             'human':lambda x:x['obs_human']==1,
             'onecol':lambda x:x['column']==1,
             'twocol':lambda x:x['column']==2,
             'boundary':lambda x:abs(float(x['loc']))>0.8,
             'old':lambda x:x['old']==1,
             'not_out_of_range':lambda x:x['out_of_range']==0,
             'no_obs_not_old_over_60':lambda x:(x['obs_car']==0 and x['obs_human']==0 and x['old']==0 and x['zebra_ratio'] >= 60)
            }

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
        query_list = []
        for item in self.db:
            try:
                if custom_filter(item):
                    print(custom_filter(item))
                    print(item['obs_car'])
                    print('Success: ' + item['filehash'])
                    query_list.append(item)
            except :
                print('Fail: ' + item['filehash'])
                continue

        #print(query_list)    
        print('Selected data: ', len(query_list))
        return query_list
	
    def make_npy(self, entries: list):
        train_hash = []
        y_train = []
        cv2.namedWindow('tool')

        for item in entries:
            hash = item['filehash']

            try:
                img = imread('./labeling_done/' + hash, mode='RGB')
                #print(img)
                cv2.imshow('tool', img)
            except:
                #print('Fail: ' + hash)
                continue

            #print('Success: ' + hash)
            label = [float(item['loc']), float(item['ang'])]

            train_hash.append(img)
            y_train.append(label)

        print('Packed data: ', len(train_hash))
        #TODO: let name include filter info?
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
    db = DBMS(options['db_file'])
    entries = get_entries(db, filterlist, 'no_obs_not_old_over_60', 'onecol')
    db.make_npy(entries)


def main():
    options = loadyaml()
    make_npy_file(options)

if __name__ == "__main__":
    main()