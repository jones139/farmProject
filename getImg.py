#!/usr/bin/python

import math
import pyproj
import urllib2
import os
import ntpath
import cv2
import skimage
import skimage.io
import numpy as np
import time
import random
import json
from selenium import webdriver

#  Hart Mill Farm , 447222.0 , 534550.0
# 027C806B-3BF0-4D10-B55A-B77337313780 , Hart Mill Farm , 447222.0 , 534550.0
# From https://wiki.openstreetmap.org/wiki/Slippy_map_tilenames#Lon..2Flat._to_tile_numbers_2

IMG_EXTRACT_SIZE = 50  # pixels
CACHEDIR = "/home/graham/Farms/TileCache"


# Google info from https://geogeek.xyz/how-to-add-google-maps-layers-in-qgis-3.html
tileSeries = {
  "OS_6in_1st" : {
    "url": "https://nls-3.tileserver.com/fpsUZbULUtp1/{0}/{1}/{2}.jpg",
    "dates" : "???"
  },
  "OS_1in_7th" : {
    "url": "https://nls-3.tileserver.com/fpsUZbc4ftb2/{0}/{1}/{2}.jpg",
    "dates" : "1955-1961"
  },
  "OS_10k" : {
    "url": "https://geo.nls.uk/mapdata3/os/10knationalgrid/{0}/{1}/{2}.png",
    "dates": "1950-1967"
  },
  "OS_10k_1900" : {
    "url": "https://nls-3.tileserver.com/fpsUZbqQLWLT/{0}/{1}/{2}.jpg",
    "dates": "1900s"
  },
  "OS_25k" : {
    "url": "https://nls-3.tileserver.com/fpsUZbIoj0Oa/{0}/{1}/{2}.jpg",
    "dates": "1937-1961"
  },
  "OSM" : {
    "url": "http://c.tile.openstreetmap.org/{0}/{1}/{2}.png",
    "dates" : "Current"
  },
  "Google" : {
    "url": "https://www.google.com/maps/@?api=1&map_action=map" \
                                            "&center={1},{2}" \
                                            "&zoom={0}" \
                                            "&basemap=map",
    "dates" : "Current"
  },
  "Google-Satellite" : {
    "url": "https://www.google.com/maps/@?api=1&map_action=map" \
                                            "&center={1},{2}" \
                                            "&zoom={0}" \
                                            "&basemap=satellite",
    "dates" : "Current"
  },
}




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

def latlon2osgb(lat,lon):
    osgb = pyproj.Proj(init='epsg:27700')
    wgs84 = pyproj.Proj(init='epsg:4326')
    osgb_n,osgb_e= pyproj.transform(wgs84,osgb,lat,lon);
    return (osgb_n,osgb_e)


  
def getTileUrl(seriesStr,x,y,z):
  if (seriesStr in tileSeries):
    #url = tileSeries[seriesStr]['url'] % (z, x, y)
    url = tileSeries[seriesStr]['url'].format(z, x, y)
  else:
    print("Unrecognised Series %s." % seriesStr)
    url = "error"

  return url


def getTileFname(seriesStr,x,y,z):
  """ Returns the cache filename of the specified map tile """
  fname = os.path.join(CACHEDIR,seriesStr,str(z),str(x),"%d.png" % y)
  return fname
        

def getGoogleApiKey():
  KEY_FNAME = "GoogleAPI.key"
  fpath = os.path.join(
        os.path.dirname(os.path.realpath(__file__)),
        KEY_FNAME)
  f = open(fpath,"r")
  apiKey = f.readline()
  f.close()
  print("apiKey=%s." % apiKey)
  return apiKey



def getGoogleUrl(seriesStr,lon,lat,zoom):
  if (seriesStr in tileSeries):
    url = tileSeries[seriesStr]['url'].format(zoom, lat,lon)
  else:
    print("Unrecognised Series %s." % seriesStr)
    url = "error"

  return url


def getAddress(lat,lon):
  """Use the Google reverse geocoding service to get the address
  of the specified point."""
  key = getGoogleApiKey()
  url = "https://maps.googleapis.com/maps/api/geocode/json?latlng={0},{1}&key={2}"
  url = url.format(lat,lon,key)
  #print(url)
  response = urllib2.urlopen(url)
  responseStr = response.read()
  responseObj = json.loads(responseStr)
  #print(responseObj)
  addrStr = responseObj['results'][0]['formatted_address']
  parishStr = responseObj['results'][0]['address_components'][2]['long_name']
  return addrStr,parishStr

