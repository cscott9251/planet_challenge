from gee_init import gee_init
import ee

gee_init()

s2Sr = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED') 
s2Clouds = ee.ImageCollection('COPERNICUS/S2_CLOUD_PROBABILITY')