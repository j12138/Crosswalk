# crosswalk labeling tool
# use preprocessed_data images
# input both side of crosswalk --> location / direction(angle)

import glob
import cv2
import math
import csv
import crosswalk_data as cd

#===================#
#       CLASS       # 
#===================#

class Annotator(object):
    """ An Annotator displays input window for each image and lets user draw
    points (label) for each image data. """

    def __init__(self, img_dir, draw_point_callback):
        self.img_dir = img_dir
        self.is_input_finished = False
        self.current_point = [0, (0,0)]
        self.all_points = [(0, 0)]*4
        self.is_line_drawn = [False, False]
        self.img_to_display = None
        self.mouse_callback = draw_point_callback

    def launch(self):
        for img_file in glob.glob(self.img_dir + '/*.png'):
            data = cd.CrosswalkData(img_file)
            self.__initialize_screen()
            self.img_to_display = data.img.copy()
            self.__launch_annotator()
            data.make_trackbar('tool')
            
            while not self.is_input_finished:
                cv2.imshow('tool', self.img_to_display)
                self.__draw_line_and_compute_label(data)
                
                if cv2.waitKey(2) == 32:
                    break # press 'spacebar' -> turn to next image

            data.input_manual_meta('tool')
            #data.display_manual_meta()
            #data.display_labels()
            
            if self.is_input_finished:
                data.write_on_csv()
                #data.write_on_db()
                

    def __draw_line_and_compute_label(self, data):
        if self.current_point[0] == 2 and not self.is_line_drawn[0]:
            cv2.line(self.img_to_display, self.all_points[0], self.all_points[1], (0, 0, 255), 2)
            self.is_line_drawn[0] = True

        if self.current_point[0] == 4 and not self.is_line_drawn[1]:
            cv2.line(self.img_to_display, self.all_points[2], self.all_points[3], (0, 0, 255), 2)
            self.is_line_drawn[1] = True

            loc, ang = self.__compute_label(data)
            data.input_labels(loc, ang)
            self.__write_labels_on_screen(loc, ang)

    def __initialize_screen(self):
        self.current_point[0] = 0 
        for i in range(4):
            self.all_points[i] = (0, 0)
        self.is_line_drawn[0] = False
        self.is_line_drawn[1] = False
        self.is_input_finished = False

    def __launch_annotator(self):
        cv2.namedWindow('tool')
        cv2.setMouseCallback('tool', self.mouse_callback, self)
        pass

    def __compute_label(self, data):
        h, w = data.img.shape[:2]
        x1, y1 = self.all_points[0]
        x2, y2 = self.all_points[1]
        x3, y3 = self.all_points[2]
        x4, y4 = self.all_points[3]

        x_1 = float(h - y1) * (x1 - x2) / (y1 - y2) + x2
        x_2 = float(h - y3) * (x3 - x4) / (y3 - y4) + x3

        loc = (w - (x_1 + x_2)) / (x_2 - 1)
        
        x_1 = float(-y1) * (x1 - x2) / (y1 - y2) + x1
        x_2 = float(-y3) * (x3 - x4) / (y3 - y4) + x3
        
        neg = (-1)**(w < (x_2 +  x_1))

        ang = math.atan(0.5 * (w - x_2 + x_1) / h)
        ang = math.degrees(ang) * neg

        return format(loc, '.3f'), format(ang, '.3f')

    def __write_labels_on_screen(self, loc, ang):
        cv2.putText(self.img_to_display, loc + '  ' + ang, (15,15), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 3)
        cv2.putText(self.img_to_display, loc + '  ' + ang, (15,15), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,0,0), 1)
#=======================#
#       FUNCTIONS       # 
#=======================#

def draw_and_record_point(event, x, y, flags, annotator):
    if event == cv2.EVENT_LBUTTONDOWN:

        if annotator.is_line_drawn[1]:
            annotator.is_input_finished = True
            return

        cv2.circle(annotator.img_to_display, (x,y), 3, (0, 0, 255), -1)

        annotator.all_points[annotator.current_point[0]] = (x, y)
        annotator.current_point[0] = annotator.current_point[0] + 1
        annotator.current_point[1] = (x, y)

#==================#
#       MAIN       # 
#==================#
def main():
    
    annotator = Annotator('./preprocessed_data', draw_and_record_point)
    annotator.launch()
        
if __name__ == "__main__":
    main()
