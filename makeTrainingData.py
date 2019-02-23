#!/usr/bin/python
# Make a machine learning training dataset using known farms as examples
# of how farms are depicted on the map.

import getImg
import cv2
import csv
import os

FARMDIR = "/home/graham/Farms/FarmData"

def test():
    print("test()")
    osgb_n = 447222.0
    osgb_e = 534550.0
    imSize = 50
    seriesStr = "OS_6in_1st"
    img = getImg.getFarmImg(seriesStr,osgb_n,osgb_e,imSize)
    cv2.imwrite("img.png",img)


def getFarmMapImgs(csvFname):
    print ("getFarmMapImgs(%s)" % csvFname)
    imSize = 50

    f = open(csvFname, "r")
    reader = csv.reader(f)
    reader.next()  # skip first row
    for i, line in enumerate(reader):
        print 'line[{}] = {}'.format(i, line)
        fbody = line[0].rstrip()
        fname = "%s.png" % fbody
        osgb_n = line[3]
        osgb_e = line[4]
        farmDir = os.path.join(FARMDIR,fbody)
        if (not os.path.exists(farmDir)):
            os.makedirs(farmDir)

        for seriesStr in ["OS_6in_1st","OS_1in_7th","OS_25k","OSM"]:
            img,imgFull = getImg.getFarmImg(seriesStr,osgb_n,osgb_e,imSize)
            cv2.imwrite(os.path.join(farmDir,"%s_%s.png" % (seriesStr,fbody)),img)
            cv2.imwrite(os.path.join(farmDir,"%s_%s_big.png" % (seriesStr,fbody)),imgFull)
        
        




#getFarmMapImgs("farms_NZ.csv")
getFarmMapImgs("test.csv")
