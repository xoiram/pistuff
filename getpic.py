#! /usr/bin/python
#
import cgitb
import picam
import cStringIO
from PIL import Image
from datetime import datetime
import time
import os
cgitb.enable()

filename = '/tmp/forcepic'
with open(filename, "a") as myfile:
	os.chmod(filename, 0777)
	myfile.write("getpicture!!")
	myfile.close()
time.sleep (3)
os.remove(filename)
#print "Content-Type: text/html\n\n"
#print '<html><head><meta content="text/html; charset=UTF-8" />'
#print '<title>Raspberry Pi</title><p>'
#pic = picam.takePhotoWithDetails(1296, 972, 20)
pic = Image.open("/tmp/capturedimage.jpg")  
f = cStringIO.StringIO()
pic.save(f, "JPEG")	
print "Content-type: image/jpg\n"
f.seek(0)
print f.read()
