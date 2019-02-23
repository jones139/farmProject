#!/usr/bin/python

import math
import pyproj
import urllib2
import os
import cv2
import skimage
import skimage.io
import numpy as np

#  Hart Mill Farm , 447222.0 , 534550.0
# 027C806B-3BF0-4D10-B55A-B77337313780 , Hart Mill Farm , 447222.0 , 534550.0
# From https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Lon..2Flat._to_tile_numbers_2

IMG_EXTRACT_SIZE = 50  # pixels

def latlon2tilexy(lat_deg, lon_deg, zoom):
  """
  Based on https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
  """
  lat_rad = math.radians(lat_deg)
  n = 2.0 ** zoom
  xtile = int((lon_deg + 180.0) / 360.0 * n)
  ytile = int((1.0 - math.log(math.tan(lat_rad)
                              + (1 / math.cos(lat_rad)))
               / math.pi) / 2.0 * n)
  return (xtile, ytile)


def tilexy2latlon(xtile, ytile, zoom):
  """
  Returns the NW-corner of the square
  Based on https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames
  """
  n = 2.0 ** zoom
  lon_deg = xtile / n * 360.0 - 180.0
  lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
  lat_deg = math.degrees(lat_rad)
  return (lat_deg, lon_deg)



def osgb2latlon(osgb_n,osgb_e):
    #osgb = pyproj.Proj('+proj=tmerc +lat_0=49 +lon_0=-2 +k=0.9996012717 +x_0=400000 +y_0=-100000 +ellps=airy +towgs84=446.448,-125.157,542.06,0.15,0.247,0.842,-20.489 +units=m +no_defs ');
    #wgs84 = pyproj.Proj('+proj=longlat +datum=WGS84 +no_defs ');
    osgb = pyproj.Proj(init='epsg:27700')
    wgs84 = pyproj.Proj(init='epsg:4326')
    lon,lat= pyproj.transform(osgb,wgs84,osgb_n,osgb_e);
    return (lon,lat)

def getTileUrl(seriesStr,x,y,z):
    if (seriesStr is "OS_6in_1st"):
        url = "https://nls-3.tileserver.com/fpsUZbULUtp1/%d/%d/%d.jpg" % (z,x,y)
    elif (seriesStr is "OS_1in_7th"): #1955-1961
        url = "https://nls-3.tileserver.com/fpsUZbc4ftb2/%d/%d/%d.jpg" % (z,x,y)
    elif (seriesStr is "OS_25k"):  # 1937-1961
        url = "https://nls-3.tileserver.com/fpsUZbIoj0Oa/%d/%d/%d.jpg" % (z,x,y)
    elif (seriesStr is "OSM"):
        url = "http://c.tile.openstreetmap.org/%d/%d/%d.png" % (z,x,y)        
    else:
        print("Unrecognised Series %s." % seriesStr)
        url = "error"

    return url
        

def getImg(seriesStr,x,y,z):
  url = getTileUrl(seriesStr,x,y,z)
  print("getImg() - url=%s" % url);
  
  user_agent = 'Mozilla/5.0 (Windows NT 6.1; Win64; x64)'
  headers = {'User-Agent': user_agent}
  req = urllib2.Request(url,None,headers)
  response = urllib2.urlopen(req)
  print response.info()
  data = response.read()
  response.close()

  #return data
  path = os.getcwd()
  filename = "img.jpg"
  file_path = "%s/%s" % (path, filename)
  print("file_path = %s" % file_path)
  downloaded_image = file(file_path, "wb")
  downloaded_image.write(data)
  downloaded_image.close()


def openImg(seriesStr,x,y,z):
  """ Returns an opencv compatible image of the tile of the given
  map series at mercator coordinates x,y and zoom level z.
  """
  url = getTileUrl(seriesStr,x,y,z)
  print("getImg() - url=%s" % url);
  imgRGB = skimage.io.imread(url)
  img = cv2.cvtColor(imgRGB,cv2.COLOR_BGR2RGB)
  #cv2.imshow("original",imgRGB)
  #cv2.imshow("corrected",img)
  #cv2.waitKey(0)
  return img


