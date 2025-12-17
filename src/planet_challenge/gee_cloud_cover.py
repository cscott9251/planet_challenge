from gee_init import gee_init
import ee

gee_init()

s2Sr = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') 
s2Clouds = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')

START_DATE = ee.Date('2022-10-04')
END_DATE = ee.Date('2022-10-10')

MAX_CLOUD_PROBABILITY = 100

#region = ee.Geometry.Rectangle({coords: [-76.5, 2.0, -74, 4.0], geodesic: false})