# crosswalk labeling tool
# use preprocessed_data images
# input both side of crosswalk --> location / direction(angle)
# reference : https://tykimos.github.io/2018/10/16/Simple_Annotation_Tool_1/

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

            cv2.imwrite(path_check_img + img_name +'.png', visual)

        if done: break
        
        cv2.namedWindow('tool')
        cv2.imshow('tool', visual)

        if cv2.waitKey(2) == 32:
            break
        ## TODO: press 'q' --> quit //nested loop break

    print(points)

    if draw_first_line and draw_second_line:
        #result = open('annotation.txt', 'a')
        #result.writelines(img_file + ' ' + loc + ' ' + ang + '\n')
        #result.close()

        # csv
        with open('annotation.csv', 'a', newline='') as csvfile:
            mywriter = csv.writer(csvfile)
            mywriter.writerow([img_file, loc, ang])
        

    



