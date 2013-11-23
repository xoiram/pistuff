#!/usr/bin/python

import os
import sys
import time
from datetime import datetime
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw 
import picam

# Motion detection settings:
# Threshold (how much a pixel has to change by to be marked as "changed")
# Sensitivity (how many changed pixels before capturing an image)
# ForceCapture (whether to force an image to be captured every forceCaptureTime seconds)
threshold = 50
sensitivity = 300

# File settings
saveWidth = 1296
saveHeight = 972

cmpWidth = 100
cmpHeigth = 100
diskSpaceToReserve = 40 * 1024 * 1024 # Keep 40 mb free on disk
basefolder = "/home/pi"

picam.config.imageFX = picam.MMAL_PARAM_IMAGEFX_NONE
picam.config.exposure = picam.MMAL_PARAM_EXPOSUREMODE_NIGHT
picam.config.meterMode = picam.MMAL_PARAM_EXPOSUREMETERINGMODE_AVERAGE
picam.config.awbMode = picam.MMAL_PARAM_AWBMODE_OFF
picam.config.ISO = 1600

picam.config.sharpness = 0               # -100 to 100
picam.config.contrast = 0              # -100 to 100
picam.config.brightness = 50             #  0 to 100
picam.config.saturation = 10              #  -100 to 100
picam.config.videoStabilisation = 0      # 0 or 1 (false or true)
picam.config.exposureCompensation  = +5   # -10 to +10 ?
picam.config.rotation = 0               # 0-359
picam.config.hflip = 0                   # 0 or 1
picam.config.vflip = 0                   # 0 or 1
picam.config.shutterSpeed = 25000

# Capture a small test image (for motion detection)
def captureTestImage():
    im = picam.takeRGBPhotoWithDetails(cmpWidth,cmpHeigth)
    return im

def drawTimestampOnPicture(pic):
    draw = ImageDraw.Draw(pic)
    font = ImageFont.truetype("/usr/share/fonts/truetype/droid/DroidSerif-Bold.ttf", 32)
    time = datetime.now()
    timestamp = "%04d-%02d-%02d %02d:%02d:%02d" % (time.year, time.month, time.day, time.hour, time.minute, time.second)

    x, y = 970, 935
    bordercolor = (0,0,0)
    draw.text((x-1, y-1), timestamp, font=font, fill=bordercolor)
    draw.text((x+1, y-1), timestamp, font=font, fill=bordercolor)
    draw.text((x-1, y+1), timestamp, font=font, fill=bordercolor)
    draw.text((x+1, y+1), timestamp, font=font, fill=bordercolor)

    draw.text((x, y),timestamp,(240,240,240),font=font)
    return pic

def captureWebImage():
    pic = picam.takePhotoWithDetails(1296, 972, 20)
    drawTimestampOnPicture(pic)
    pic.save("/tmp/capturedimage.jpg")

# Save a full size image to disk
def saveImage(width, height, diskSpaceToReserve):
    keepDiskSpaceFree(diskSpaceToReserve)
    time = datetime.now()
    #filename = "capture-%04d%02d%02d-%02d%02d%02d.jpg" % (time.year, time.month, time.day, time.hour, time.minute, time.second)
    #subprocess.call("raspistill -w 1296 -h 972 -t 0 -e jpg -q 15 -o %s" % filename, shell=True)
    
    folder = "%s/%04d-%02d-%02d" % (basefolder, time.year, time.month, time.day)
    if not os.path.exists(folder):
        os.makedirs(folder)

    quality = 10

    for x in range(1,2):
        filename = "%s/cam-%02d%02d%02d-%02d.jpg" % (folder, time.hour, time.minute, time.second, x)
        pic = picam.takePhotoWithDetails(width, height, quality)
        drawTimestampOnPicture(pic)
        pic.save(filename)
    
    #filename = "%s/cam-%02d%02d%02d-" % (folder, time.hour, time.minute, time.second)
    #filename += "%02d.jpg"
    #subprocess.call("raspistill -w %d -h %d -ex auto -e jpg -q %d -tl 100 -t 800 -o %s" % width, height, quality, filename, shell=True)
    #subprocess.call("raspistill -w 1296 -h 972 -tl 1000 -t 9000 -ex auto -e jpg -q 15 -o %s" % filename, shell=True)
    
#    print "Captured %s" % filename

# Keep free space above given level
def keepDiskSpaceFree(bytesToReserve):
    if (getFreeSpace() < bytesToReserve):
        for filename in sorted(os.listdir(".")):
            if filename.startswith("capture") and filename.endswith(".jpg"):
                os.remove(filename)
                print "Deleted %s to avoid filling disk" % filename
                if (getFreeSpace() > bytesToReserve):
                    return

# Get available disk space
def getFreeSpace():
    st = os.statvfs(".")
    du = st.f_bavail * st.f_frsize
    return du
       
print "Starting motion capture"
if not os.path.exists(basefolder):
    print "Output folder does not exist. Mounted?"
    sys.exit()

# Get first image
image1 = captureTestImage()
cmpMaxPixels = cmpWidth * cmpHeigth
print "cmpMaxPixels:",cmpMaxPixels
while (True):
    # Get comparison image
    image2 = captureTestImage()
    (modified,changedPixels) = picam.difference(image1,image2,threshold)
    image1 = image2
    
    logtime = datetime.now()    
    timestamp = "%04d-%02d-%02d %02d:%02d:%02d" % (logtime.year, logtime.month, logtime.day, logtime.hour, logtime.minute, logtime.second)
    # Save an image if pixels changed
    if changedPixels > sensitivity:
        if changedPixels < cmpMaxPixels:
            print "%s - change detected" % timestamp, changedPixels
            saveImage(saveWidth, saveHeight, diskSpaceToReserve)
            #picam.saveRGBToImage(image1, "/tmp/pic1.bmp", cmpWidth, cmpHeigth)
            #picam.saveRGBToImage(image2, "/tmp/pic2.bmp", cmpWidth, cmpHeigth)
        else:
            print "%s - to many changed" % timestamp, changedPixels
#    else:
#        print "%s - not enough changed" % timestamp, changedPixels

    
    if(os.path.isfile("/tmp/forcepic")):
        print "%s - Taking picture for web" % timestamp
        captureWebImage()
    
    # time.sleep (0.5);
