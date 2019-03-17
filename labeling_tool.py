# crosswalk labeling tool
# use preprocessed_data images
# input both side of crosswalk --> location / direction(angle)

import argparse
import glob
import cv2
import math
import csv
import crosswalk_data as cd
import compute_label_lib as cl

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('data_path', help = 'Path of folder containing images', default = '', type = str)
    return parser.parse_args()

#===================#
#       CLASS       # 
#===================#

class Annotator(object):
    """ An Annotator displays input window for each image and lets user draw
    points (label) for each image data. """

    def __init__(self, img_dir):
        self.img_dir = img_dir
        self.is_input_finished = False
        self.current_point = [0, (0,0)]
        self.all_points = [(0, 0)]*4
        self.is_line_drawn = [False, False]
        self.img_to_display = None

    def launch(self):
        for img_file in glob.glob(self.img_dir + '/*'):
            data = cd.CrosswalkData(img_file)
            self.__initialize_screen()
            self.img_to_display = data.img.copy()
            self.__launch_window()
            data.make_trackbar('tool')

            while not self.is_input_finished:
                cv2.imshow('tool', self.img_to_display)
                self.__draw_line_and_compute_label(data)

                '''
                if cv2.waitKey(1) == 32:
                    break # press 'spacebar' -> turn to next image
                '''
                
                if cv2.waitKey(1) == 120: # press 'x'
                    data.set_invalid()
                    data.write_on_db()
                    break
            
            if self.is_input_finished:
                data.input_manual_meta('tool')
                data.write_on_db()
                
    @staticmethod
    def mouse_callback(event, x, y, flags, annotator):
        annotator.draw_and_record_point(event, x, y, flags)
                                                
    def draw_and_record_point(self, event, x, y, flags):
        if event == cv2.EVENT_LBUTTONDOWN:
            if self.is_line_drawn[1]:
                self.is_input_finished = True
                return

            cv2.circle(self.img_to_display, (x,y), 2, (0, 0, 255), -1)

            self.all_points[self.current_point[0]] = (x, y)
            self.current_point[0] = self.current_point[0] + 1
            self.current_point[1] = (x, y)

    def __draw_line_and_compute_label(self, data):
        if self.current_point[0] == 2 and not self.is_line_drawn[0]:
            cv2.line(self.img_to_display, self.all_points[0],
                    self.all_points[1], (0, 0, 255), 2)
            self.is_line_drawn[0] = True

        if self.current_point[0] == 4 and not self.is_line_drawn[1]:
            cv2.line(self.img_to_display, self.all_points[2],
                    self.all_points[3], (0, 0, 255), 2)
            self.is_line_drawn[1] = True

            loc, ang = self.__compute_label(data)
            data.input_labels(loc, ang)
            self.__write_labels_on_screen(str(loc), str(ang))

    def __initialize_screen(self):
        self.current_point[0] = 0 
        for i in range(4):
            self.all_points[i] = (0, 0)
        self.is_line_drawn[0] = False
        self.is_line_drawn[1] = False
        self.is_input_finished = False

    def __launch_window(self):
        cv2.namedWindow('tool', cv2.WINDOW_FREERATIO)
        #cv2.resizeWindow('tool', 700,720)
        cv2.setMouseCallback('tool', Annotator.mouse_callback, self)
        pass

    def __compute_label(self, data):
        h, w = data.img.shape[:2]
        p1 = self.all_points[0]
        p2 = self.all_points[1]
        p3 = self.all_points[2]
        p4 = self.all_points[3]

        left_line = cl.line(p1, p2)
        right_line = cl.line(p3, p4)
        mid_pt, bottom_width = cl.bottom_mid_point_and_width(h, left_line, right_line)

        loc = cl.compute_loc(mid_pt, w, bottom_width)
        ang = cl.compute_ang(left_line, right_line, mid_pt, h)

        return round(loc, 3), round(ang, 3)

    def __write_labels_on_screen(self, loc, ang):
        cv2.putText(self.img_to_display, loc + '  ' + ang, (15,15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255,255,255), 3)
        cv2.putText(self.img_to_display, loc + '  ' + ang, (15,15),
                cv2.FONT_HERSHEY_SIMPLEX, 0.35, (255,0,0), 1)


#==================#
#       MAIN       # 
#==================#

def launch_annotator(data_path):
    """ the actual 'main' function. Other modules that import this module shall
    call this as the entry point. """
    folder = args.data_path.split('\\')[-1]
    annotator = Annotator(data_path)
    annotator.launch()

def main(args):
    launch_annotator(args.data_path)
        
if __name__ == "__main__":
    args = parse_args()
    main(args)
