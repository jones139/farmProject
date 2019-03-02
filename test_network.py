#!/usr/bin/python

# USAGE
# python test_network.py --model <filename> --dataset <folder path>
# Based on https://www.pyimagesearch.com/2017/12/11/image-classification-with-keras-and-deep-learning/

# import the necessary packages
from keras.preprocessing.image import img_to_array
from keras.models import load_model
import numpy as np
import argparse
import imutils
from imutils import paths
import cv2
import random
import time
import os, sys
import ntpath
import shutil

# Size of image to use (input images are scaled to this size)
# Note that I THINK this has to be the same as was used to train the model.
IM_SIZE = (64,64)


def classifyImage(model,image,gui=False):
        """ Classify the image using the image using the given model.
        if gui is True, displays it on the screen.
        """
        orig = image.copy()

        # pre-process the image for classification
        image = cv2.resize(image, IM_SIZE)
        image = image.astype("float") / 255.0
        image = img_to_array(image)
        image = np.expand_dims(image, axis=0)

        # classify the input image
        (normal, pFarm) = model.predict(image)[0]

        # build the label
        label = "Farm" if pFarm > normal else "Normal"
        label = "{}: P={:.1f}%".format(label, pFarm * 100)

        # draw the label on the image
        output = imutils.resize(orig, width=400)
        cv2.putText(output, label, (10, 25),  cv2.FONT_HERSHEY_SIMPLEX,
                0.7, (0, 255, 0), 2)

        # show the output image
        if (gui): cv2.imshow("Output", output)

        return(pFarm,output)


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
ap.add_argument("-m", "--model", required=True,
	help="path to trained model model")
ap.add_argument("-d", "--dataset", required=False,
	help="path to input image dataset")
ap.add_argument("-o", "--outDir", required=False,
	help="path to output directory")
ap.add_argument("-l", "--live", required=False, action="store_true",
        help="Use live images from the camera rather than files")
ap.add_argument("-g", "--gui", required=False, action="store_true",
        help="Show a simple graphical interface that displays the images and analysis results")
args = vars(ap.parse_args())

if (args['outDir'] == None):
        args['outDir'] = "output"

print args



# load the trained convolutional neural network
print("[INFO] loading network...")
model = load_model(args["model"])

if not args['live']:
        # grab the image paths and randomly shuffle them
        imagePaths = sorted(list(paths.list_images(args["dataset"])))
        random.seed(42)
        random.shuffle(imagePaths)

        nNorm = 0
        nNormErr = 0
        nFarm = 0
        nFarmErr = 0

        errorPaths = []

        outFarmDir = os.path.join(args['outDir'],"Farm")
        if (not os.path.exists(outFarmDir)):
            os.makedirs(outFarmDir)
        outNotFarmDir = os.path.join(args['outDir'],"notFarm")
        if (not os.path.exists(outNotFarmDir)):
            os.makedirs(outNotFarmDir)


        # loop over the input images
        for imagePath in imagePaths:
                # load the image, 
                image = cv2.imread(imagePath)
                fname = ntpath.basename(imagePath)
                pFarm,outimg = classifyImage(model,image,args['gui'])
                if (args['gui']):
                        cv2.waitKey(5000)
                        if (pFarm>0.5):
                                label = "**** farm *****"
                        else:
                                label = "not farm"
                        label = "{}: P(farm)={:.0f}%".format(label, pFarm * 100)
                        print("imagePath=%s" % imagePath)
                        print (label)
                else:
                        sys.stdout.write(".")
                        sys.stdout.flush()
                # We expect all images to be in a directory named its
                # class name (e.g. 'normal' or 'odd'
                imgClass = imagePath.split(os.path.sep)[-2]
                if (imagePath.find('notFarm')==-1):
                        nFarm+=1
                        if (pFarm<0.5):
                                sys.stdout.write("*")
                                sys.stdout.flush()
                                nFarmErr+=1
                                errorPaths.append(imagePath)
                                outPath = os.path.join(outFarmDir,fname)
                                shutil.copyfile(imagePath,outPath)
                else:
                        nNorm+=1
                        if (pFarm>=0.5):
                                sys.stdout.write("|")
                                sys.stdout.flush()
                                nNormErr+=1
                                errorPaths.append(imagePath)
                                outPath = os.path.join(outNotFarmDir,fname)
                                shutil.copyfile(imagePath,outPath)


        print ("")
        print ("************************")
        print ("*     RESULTS          *")
        print ("************************")
        print ("")
        print ("Number of Farm Images Tested = %d" % nFarm)
        print ("Number of Farm Image Errors  = %d" % nFarmErr)
        if (nFarm>0):
                print ("  Farm Detection Reliability = %d%%" % (100-int(100*nFarmErr/nFarm))) 
        print ("")
        print ("Number of Normal Images Tested = %d" % nNorm)
        print ("Number of Normal Image Errors  = %d" % nNormErr)
        if (nNorm>0):
                print ("  Normal Detection Reliability = %d%%" % (100-int(100*nNormErr/nNorm)))
        print ("")
        print (" Images incorrectly classified:")
        for p in errorPaths:
                print p

else:
        print("Live images not working yet!")

