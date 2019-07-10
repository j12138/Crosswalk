# A pseudo-code for managing crosswalk data (and its metadata)

import cv2
import csv
import hashlib
import json
import yaml
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(BASE_DIR, 'config.yaml')


def loadyaml():
    with open(config_file, 'r') as stream: 
        options = yaml.load(stream)
    return options


class LabelingStatus(object):
    """
    An entity class that contains labeling state information for each input
    image.
    """

    def __init__(self):
        self.is_input_finished = False
        self.current_point = [0, (0, 0)]
        self.all_points = [(0, 0)] * 6
        self.is_line_drawn = [False, False, False]
        self.widgets_status = {
            'cb_obscar': False,
            'cb_obshuman': False,
            'cb_shadow': False,
            'cb_old': False,
            # 'cb_outrange': False,
            'rb_1col': 1
            # 'slider_ratio': 60
        }


class CrosswalkData:

    def __init__(self, img_file):
        options = loadyaml()
        self.img_file = img_file
        self.hashname = self.__parse_img_name()
        self.img = cv2.imread(img_file)
        self.meta = options['manualmeta']
        self.labels = {
            'loc': 0.0,
            'ang': 0.0,
            'pit': 0.0,
            'roll': 0.0
        }
        self.db = self.__get_db_file()

    def __get_db_file(self):
        data_path = os.path.abspath(self.img_file + "/../../")
        db_path = os.path.join(data_path, 'db.json')
        return db_path

    def display_manual_meta(self):
        for name in self.meta:
            print(name, self.meta[name][2])

    def display_labels(self):
        for name in self.labels:
            print(name, self.labels[name])

    def make_trackbar(self, winname):
        for name in self.meta:
            cv2.createTrackbar(name, winname, self.meta[name][0],
                               self.meta[name][1], lambda x: x)
        cv2.setTrackbarPos('zebra_ratio', winname, 60)

    def input_manual_meta(self, winname):
        for name in self.meta:
            self.meta[name][2] = cv2.getTrackbarPos(name, winname)

    def input_labels(self, loc, ang, pit, roll):
        self.labels['loc'] = loc
        self.labels['ang'] = ang
        self.labels['pit'] = pit
        self.labels['roll'] = roll

    def write_on_csv(self):
        with open('annotation.csv', 'a', newline='') as csvfile:
            mywriter = csv.writer(csvfile)
            mywriter.writerow([self.img_file, self.labels['loc'], self.labels['ang']])

    def write_on_db(self):
        with open(self.db, 'r+') as db_json:
            db = json.load(db_json)

        try:
            for name in self.meta:
                db[self.hashname][name] = self.meta[name][2]

            for label in self.labels:
                db[self.hashname][label] = self.labels[label]
        except Exception as e:
            print('{}: {}'.format(e, self.hashname))
            return

        with open(self.db, "w") as db_json:
            json.dump(db, db_json)

    def set_invalid(self):
        for name in self.meta:
            self.meta[name][2] = -1

        self.meta['invalid'][2] = 1

    def __parse_img_name(self):
        # print(self.img_file)
        img_name = os.path.split(self.img_file)[-1]
        # print(img_name)
        return img_name

    def load_labeling_status(self):
        status = LabelingStatus()

        with open(self.db, 'r+') as db_json:
            this_data = json.load(db_json)[self.hashname]

        status.is_input_finished = this_data['is_input_finished']
        status.current_point = [this_data['current_point'][0],
                                tuple(this_data['current_point'][1])]
        for i in range(6):
            status.all_points[i] = tuple(this_data['all_points'][i])

        status.is_line_drawn = this_data['is_line_drawn']
        for name in status.widgets_status:
            status.widgets_status[name] = this_data[name]

        return status

    def save_labeling_status(self, status):
        # print(status.widgets_status['rb_1col'])
        with open(self.db, 'r+') as db_json:
            db = json.load(db_json)

        this_data = db[self.hashname]
        this_data['is_input_finished'] = status.is_input_finished
        this_data['current_point'] = status.current_point
        this_data['all_points'] = status.all_points
        this_data['is_line_drawn'] = status.is_line_drawn
        for name in status.widgets_status:
            this_data[name] = status.widgets_status[name]

        db[self.hashname] = this_data
        with open(self.db, "w") as db_json:
            json.dump(db, db_json)
