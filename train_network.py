#!/usr/bin/python

# USAGE
# python train_network.py --dataset images --model ann.model

# Based on https://www.pyimagesearch.com/2017/12/11/image-classification-with-keras-and-deep-learning/
# And https://www.learnopencv.com/image-classification-using-convolutional-neural-networks-in-keras/

# set the matplotlib backend so figures can be saved in the background
import matplotlib
matplotlib.use("Agg")

# import the necessary packages
import keras
from keras.preprocessing.image import ImageDataGenerator
from keras.optimizers import Adam
from sklearn.model_selection import train_test_split
from keras.preprocessing.image import img_to_array
from keras.utils import to_categorical
from keras.models import Sequential
from keras.layers.convolutional import Conv2D
from keras.layers.convolutional import MaxPooling2D
from keras.layers.core import Activation
from keras.layers.core import Flatten
from keras.layers.core import Dense
from keras.layers.core import Dropout
from keras import backend as K

from imutils import paths
import matplotlib.pyplot as plt
import numpy as np
import argparse
import random
import cv2
import os



def initialiseModel(width, height, depth, classes):
        # initialize the model
        model = Sequential()
        inputShape = (height, width, depth)

        # if we are using "channels first", update the input shape
        if K.image_data_format() == "channels_first":
                inputShape = (depth, height, width)

        # first set of CONV => RELU => POOL layers
        model.add(Conv2D(32, (3, 3), padding="same",
                input_shape=inputShape))
        model.add(Activation("relu"))
        model.add(Conv2D(32, (3, 3)))
        model.add(Activation("relu"))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.25))

        # second set of CONV => RELU => POOL layers
        model.add(Conv2D(64, (3, 3), padding='same'))
        model.add(Activation("relu"))
        model.add(Conv2D(64, (3, 3)))
        model.add(Activation("relu"))
        model.add(MaxPooling2D(pool_size=(2, 2)))
        model.add(Dropout(0.25))

        # third set of CONV => RELU => POOL layers
        #model.add(Conv2D(64, (3, 3), padding='same', activation='relu'))
        #model.add(Conv2D(64, (3, 3), activation='relu'))
        #model.add(MaxPooling2D(pool_size=(2, 2)))
        #model.add(Dropout(0.25))

        # first (and only) set of FC => RELU layers
        model.add(Flatten())
        model.add(Dense(512))
        model.add(Activation("relu"))
        model.add(Dropout(0.5))

        # softmax classifier
        model.add(Dense(classes))
        model.add(Activation("softmax"))

        # return the constructed network architecture
        return model


# construct the argument parse and parse the arguments
ap = argparse.ArgumentParser()
#ap.add_argument("-o", "--oddset", required=True,
#	help="path to odd examples dataset")
#ap.add_argument("-n", "--normalset", required=True,
#	help="path to normal examples dataset")
ap.add_argument("-i", "--imageDir", required=True,
	help="path to directory of images - can be a tree structure but the final two folders in each branch should be 'Normal' and 'Odd'")
ap.add_argument("-m", "--model", required=True,
	help="path to output model")
ap.add_argument("-r", "--ratio", required=False,
	help="Normal to odd image ratio (e.g. 3 means use 3 normal images for every odd one")
ap.add_argument("-p", "--plot", type=str, default="plot.png",
	help="path to output loss/accuracy plot")
args = vars(ap.parse_args())

# initialize the number of epochs to train for, initia learning rate,
# and batch size
EPOCHS = 25   # was 25
INIT_LR = 1e-4  # was 1e-3
INIT_DECAY = 1e-6
BS = 32
# Suppress Tensorflow debugging warnings (because we get lots about memory)
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# Size of image to use (input images are scaled to this size)
IM_SIZE = (64,64)

# initialize the data and labels
print("[INFO] loading images - imageDir=%s" % args["imageDir"])
data = []
labels = []

# grab the image paths and randomly shuffle them
farmImagePaths = []
notFarmImagePaths=[]
notFarmImagePathsAll = []
allImagePaths = sorted(list(paths.list_images(args["imageDir"])))
#print(allImagePaths)
for imPath in allImagePaths:
        if (imPath.find("notFarm")==-1):
                farmImagePaths.append(imPath)
        else:
                notFarmImagePathsAll.append(imPath)


