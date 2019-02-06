import json
import numpy as np
import os

filterlist = {'Apple':lambda x:x['Make']=='Apple', 'Samsung':lambda x:x['Make']=='Samsung',
                'shadow':lambda x:x['shadow'][2]==1, 'obstacle':lambda x:x['obs_car'][2]==1 and x['obs_human'][2]==1,
                'car':lambda x:x['obs_car'][2]==1, 'human':lambda x:x['obs_human'][2]==1,
                'onecol':lambda x:x['column'][2]==1, 'twocol':lambda x:x['column'][2]==2,
                'boundary':lambda x:abs(float(x['loc']))>0.8, 'old':lambda x:x['old'][2]==1,
                'not_out_of_range':lambda x:x['out_of_range'][2]==0
                'no_obs':lambda x:x['obs_car'][2]==0 and x['obs_human'][2]==0}

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
            hash = item['filehash']
            label = [item['loc'], item['ang']]
            train_hash.append(hash)
            y_train.append(label)

        np.save('./X.npy', train_hash)
        np.save('./Y.npy', y_train)

def get_entries(db, fil1, fil2):
    entries = db.query(filterlist[fil1]and filterlist[fil2])
    return entries

def merge_list(list):
    merged = []
    for elem in list:
        merged = merged + elem
    return merged


def main():
    db = DBMS("Crosswalk_Database.json")
    entries = get_entries(db, 'Apple', 'test')
    db.make_npy(entries)


if __name__ == "__main__":
    main()