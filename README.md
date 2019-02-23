Graham's Farm Project Code
==========================

Approach
========
Extract a list of current farms from OS Opendata Vector Map District

Use the NLS 6inch OS maps to extract an image of the current farms in the 
original OS maps.

Use the images to train a neural network to scan the images for other farms.



Useful Info
===========

6inch tiles URL
var sixinch2 = new ol.layer.Group({
  	extent: ol.proj.transformExtent([-8.8, 49.8, 1.8, 60.9], 'EPSG:4326', 'EPSG:3857'),
        preload: Infinity,
	title: "Great Britain - OS Six Inch, 1888-1913", 	
		layers: [ sixinch2scot_api, sixinch_damerham ],
				minZoom: 1,
				maxZoom: 17,

        group_no: '36',
        mosaic_id: '6',
        typename: 'nls:Six_Inch_GB_WFS',
        type: 'overlay', 
        visible: false,
	keytext: 'View the individual sheets of this OS six-inch mapping by selecting "Find by place" above',
        key: 'geo.nls.uk/mapdata3/os/6inchfirst/key/openlayers.html',
        attribution: '',
        tileOptions: {crossOriginKeyword: null},      
        minx: -8.8, 
	miny: 49.8,
        maxx: 1.8, 
        maxy: 60.9
    });

var oneinchseventh = new ol.layer.Tile({
  	extent: ol.proj.transformExtent([-8.8, 49.8, 1.8, 60.9], 'EPSG:4326', 'EPSG:3857'),
        preload: Infinity,
	title: "Great Britain - OS One Inch 7th series, 1955-61",
	source: new ol.source.XYZ({
		          urls:[
		            'https://nls-0.tileserver.com/fpsUZbc4ftb2/{z}/{x}/{y}.jpg',
		            'https://nls-1.tileserver.com/fpsUZbc4ftb2/{z}/{x}/{y}.jpg',
		            'https://nls-2.tileserver.com/fpsUZbc4ftb2/{z}/{x}/{y}.jpg',
		            'https://nls-3.tileserver.com/fpsUZbc4ftb2/{z}/{x}/{y}.jpg'
		          ],
		          minZoom: 1,
		          maxZoom: 15,
		          tilePixelRatio: 1
		        }),
        group_no: '55',
        mosaic_id: '11',
        typename: 'nls:catalog_one_inch_7th_series',
        type: 'overlay', 
        visible: false,
        minx: -8.8, 
	miny: 49.8,
        maxx: 1.77, 
        maxy: 60.9,
	keytext: 'View the individual sheets of this OS one-inch mapping by selecting "Find by place" above',
        key: 'geo.nls.uk/mapdata2/os/seventh/key/openlayers.html'
    });
	
