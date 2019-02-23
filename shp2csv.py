#!/usr/bin/python

import shapefile
fname = "VMD/OS OpenMap Local (ESRI Shape File) NZ/data/NZ_NamedPlace.shp"
sf = shapefile.Reader(fname)

#print("Number of Shapes Imported: ",len(sf.shapes()))

#for f in sf.fields:
#    print f

print("# Data From %s" % fname)
print("uname, ID, DISTNAME, osgb_n, osgb_e")
recs = sf.records()
shapes = sf.shapes()
for ir in range(0,len(recs)):
    r = recs[ir]
    if "FARM" in r['DISTNAME'].upper():
        uname = r['DISTNAME'].replace(" ","_") + "_" + r['ID'][-5:]
        print uname,", ",r['ID'],",",r['DISTNAME'],",",shapes[ir].points[0][0],",",shapes[ir].points[0][1]

#for f in sf.fields:
#    print f




    
