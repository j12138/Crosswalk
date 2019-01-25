# A pseudo-code for managing crosswalk data (and its metadata)

import cv2

class CrosswalkData:

    def __init__(self, img_file):
        self.img_file = img_file
        #self.input_filenme = ""
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

    def __display_image(self):
        pass

    def __create_track_bars(self):
        pass

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

