#! /usr/bin/env python3
#
#The MIT License (MIT)
#Copyright (c) 2014 Ron Ostafichuk
#
#Permission is hereby granted, free of charge, to any person obtaining a copy
#of this software and associated documentation files (the "Software"), to deal
#in the Software without restriction, including without limitation the rights
#to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#copies of the Software, and to permit persons to whom the Software is
#furnished to do so, subject to the following conditions:
#
#The above copyright notice and this permission notice shall be included in all
#copies or substantial portions of the Software.
#
#THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#SOFTWARE.
 
import io
import os
import time
import picamera
import numpy as np
 
widthH = 2592 # too slow for motion check, only use for the save sequence 
heightH = 1944
width = 1440 # use lower resolution for motion check
height = 1080
 
threshold = 30 # how much must the color value (0-255) change to be considered a change
minPixelsChanged = width * height * 2 / 100 # % change  # how many pixels must change to begin a save sequence
print("minPixelsChanged =",minPixelsChanged) # debug
 
print ('Creating in-memory stream')
stream = io.BytesIO()
step = 1  # use this to toggle where the image gets saved
numImages = 1 # count number of images processed
captureCount = 0 # flag used to begin a sequence capture
 
# function to generate a sequence of 20 filenames for the picamera capture_sequence command to use
def filenames():
    frame = 0
    fileName = time.strftime("pics/%Y%m%d/%Y%m%d-%H%M%S-",time.localtime())
    while frame < 20:
        yield '%s%02d.jpg' % (fileName, frame)
        frame += 1
 
# begin monitoring
with picamera.PiCamera() as camera:
    time.sleep(1) # let camera warm up
    try:
        while threshold > 0:
            camera.resolution = (width,height) # use a smaller resolution for higher speed compare
            #print ('Capture ' , numImages)
            if step == 1:
                stream.seek(0)
                camera.capture(stream, 'rgba',True) # use video port for high speed
                data1 = np.fromstring(stream.getvalue(), dtype=np.uint8)
                step = 2
            else:
                stream.seek(0)
                camera.capture(stream, 'rgba',True)
                data2 = np.fromstring(stream.getvalue(), dtype=np.uint8)
                step = 1
            numImages = numImages + 1
 
            if numImages > 4:  # ignore first few images because if the camera is not quite ready it will register as motion right away
                # look for motion unless we are in save mode
                if captureCount <= 0:
                    #print("Compare")
                    # not capturing, test for motion (very simplistic, but works good enough for my purposes)
                    data3 = np.abs(data1 - data2)  # get difference between 2 successive images
                    numTriggers = np.count_nonzero(data3 > threshold) / 4 / threshold #there are 4 times the number of pixels due to rgba
 
                    print("Trigger cnt=",numTriggers)
 
                    if numTriggers > minPixelsChanged:
                        captureCount = 1 # capture ? sequences in a row
                        # make sure directory exists for today
                        d = time.strftime("pics/%Y%m%d") #unfortunately this saves as UTC time instead of local, will fix it later sorry
                        if not os.path.exists(d):
                            os.makedirs(d)
 
                if captureCount > 0:
		    # in capture mode, save an image in hi res
                    camera.resolution = (widthH,heightH)
                    dtFileStr = time.strftime("pics/%Y%m%d/%Y%m%d-%H%M%S-00.jpg",time.localtime()) # once again, UTC time instead of local time
                    print("Saving sequence ",dtFileStr)
                    # save full resolution images to the NAS
                    camera.capture_sequence(filenames(),'jpeg',use_video_port=False, quality=92)
                    captureCount = captureCount-1
 
    finally:
        camera.close()
        print ('Program Terminated')