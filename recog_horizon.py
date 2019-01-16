
#  crosswalk direction analysis by horizontal line

import numpy as np
import cv2
import math
import glob

img_files = glob.glob('./preprocessed_data/above/*.png')


cv2.namedWindow('dir')

for img_file in img_files:
    img = cv2.imread(img_file)
    img_name = img_file.split('\\')[1]

    #visual = img.copy()

    #------------------------------------------#

    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    eq = cv2.equalizeHist(gray_img)

    lower = 190
    upper = 255
    
    mask = cv2.inRange(eq,lower,upper)
    cv2.imshow('dir',mask)

    #-----------------------------------------#

    bw_width = 170 
    bxLeft = []
    byLeft = []
    bxbyLeftArray = []
    bxbyRightArray = []
    bxRight = []
    byRight = []
    boundedLeft = []
    boundedRight = []

      #3. find contours and  draw the green lines on the white strips
    _ , contours,hierarchy = cv2.findContours(mask,cv2.RETR_TREE,cv2.CHAIN_APPROX_NONE )
    
    visual = cv2.drawContours(img, [contours[0]], -1, (0,255,0), 3)
    '''
    for i in contours:

        bx,by,bw,bh = cv2.boundingRect(i)

        if (bw > bw_width):
                
            cv2.line(visual,(bx,by),(bx+bw,by),(0,255,0),2) # draw the a contour line
            bxRight.append(bx+bw) #right line
            byRight.append(by) #right line
            bxLeft.append(bx) #left line
            byLeft.append(by) #left line
            bxbyLeftArray.append([bx,by]) #x,y for the left line
            bxbyRightArray.append([bx+bw,by]) # x,y for the left line
            cv2.circle(visual,(int(bx),int(by)),5,(0,250,250),2) #circles -> left line
            cv2.circle(visual,(int(bx+bw),int(by)),5,(250,250,0),2) #circles -> right line
        '''
        


    while True:
        
            
        #print('hi!')
        cv2.imshow('dir', visual)

        if cv2.waitKey(2) == 32:
            break
        ## TODO: press 'q' --> quit //nested loop break


    



