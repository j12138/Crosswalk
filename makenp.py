import json
import numpy as np
import os
import yaml
import cv2
from scipy.misc import imread
import datetime
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
    
def merge_list(list):
    merged = []
    for elem in list:
        merged = merged + elem
    return merged

def show_and_pick_filters(filterlist):
    picked = []
    cnt = 0
    print('\n------- filter lists -------')
    
    for fil in filterlist:
        cnt = cnt + 1
        print('['+ str(cnt) +'] ', fil)

    print('----------------------------')
    print('select filters (ex: 1 2 3 4 5)')
    picked_num = input('└─ here: ')
    picked_num_list = picked_num.split(' ')

    filter_keys = list(filterlist.keys())
    #print(filter_keys)
    
    print('\n------- selected filters -------')
    for num in picked_num_list:
        key = filter_keys[int(num) - 1]
        print('['+ num +']',key)
        picked.append(key)
    print('--------------------------------\n')

    return picked

class DBMS(object):
    def __init__(self, json_file, picked_filters):
        self.__load(json_file)
        self.filters = picked_filters #keys
        self.query_list = []
		
    def __load(self, json_file):
        with open(json_file, "r") as read_file:
            #list of metadata dictionaries
            self.db = json.load(read_file).values()
		
    def query(self):
        for item in self.db:
            #print(item['obs_car'], item['column'])
            suc = True
            try:
                for filt in self.filters:
                    suc = suc and filterlist[filt](item)
                        
                if suc:
                    #print('Success: ' + item['filehash'])
                    self.query_list.append(item)
            except :
                print('Fail: ' + item['filehash'])
                continue

        #print(query_list)    
        print('Selected data: ', len(self.query_list))
	
    def make_npy(self):
        train_hash = []
        y_train = []
        cv2.namedWindow('tool')

        for item in self.query_list:
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

        cnt = len(train_hash)
        print('Packed data: ', cnt)
        
        nowDatetime = self.__write_log(cnt)
        np.save('./npy/'+ nowDatetime +'_X.npy', train_hash)
        np.save('./npy/'+ nowDatetime +'_Y.npy', y_train)


    def __write_log(self, num):
        now = datetime.datetime.now()
        nowDatetime = now.strftime('%Y-%m-%d__%H-%M-%S')

        with open('./makenp_log.txt', "a") as f:
            f.write(nowDatetime + '\t' + str(num) + '\t' + str(self.filters) + '\n')

        return nowDatetime

def make_npy_file(options, picked_filters):
    """ the actual 'main' function. Other modules that import this module shall
    call this as the entry point. """
    db = DBMS(options['db_file'], picked_filters)
    db.query()
    db.make_npy()


def main():
    options = loadyaml()
    picked_filters = show_and_pick_filters(filterlist) #key
    make_npy_file(options, picked_filters)

if __name__ == "__main__":
    main()