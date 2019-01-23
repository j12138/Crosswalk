# A pseudo-code for managing crosswalk data (and its metadata)

import cv2

def launch_annotator(self):
    cv2.namedWindow('tool')
    cv2.setMouseCallback('tool', draw_point)
    pass

class CrosswalkData:

    def __init__(self, img_name):
        self.img_name = img_name
        self.input_filenme = ""
        self.meta = {}
        self.labels = {}

    def __display_image(self):
        pass

    def __create_track_bars(self):
        pass

    def annotate(self):
        self.__display_image()
        self.__create_track_bars()


launch_annotator()
for img in images:
    data = CrosswalkData(img)
    data.annotate()

