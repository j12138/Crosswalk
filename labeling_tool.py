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
            data.display_manual_meta()
            data.display_labels()
            
            if self.is_input_finished:

                data.write_on_csv()

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

<<<<<<< HEAD
img_files = glob.glob('./preprocessed_data/*.png')
path_check_img = "annotated_data/"
point = [0, (0,0)] # click_cnt, location carrier

#=======================#
#       FUNCTIONS       # 
#=======================#

def draw_point(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:

        global done
        if draw_second_line:
            done = True
            return

        cv2.circle(visual, (x,y), 3, (0, 0, 255), -1)

        global point, points
        points[point[0]] = (x, y)
        point[0] = point[0] + 1
        point[1] = (x, y)

        print (point[0], points)


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
    print (x_1, x_2)
    neg = (-1)**(w < (x_2 +  x_1))
    print(neg)

    ang = math.atan(0.5 * (w - x_2 + x_1) / h)
    ang = math.degrees(ang) * neg

    return format(loc, '.3f'), format(ang, '.3f')

def get_manual_metadata():
    # TODO :: write manual metadata

    print('obs_car(0,1) : ')
    cv2.waitKey(0)
    obs_car = int(input())
    
    print('obs_human(0,1) : ')
    cv2.waitKey(0)
    obs_human = int(input())

    print('shadow(0,1) : ')
    cv2.waitKey(0)
    shadow = int(input())

    print('zebra_rate(0-1) : ')
    cv2.waitKey(0)
    zebra_rate = float(input())

    print('column(1,2) : ')
    cv2.waitKey(0)
    column = int(input())

    print(obs_car, obs_human, shadow, zebra_rate, column)
=======
    def __compute_label(self, data):
        h, w = data.img.shape[:2]
        x1, y1 = self.all_points[0]
        x2, y2 = self.all_points[1]
        x3, y3 = self.all_points[2]
        x4, y4 = self.all_points[3]
>>>>>>> b0fed260fd6bbea943d0e425d26586d3b2b02c7d

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
<<<<<<< HEAD

cv2.namedWindow('tool')
cv2.setMouseCallback('tool', draw_point)

# NOTE(TJ): I see that `img_files` is defined in a much earlier line while it's
# only being used here in the `for` statement. It's generally better to keep
# the definition and usage close together. Even better, in this particular
# case, is to have the configuration variable separate at the top like 
#   IMG_DIR = './preprocessed_data'
# and use it in the `for` such as:
#   for img_file in glob.glob(IMG_DIR + '/*.png'):
# in my opinion.
for img_file in img_files:
    img = cv2.imread(img_file)
    img_name = img_file.split('/')[-1]

    point[0] = 0 
    points = [(0, 0)]*4
    draw_first_line = False
    draw_second_line = False
    done = False
    visual = img.copy()

    #cv2.imshow('tool', visual)
    #get_manual_metadata()

    obs_car = 0
    obs_human = 0
    shadow = 0
    column = 1
    zebra_rate = 0.0

    # NOTE(TJ): I think you can deal with this issue of having to define a
    # function only to assign a value to a variable by introducing lambda
    # functions. Please look at the sample code at `lambda_sample` function and
    # refactor the code accordingly.
    cv2.createTrackbar('obs_car', 'tool', 0, 1, assign_obs_car)
    cv2.createTrackbar('obs_human', 'tool', 0, 1, assign_obs_human)
    cv2.createTrackbar('shadow', 'tool', 0, 1, assign_shadow)
    cv2.createTrackbar('column', 'tool', 1, 2, assign_column)
    cv2.createTrackbar('zebra_rate', 'tool', 0, 100, assign_zebra_rate)

    while True:
        if point[0] == 2 and not draw_first_line:
            cv2.line(visual, points[0], points[1], (0, 0, 255), 2)
            draw_first_line = True

        if point[0] == 4 and not draw_second_line:
            cv2.line(visual, points[2], points[3], (0, 0, 255), 2)
            draw_second_line = True

            loc, ang = compute_label(img, points)
            print(loc, ang)

            cv2.putText(visual, loc + '  ' + ang, (15,15), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,255,255), 3)
            cv2.putText(visual, loc + '  ' + ang, (15,15), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255,0,0), 1)

            #cv2.imwrite(path_check_img + img_name +'.png', visual)

        # NOTE(TJ): it is better to line-break these two statements.
        if done: break

        
        cv2.namedWindow('tool')
        cv2.imshow('tool', visual)

        if cv2.waitKey(2) == 32:
            # NOTE(TJ): What does it mean that a waitKey(2) equals 32 ? When
            # the intent of the code is not obvious by reading it, as a general
            # principle, it is better to leave a comment of its intent.
            break
        ## TODO: press 'q' --> quit //nested loop break

    print(points)
    print(obs_car, obs_human, shadow, column, zebra_rate)
    if draw_first_line and draw_second_line:
        # csv
        with open('annotation.csv', 'a', newline='') as csvfile:
            mywriter = csv.writer(csvfile)
            mywriter.writerow([img_file, loc, ang])
        

=======
def main():
>>>>>>> b0fed260fd6bbea943d0e425d26586d3b2b02c7d
    
    annotator = Annotator('./preprocessed_data', draw_and_record_point)
    annotator.launch()
        
if __name__ == "__main__":
    main()