def getCompositeImg(seriesStr,x,y,z):
  """ Returns a composite image of 9 tiles in a 3x3 matrix, centred
  on x,y at zoom level z.
  """
  # Get the 9 images to make up the array.
  img11 = skimage.io.imread(getTileUrl(seriesStr, x-1, y-1, z))
  img12 = skimage.io.imread(getTileUrl(seriesStr, x+0, y-1, z))
  img13 = skimage.io.imread(getTileUrl(seriesStr, x+1, y-1, z))
  img21 = skimage.io.imread(getTileUrl(seriesStr, x-1, y+0, z))
  img22 = skimage.io.imread(getTileUrl(seriesStr, x+0, y+0, z))
  img23 = skimage.io.imread(getTileUrl(seriesStr, x+1, y+0, z))
  img31 = skimage.io.imread(getTileUrl(seriesStr, x-1, y+1, z))
  img32 = skimage.io.imread(getTileUrl(seriesStr, x+0, y+1, z))
  img33 = skimage.io.imread(getTileUrl(seriesStr, x+1, y+1, z))

  row1 = np.hstack([img11, img12, img13])
  row2 = np.hstack([img21, img22, img23])
  row3 = np.hstack([img31, img32, img33])

  imgRGB = np.vstack([row1, row2, row3])
  img = cv2.cvtColor(imgRGB,cv2.COLOR_BGR2RGB)

  return img


def getPixelCoords(lat,lon,x,y,z):
  """ returns the pixel coordinatex xpx,ypx of point (lat,lon) in deg
  within tile (x,y,z) - assuming tile is a 3x3 array of 256 pixel square images,
  centred on (x,y,z).
  """
  tilex = 256  # size of tile in pixels.
  tiley = 256  # size of tile in pixels.
  lat1,lon1 = tilexy2latlon(x-1,y-1,z)
  lat2,lon2 = tilexy2latlon(x+2,y+2,z)

  xfrac = (lon-lon1) / (lon2 - lon1)
  yfrac = (lat-lat2) / (lat1 - lat2)

  xpx = int(3 * tilex * xfrac)
  ypx = int(3 * tiley * yfrac)

  print("getPixelCoords(%f,%f,%d,%d,%d)" % (lat,lon,x,y,z))
  print("tile bounds: (%f,%f), (%f,%f)" % (lat1,lon1,lat2,lon2))
  print("  xfrac,yfrac = %f, %f" % (xfrac,yfrac))
  print("  xpx,ypx = %d, %d" % (xpx,ypx))

  return (xpx,ypx)


def getFarmImg(seriesStr,osgb_n,osgb_e,imSize):
  """ Returns an opencv compatible image of the object at osgb coordinates
  osgb_n, osgb_e, giving an image of size imSize pixels square about the point.
  """
  z = 16
  lon,lat = osgb2latlon(osgb_n, osgb_e)
  x,y = latlon2tilexy(lat, lon, z)
  img = getCompositeImg(seriesStr,x,y,z)

  xpx,ypx = getPixelCoords(lat,lon,x,y,z)

  print(xpx,ypx)
  cv2.imwrite("img_comp.png",img)
  
  img_cropped = img[(ypx-imSize):(ypx+imSize), (xpx-imSize):(xpx+imSize)]
  return img_cropped


    
zoom = 16
lon,lat = osgb2latlon(447222.0 , 534550.0)
print lon,lat
print("https://www.openstreetmap.org/?mlat=%f&mlon=%f#map=17/%f/%f" % (lat,lon,lat,lon))

x,y = latlon2tilexy(lat,lon, zoom)

print("http://c.tile.openstreetmap.org/%d/%d/%d.png" % (zoom,x,y))
print("https://geo.nls.uk/mapdata3/os/6inchfirst/%d/%d/%d.png" % (zoom,x,y))
print("https://nls-3.tileserver.com/fpsUZbc4ftb2/%d/%d/%d.jpg" % (zoom,x,y))
print("https://nls-3.tileserver.com/fpsUZbULUtp1/%d/%d/%d.jpg" % (zoom,x,y))

print(getTileUrl("OS_6in_1st",x,y,zoom))

#imgData =  getImg("OS_6in_1st",x,y,zoom)

#openImg("OS_6in_1st",x,y,zoom)

osgb_n = 447222.0
osgb_e = 534550.0
imSize = 50
seriesStr = "OS_6in_1st"
img = getFarmImg(seriesStr,osgb_n,osgb_e,imSize)
cv2.imwrite("img.png",img)
