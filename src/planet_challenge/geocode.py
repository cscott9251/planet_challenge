#from geopy.geocoders import GoogleV3
#from geopy.geocoders import GoogleV3
import googlemaps

import time
import geopandas as gpd


from shapely.geometry import (Point)


"""

This module loads the Shapefile from the URL given in the challenge brief into a GeoDataframe.
It sorts the values by population, selects the 40 cities with the greatest populations,
orders the GeoDataframe by the populations, and deletes the remaining cities.

I originally included logic to use Google's Maps and Geocoding APIs to pass the names of the cities 
to the API so get the lat/long, but then realised that these points are already part of the geometry 
column of the Shapefile. 

"""



#gee_init()

# CONSTRAINTS
# 7 days to image the 40 most populous cities 
# Sensor can image 8 images per day

# OBJECTIVE
# Select best day to image each city (based on minimum cloud cover )


# Originally I wanted to use my Google Cloud account and the Google Earth Engine, and to write logic 
# to pass the city names in the city/population dataset to the Google Geocoding API via some loop, which would then return their decimal
# lat / long centre points (using geopy), which could then in turn natively be passed to the Google Earth Engine API (using earthengine-api),
# which, finally, would return cloud cover percentages for some 7-day window. 

# However, using both geopy with the Google Geocoding API, and using earthengine-api with the Google Earth Engine API requires I use my 
# personal API key(s), client_id, and secret_key (or at the very least my API key), and it also requires the end-user to authenticate their 
# terminal / machine with my Google Cloud project / billing acount in order to initialise / instantiate the earthengine-api object constructor 
# via ee.Authenticate() and ee.Initialize(project='XXX').

# This would require that I set up one of you as 

# The earthengine-api is a very powerful Python library, and I know that Planet must use it in its codebase, since it has a collaboration with GEE.
# 




# geolocator2 = GoogleV3(api_key="<XXX>")

#location = geolocator.geocode("Berlin")


# geolocator = GoogleV3(api_key="<XXX>",
#                     client_id="<XXX>", 
#                     secret_key="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")
    







################### FOR CLOUD COVER TRY OPEN METEO API


############# CAN USE GOOGLE WEATHER API FOR CLOUD COVER IN THE FUTURE OR OPEN-METEO FOR BOTH FORECAST AND HISTORICAL


#pd.set_option('display.max_columns',None)

url = r"https://naciscdn.org/naturalearth/10m/cultural/ne_10m_populated_places_simple.zip"

def load_top_40_cities(data_source_url):

    """
    This function loads the top 40 most populous cities from a zipped shapefile.
    Currently, this only works with a hosted zipped shapefile downloadable via a public URL.
    The function could of course be expanded to handle different formats, sources etc.

    """

    print("Loading cities population Shapefile from URL to Geodataframe...")

    gdf = gpd.read_file(filename=url)

    gdf = gdf.sort_values('pop_max', ascending=False)

    gdf = gdf.drop(gdf.columns.difference(['nameascii','sov0name','adm0name','pop_max','geometry']),axis=1)


    # print(gdf.head())
    # print(gdf.info())

    gdf = gdf.nlargest(40,"pop_max")

    namedict = {
        'sov0name':'country',
        'nameascii':'city_name'
    }

    gdf = gdf.rename(mapper=namedict,axis=1)

    gdf = gdf.reset_index(drop=True)

    #print(gdf.head())

    return gdf




# gdf = load_top_40_cities(url)

# print(gdf)

#geocode_cities(gdf)
    


def geocoded_cities_pipeline():

    print("Loading cities population Shapefile from URL to Geodataframe...") 

    time.sleep(2.5)   

    gdf = load_top_40_cities(url)

    #gdf_geocoded = geocode_cities(gdf) ## No need to geocode or because the GEOMETRY column of the Geodataframe already contains the lat/long 

    return gdf





### XXX Below are functions that are no longer needed XXX

### I originally wanted to use Google's Geocoding API to get the long / lat of the cities by passing their name, but I then realised the coords were already in the Point Geometries

def extract_coords(cities_gdf):


    gmaps = googlemaps.Client(key="AIzaSyCpw_ThiNdXC9hFiSt0HeP7CMrIdzoY0II")

    for idx in cities_gdf.index:

        geom = cities_gdf.at[idx, 'geometry']

        #print(geom.x)

        p = Point(geom)

        #print(p)

        cities_gdf.at[idx, 'long'] = geom.x
        
        cities_gdf.at[idx, 'lat'] = geom.y


    return cities_gdf



        

# gdf = geocoded_cities_pipeline()
# print(gdf)

# gdf = extract_coords(gdf)



# print(gdf_geocoded.head())
# print(gdf_geocoded.info())
# print(gdf_geocoded)


# gmaps = googlemaps.Client(key="<XXX>")

# geolocator = gmaps.geocode('Coburg, Germany')

# coords = list(geolocator[0]['geometry']['location'].values())


################### FOR CLOUD COVER TRY OPEN METEO API


############# CAN USE GOOGLE WEATHER API FOR CLOUD COVER IN THE FUTURE OR OPEN-METEO FOR BOTH FORECAST AND HISTORICAL


# cloudcover = "https://pastebin.com/raw/yxhrQ2D5"