for imPath in farmImagePaths:
        print imPath
print("**********************************\n * NOT FARM *\n***************")
for imPath in notFarmImagePathsAll:
        print imPath
#exit(-1)

random.seed(42)
random.shuffle(farmImagePaths)
random.shuffle(notFarmImagePathsAll)


# Create a set of not-farm images from the available ones.
if (args['ratio']==None):
        normFactor = 1 # Use one normal image for each odd image.
else:
        normFactor = int(args['ratio'])  

print("Read %d Farm images" % (len(farmImagePaths)))
print("Read %d not-Farm images" % (len(notFarmImagePathsAll)))

print ("Using normFactor ratio of %d" % normFactor)
while (len(notFarmImagePaths)<len(farmImagePaths)*normFactor):
        notFarmImagePaths.append(notFarmImagePathsAll[0])
        #print normalImagePaths
        notFarmImagePathsAll = notFarmImagePathsAll[1:]

print("Using %d farm images" % (len(farmImagePaths)))
print("Using %d not-Farm images" % (len(notFarmImagePaths)))

# Merge the farm and non-farm lists
imagePaths = farmImagePaths
imagePaths.extend(notFarmImagePaths)

# and randomise the order
random.shuffle(imagePaths)  

# loop over the input images
for imagePath in imagePaths:
        #print("imagePath=%s" % imagePath)
	# load the image, pre-process it, and store it in the data list
	image = cv2.imread(imagePath)
	image = cv2.resize(image, IM_SIZE)
	image = img_to_array(image)
	data.append(image)

	# extract the class label from the image path and update the
	# labels list
	if (imagePath.find("notFarm") == -1):
                label = 1
        else:
                label = 0
	labels.append(label)

print(labels)

#exit(-1)
        
# scale the raw pixel intensities to the range [0, 1]
data = np.array(data, dtype="float") / 255.0
labels = np.array(labels)

# partition the data into training and testing splits using 75% of
# the data for training and the remaining 25% for testing
(trainX, testX, trainY, testY) = train_test_split(data,
	labels, test_size=0.25, random_state=42)

# convert the labels from integers to vectors
trainY = to_categorical(trainY, num_classes=2)
testY = to_categorical(testY, num_classes=2)

# construct the image generator for data augmentation
aug = ImageDataGenerator(rotation_range=30, width_shift_range=0.1,
	height_shift_range=0.1, shear_range=0.2, zoom_range=0.2,
	horizontal_flip=True, fill_mode="nearest")

# initialize the model
print("[INFO] compiling model...")
model = initialiseModel(width=IM_SIZE[0], height=IM_SIZE[1], depth=3, classes=2)
#opt = Adam(lr=INIT_LR, decay=INIT_LR / EPOCHS)
opt = keras.optimizers.rmsprop(lr=INIT_LR, decay=INIT_DECAY)
model.compile(loss="categorical_crossentropy", optimizer=opt,
	metrics=["accuracy"])

print(model.summary())

# train the network
print("[INFO] training network...")
aug.fit(trainX)
H = model.fit_generator(aug.flow(trainX, trainY, batch_size=BS),
	validation_data=(testX, testY), steps_per_epoch=len(trainX) // BS,
	epochs=EPOCHS, verbose=1)

# save the model to disk
print("[INFO] serializing network...")
model.save(args["model"])

# plot the training loss and accuracy
plt.style.use("ggplot")
plt.figure()
N = EPOCHS
plt.plot(np.arange(0, N), H.history["loss"], label="train_loss")
plt.plot(np.arange(0, N), H.history["val_loss"], label="val_loss")
plt.plot(np.arange(0, N), H.history["acc"], label="train_acc")
plt.plot(np.arange(0, N), H.history["val_acc"], label="val_acc")
plt.title("Training Loss and Accuracy on Santa/Not Santa")
plt.xlabel("Epoch #")
plt.ylabel("Loss/Accuracy")
plt.legend(loc="lower left")
plt.savefig(args["plot"])
