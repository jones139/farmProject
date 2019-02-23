#!/usr/bin/python
# Make a machine learning training dataset using known farms as examples
# of how farms are depicted on the map.

import getImg
import cv2
import csv
import os

FARMDIR = "/home/graham/Farms/FarmData"
TRAINDIR = "/home/graham/Farms/Training"

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
    imSize = 100

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
        bigDir = os.path.join(farmDir,"big")
        if (not os.path.exists(bigDir)):
            os.makedirs(bigDir)
        trainFarmDir = os.path.join(TRAINDIR,"farm")
        if (not os.path.exists(trainFarmDir)):
            os.makedirs(trainFarmDir)

        for seriesStr in ["OS_6in_1st",
                          #"Google",
                          #"OS_1in_7th",
                          #"Google-Satellite",
                          #"OS_25k",
                          #"OSM"
        ]:
            farmImgFname = os.path.join(farmDir,"%s_%s.png" % (seriesStr,fbody))
            if (not os.path.exists(farmImgFname)):
                print("Making Image for map series %s" % seriesStr)
                img,imgFull = getImg.getFarmImg(seriesStr,osgb_n,osgb_e,imSize)
                if (img is not None):
                    print("Writing image to directory %s." % farmDir)
                    cv2.imwrite(os.path.join(farmDir,"%s_%s.png" % (seriesStr,fbody)),img)
                    cv2.imwrite(os.path.join(bigDir,"%s_%s.png" % (seriesStr,fbody)),imgFull)
                    if (seriesStr == "OS_6in_1st"):
                        # Write image to the 'Farm' training directory
                        cv2.imwrite(os.path.join(trainFarmDir,"%s_%s.png" % (seriesStr,fbody)),img)
                        # FIXME - write a 'not farm' image too....
                else:
                    print("ERROR Creating Image for series %s" % seriesStr);
            else:
                print("Image %s already exists, not doing anything" % farmImgFname)




getFarmMapImgs("farms_NZ.csv")
#getFarmMapImgs("test.csv")
