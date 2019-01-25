# crosswalk labeling tool
# use preprocessed_data images
# input both side of crosswalk --> location / direction(angle)

import glob
import cv2
import math
import csv
import pymongo
import crosswalk_data as cd

class Annotator(object):
    """ An Annotator displays input window for each image and lets user draw
    points (label) for each image data. """

    def __init__(self, img_dir):
        self.img_dir = img_dir
        self.is_input_finshed = False

    def launch(self):
        for img in glob.glob(self.img_dir + '/*.png'):
            pass # in progress
            data = cd.CrosswalkData(img_file)
            self.__initialize_screen()
            img_to_display = data.img.copy()
            launch_annotator(img_to_display, drawn_line)
            data.make_trackbar('tool')
            
            while True:
                cv2.imshow('tool', img_to_dislay)
                draw_line_and_compute_label(data, img_to_dislay, drawn_line)
                
                if self.is_input_finished:
                    break

                if cv2.waitKey(2) == 32:
                    break # press 'spacebar' -> turn to next image

            data.input_manual_meta('tool')
            data.display_manual_meta()
            data.display_labels()
            write_on_csv(drawn_line, data)

    def draw_line_and_compute_label(data, visual, drawn_line):
        if point[0] == 2 and not drawn_line[0]:
            cv2.line(visual, points[0], points[1], (0, 0, 255), 2)
            drawn_line[0] = True

        if point[0] == 4 and not drawn_line[1]:
            cv2.line(visual, points[2], points[3], (0, 0, 255), 2)
            drawn_line[1] = True

            loc, ang = compute_label(data.img, points)
            data.input_labels(loc, ang)
            write_labels_on_screen(visual, loc, ang)

    def __initialize_screen():
        global done
        point[0] = 0 
        for i in range(4):
            points[i] = (0, 0)
        drawn_line[0] = False
        drawn_line[1] = False
        done = False



IMG_DIR = './preprocessed_data'
path_check_img = "annotated_data\\"
point = [0, (0,0)] # click_cnt, location carrier
points = [(0, 0)]*4
drawn_line = [False, False]
done = False

# TODO :: combine common parameter on configure


#=======================#
#       FUNCTIONS       # 
#=======================#

def launch_annotator(visual, drawn_line):
    cv2.namedWindow('tool')
    cv2.setMouseCallback('tool', draw_point, [visual, drawn_line])
    pass

def write_labels_on_screen(visual, loc, ang):
    cv2.putText(visual, loc + '  ' + ang, (15,15), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 3)
    cv2.putText(visual, loc + '  ' + ang, (15,15), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,0,0), 1)

def draw_point(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:

        global done

        if param[1][1]:
            done = True
            return

        cv2.circle(param[0], (x,y), 3, (0, 0, 255), -1)

        global point, points
        points[point[0]] = (x, y)
        point[0] = point[0] + 1
        point[1] = (x, y)

        #print (point[0], points)

def compute_label(img, points):
    h, w = img.shape[:2]
    x1, y1 = points[0]
    x2, y2 = points[1]
    x3, y3 = points[2]
    x4, y4 = points[3]

    x_1 = float(h - y1) * (x1 - x2) / (y1 - y2) + x2
    x_2 = float(h - y3) * (x3 - x4) / (y3 - y4) + x3

    loc = (w - (x_1 + x_2)) / (x_2 - 1)
    
    x_1 = float(-y1) * (x1 - x2) / (y1 - y2) + x1
    x_2 = float(-y3) * (x3 - x4) / (y3 - y4) + x3
    #print (x_1, x_2)
    neg = (-1)**(w < (x_2 +  x_1))
    #print(neg)

    ang = math.atan(0.5 * (w - x_2 + x_1) / h)
    ang = math.degrees(ang) * neg

    return format(loc, '.3f'), format(ang, '.3f')

def draw_line_and_compute_label(data, visual, drawn_line):
    if point[0] == 2 and not drawn_line[0]:
        cv2.line(visual, points[0], points[1], (0, 0, 255), 2)
        drawn_line[0] = True

    if point[0] == 4 and not drawn_line[1]:
        cv2.line(visual, points[2], points[3], (0, 0, 255), 2)
        drawn_line[1] = True

        loc, ang = compute_label(data.img, points)
        data.input_labels(loc, ang)
        write_labels_on_screen(visual, loc, ang)

def write_on_csv(drawn_line, data):
    if drawn_line[0] and drawn_line[1]:
        with open('annotation.csv', 'a', newline='') as csvfile:
            mywriter = csv.writer(csvfile)
            mywriter.writerow([data.img_file, data.labels['loc'], data.labels['ang']])

def initialize_screen():
    global done
    point[0] = 0 
    for i in range(4):
        points[i] = (0, 0)
    drawn_line[0] = False
    drawn_line[1] = False
    done = False


#==================#
#       MAIN       # 
#==================#
def main():
    
    for img_file in glob.glob(IMG_DIR + '/*.png'):

        data = cd.CrosswalkData(img_file)
        initialize_screen()
        visual = data.img.copy()
        launch_annotator(visual, drawn_line)
        data.make_trackbar('tool')
        
        while True:
            cv2.imshow('tool', visual)
            draw_line_and_compute_label(data, visual, drawn_line)
            
            if done:
                break

            if cv2.waitKey(2) == 32:
                break # press 'spacebar' -> turn to next image

        data.input_manual_meta('tool')
        data.display_manual_meta()
        data.display_labels()
        write_on_csv(drawn_line, data)
        
if __name__ == "__main__":
    main()
