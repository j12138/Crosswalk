# crosswalk labeling tool
# use preprocessed_data images
# input both side of crosswalk --> location / direction(angle)

import glob
import cv2
import math
import csv

img_files = glob.glob('./preprocessed_data/*.png')
path_check_img = "annotated_data\\"
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

    return

def assign_obs_car(x):
    global obs_car
    obs_car = x

def assign_obs_human(x):
    global obs_human
    obs_human = x

def assign_shadow(x):
    global shadow
    shadow = x

def assign_column(x):  
    global column
    column = x

def assign_zebra_rate(x):
    global zebra_rate
    zebra_rate = x / 100.0

#==================#
#       MAIN       # 
#==================#

cv2.namedWindow('tool')
cv2.setMouseCallback('tool', draw_point)

for img_file in img_files:
    img = cv2.imread(img_file)
    img_name = img_file.split('\\')[1]

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

        if done: break

        
        cv2.namedWindow('tool')
        cv2.imshow('tool', visual)

        if cv2.waitKey(2) == 32:
            break
        ## TODO: press 'q' --> quit //nested loop break

    print(points)
    print(obs_car, obs_human, shadow, column, zebra_rate)
    if draw_first_line and draw_second_line:
        # csv
        with open('annotation.csv', 'a', newline='') as csvfile:
            mywriter = csv.writer(csvfile)
            mywriter.writerow([img_file, loc, ang])
        

    



