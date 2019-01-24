# crosswalk labeling tool
# use preprocessed_data images
# input both side of crosswalk --> location / direction(angle)

import glob
import cv2
import math
import csv
import pymongo

IMG_DIR = './preprocessed_data'
path_check_img = "annotated_data\\"
point = [0, (0,0)] # click_cnt, location carrier
points = [(0, 0)]*4

draw_first_line = False
draw_second_line = False

# TODO :: combine common parameter on configure
# class metadata
meta = {
        'obs_car': [0, 1, 0],
        'obs_human': [0, 1, 0],
        'shadow': [0, 1, 0],
        'column': [1, 2, 1],
        'zebra_ratio': [0, 100, 0],
        # not zebra
        'out_of_range' : [0, 1, 0],
        'old' : [0, 1, 0]
        }

#=======================#
#       FUNCTIONS       # 
#=======================#

def draw_point(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:

        global done
        if draw_second_line:
            done = True
            return

        cv2.circle(param, (x,y), 3, (0, 0, 255), -1)

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


# TODO : encapsulate the implementation-level details.

#==================#
#       MAIN       # 
#==================#
def main():
    cv2.namedWindow('tool')
    global points

    for img_file in glob.glob(IMG_DIR + '/*.png'):
        img = cv2.imread(img_file)
        img_name = img_file.split('\\')[1]

        point[0] = 0 
        points = [(0, 0)]*4
        draw_first_line = False
        draw_second_line = False
        done = False
        visual = img.copy()

        cv2.setMouseCallback('tool', draw_point, visual)

        for name in meta:
            cv2.createTrackbar(name, 'tool', meta[name][0], meta[name][1], lambda x: x)
        
        while True:

            cv2.getTrackbarPos('old', 'tool')
            if point[0] == 2 and not draw_first_line:
                print('hello')
                print(points)
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

            if done:
                break

            cv2.imshow('tool', visual)

            # press 'spacebar' -> turn to next image
            if cv2.waitKey(2) == 32:
                break

        for name in meta:
            meta[name][2] = cv2.getTrackbarPos(name, 'tool')
        
        #print(points)

        for name in meta:
            print(meta[name][2])
        
        if draw_first_line and draw_second_line:
            with open('annotation.csv', 'a', newline='') as csvfile:
                mywriter = csv.writer(csvfile)
                mywriter.writerow([img_file, loc, ang])
        

if __name__ == "__main__":
    main()