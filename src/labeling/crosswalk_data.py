# A pseudo-code for managing crosswalk data (and its metadata)

import cv2
import json
import yaml
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
config_file = os.path.join(BASE_DIR, 'config.yaml')


def loadyaml():
    options = {'db_file': './Crosswalk_Database.json',
               'npy_log_file': './makenp_log.txt',
               'data_dir': './preprocessed_data/',
               'preprocess_width': 150, 'preprocess_height': 120,
               'exifmeta': {'ImageWidth': None, 'ImageLength': None,
               'Make': None, 'Model': None, 'GPSInfo': None,
               'DateTimeOriginal': None, 'BrightnessValue': None},
               'manualmeta': {'obs_car': [0, 1, 0], 'obs_human': [0, 1, 0],
               'shadow': [0, 1, 0], 'column': [1, 2, 1],
               'zebra_ratio': [0, 100, 60], 'out_of_range': [0, 1, 0],
               'old': [0, 1, 0], 'invalid': [0, 0, 0], 'corner-case': [0, 0, 0 ]},
               'widgets': {'cb_obscar': False, 'cb_obshuman': False,
               'cb_shadow': False, 'cb_old': False, 'cb_outrange': False,
               'rb_1col': True, 'slider_ratio': 60, 'cb_corner': False}}

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
            'rb_1col': 1,
            # 'slider_ratio': 60
            'cb_corner': False
        }
        self.remarks = ''


class CrosswalkData:

    def __init__(self, img_file):
        self.options = loadyaml()
        self.img_file = img_file
        self.hashname = self.__parse_img_name()
        self.img = cv2.imread(img_file)
        self.meta = self.options['manualmeta']
        self.labels = {
            'loc': 0.0,
            'ang': 0.0,
            'pit': 0.0,
            'roll': 0.0
        }
        self.remarks = ''
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

    def input_labels(self, loc, ang, pit, roll):
        self.labels['loc'] = loc
        self.labels['ang'] = ang
        self.labels['pit'] = pit
        self.labels['roll'] = roll

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
            try:
                status.widgets_status[name] = this_data[name]
            except Exception as e:
                this_data[name] = self.options['widgets'][name]
                status.widgets_status[name] = this_data[name]

        if 'remarks' in this_data.keys():
            status.remarks = this_data['remarks']
        else:
            print('비고 없음')

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
        this_data['remarks'] = status.remarks
        for name in status.widgets_status:
            this_data[name] = status.widgets_status[name]

        db[self.hashname] = this_data
        with open(self.db, "w") as db_json:
            json.dump(db, db_json)