def openImg(seriesStr,x,y,z):
  downloadTile(seriesStr,x,y,z)

def downloadTile(seriesStr,x,y,z):
  """ Returns an opencv compatible image of the tile of the given
  map series at mercator coordinates x,y and zoom level z.
  """
  url = getTileUrl(seriesStr,x,y,z)
  #print("downloadTile() - url=%s" % url);
  try:
    img_in = skimage.io.imread(url)
    if (len(img_in.shape)<3):
      img = cv2.cvtColor(img_in,cv2.COLOR_GRAY2RGB)
    else:
      img = cv2.cvtColor(img_in,cv2.COLOR_BGR2RGB)
    #cv2.imshow("original",imgRGB)
    #cv2.imshow("corrected",img)
    #cv2.waitKey(0)
  except:
    img = None
  return img


def getTile(seriesStr,x,y,z):
  """ Checks the local cache for the tile.  If it exists, the chached
  version is returned.  If it is not, it is downloaded and added to the 
  cache, then the cached version is returned.
  """
  fpath = getTileFname(seriesStr,x,y,z)
  if (not os.path.exists(fpath)):
    path,fname = ntpath.split(fpath)
    if (not os.path.exists(path)):
      os.makedirs(path)

    delaySec = 1.0 * random.random()
    print("getTile - downloading tile %s into cache, after delay %f"
          % (fpath,delaySec))
    time.sleep(delaySec)
    img = downloadTile(seriesStr,x,y,z)
    if (img is not None):
      cv2.imwrite(fpath,img)
    else:
      print("ERROR Downloading Tile %s" % fpath)
  else:
    #print("getTile - using cached version of tile from %s" % fpath)
    img = cv2.imread(fpath,cv2.IMREAD_UNCHANGED)

  return img


def getCompositeImgRange(seriesStr,x1,y1,x2,y2,z):
  """ Returns a composite image of all the tiles in the range x1-x2,y1-y2
  """
  colArr = [] # array of rows of images
  for j in range(y1,y2):
    #print("******ROW***** j=%d" % j)
    rowArr = []  # horizontal array of images
    for i in range(x1,x2):
      #print(i)
      rowArr.append(getTile(seriesStr, i,j, z))
    colArr.append(np.hstack(rowArr))
  img = np.vstack(colArr)
  return(img)

def getCompositeImg(seriesStr,x,y,z):
  """ Returns a composite image of 9 tiles in a 3x3 matrix, centred
  on x,y at zoom level z.
  """
  # Get the 9 images to make up the array.
  img11 = getTile(seriesStr, x-1, y-1, z)
  img12 = getTile(seriesStr, x+0, y-1, z)
  img13 = getTile(seriesStr, x+1, y-1, z)
  img21 = getTile(seriesStr, x-1, y+0, z)
  img22 = getTile(seriesStr, x+0, y+0, z)
  img23 = getTile(seriesStr, x+1, y+0, z)
  img31 = getTile(seriesStr, x-1, y+1, z)
  img32 = getTile(seriesStr, x+0, y+1, z)
  img33 = getTile(seriesStr, x+1, y+1, z)

  try:
    row1 = np.hstack([img11, img12, img13])
    row2 = np.hstack([img21, img22, img23])
    row3 = np.hstack([img31, img32, img33])
    imgRGB = np.vstack([row1, row2, row3])
    #img = cv2.cvtColor(imgRGB,cv2.COLOR_BGR2RGB)
    img = imgRGB
  except:
    print("ERROR Creating composite image")
    img = None
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
  yfrac = (lat-lat1) / (lat2 - lat1)

  xpx = int(3 * tilex * xfrac)
  ypx = int(3 * tiley * yfrac)

  #print("getPixelCoords(%f,%f,%d,%d,%d)" % (lat,lon,x,y,z))
  #print("tile bounds: (%f,%f), (%f,%f)" % (lat1,lon1,lat2,lon2))
  #print("  xfrac,yfrac = %f, %f" % (xfrac,yfrac))
  #print("  xpx,ypx = %d, %d" % (xpx,ypx))

  return (xpx,ypx)


