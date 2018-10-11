#!/usr/bin/env python3


# import the necessary packages
from collections import deque
import argparse
import imutils
import numpy as np
import cv2
import sys
import tty


camera = cv2.VideoCapture('black_dot.mp4')

watch = True
# keep looping
counter = 0
while True:
    counter = counter + 1
    
    
    (grabbed, frame) = camera.read()
    
    if 'black_dot.mp4' and not grabbed:
        break
    
    #frame = imutils.resize(frame, width = 600)

    
    cv2.imshow("Frame", frame)
    key = cv2.waitKey(1) & 0xFF

        
    if key == ord("q"):
        break
        
    #if ch == ord("s"):
    #    print ("hey")
            
    #if ch == ord("g"):
    #    print ("hi")
        
cv2.waitKey(0) 
camera.release()
cv2.destroyAllWindows()