def getFarmImg(seriesStr,osgb_n,osgb_e,imSize):
  """ Returns an opencv compatible image of the object at osgb coordinates
  osgb_n, osgb_e, giving an image of size imSize pixels square about the point.
  """
  return getFarmImgOsgb(seriesStr,osgb_n,osgb_e,imSize)


def getFarmImgOsgb(seriesStr,osgb_n,osgb_e,imSize):
  """ Returns an opencv compatible image of the object at osgb coordinates
  osgb_n, osgb_e, giving an image of size imSize pixels square about the point.
  """
  lon,lat = osgb2latlon(osgb_n, osgb_e)
  return getFarmImgLatLon(seriesStr,lat,lon,imSize)

def getFarmImgLatLon(seriesStr,lat,lon,imSize):
  z = 16
  x,y = latlon2tilexy(lat, lon, z)

  if (seriesStr!="Google" and seriesStr!="Google-Satellite"):
    img = getCompositeImg(seriesStr,x,y,z)

    if (img is not None):
      xpx,ypx = getPixelCoords(lat,lon,x,y,z)
      img_cropped = img[(ypx-imSize):(ypx+imSize), (xpx-imSize):(xpx+imSize)]
      # Make a 'not farm' image of the area to the right of the farm image.
      img_notFarm = img[(ypx-imSize):(ypx+imSize), (xpx+imSize):(xpx+3*imSize)]
    else:
      img_cropped = None
      img_notFarm = None
  else:
    # Handle Google Maps, - open a browser and take a screen shot Based on
    # https://medium.com/@ronnyml/website-screenshot-generator-with-python-593d6ddb56cb
    webDriver = webdriver.Chrome('chromedriver')
    webDriver.get(getGoogleUrl(seriesStr,lon,lat,z))
    # Wait for the website to populate - it takes a while.
    time.sleep(10)
    tmpFname = '/tmp/google.png'
    webDriver.save_screenshot(tmpFname)
    img = cv2.imread(tmpFname,cv2.IMREAD_UNCHANGED)
    ypx = int(img.shape[0]/2)
    xpx = int(img.shape[1]/2)
    img_cropped = img[(ypx-imSize):(ypx+imSize), (xpx-imSize):(xpx+imSize)]
    img_notFarm = None
    #driver.quit()
    
  return img_cropped,img,img_notFarm

    
if (__name__ == "__main__"):
  zoom = 16
  osgb_n = 447222.0
  osgb_e = 534550.0
  lon = 0
  lat = 0
  print osgb_n,osgb_e, lon,lat
  lon,lat = osgb2latlon(osgb_n,osgb_e)
  print osgb_n,osgb_e, lon,lat
  osgb_n,osgb_e = latlon2osgb(lon,lat)
  print osgb_n,osgb_e, lon,lat
  lon,lat = osgb2latlon(osgb_n,osgb_e)
  print osgb_n,osgb_e, lon,lat
    #print("https://www.openstreetmap.org/?mlat=%f&mlon=%f#map=17/%f/%f" % (lat,lon,lat,lon))

  x,y = latlon2tilexy(lat,lon, zoom)

  #print("http://c.tile.openstreetmap.org/%d/%d/%d.png" % (zoom,x,y))
  #print("https://geo.nls.uk/mapdata3/os/6inchfirst/%d/%d/%d.png" % (zoom,x,y))
  #print("https://nls-3.tileserver.com/fpsUZbc4ftb2/%d/%d/%d.jpg" % (zoom,x,y))
  #print("https://nls-3.tileserver.com/fpsUZbULUtp1/%d/%d/%d.jpg" % (zoom,x,y))

  print(getTileUrl("Google",x,y,zoom))
  print(getTileUrl("OSM",x,y,zoom))
  print(getTileUrl("OS_6in_1st",x,y,zoom))


  #openImg("OS_6in_1st",x,y,zoom)

  osgb_n = 447222.0
  osgb_e = 534550.0
  imSize = 50
  seriesStr = "OS_6in_1st"
  img,img_big,notFarm = getFarmImg(seriesStr,osgb_n,osgb_e,imSize)
  cv2.imwrite("img.png",img)


  print(getAddress(54.53872,-1.41799))
