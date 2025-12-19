import pandas as pd
import geopandas as gpd
#import numpy as np
#from scipy.spatial.distance import cdist
from sqlalchemy import create_engine
from geopy.distance import geodesic

from pathlib import Path 
from datetime import datetime, timedelta
#import time
#from collections import defaultdict

from planet_challenge.weather_api_clouds import cloud_covers_pipeline


"""
This module takes the final cloud covers dataframe from weather_api_clouds.py and 
searches for the best cities to image per day in two ways, sequentially:

1. By cloud cover, by using the free Open Meteo weather API to retrieve cloud covers for
all of the cities, and then finding the 8 smallest values for cloud cover per day in ascending order per day.
Cloud covers dataframe and pipeline from weather_api_clouds.py.

2. By geodesic proximity. Assuming the satellite moves from east to west, the easternmost city of the 8 cities
given by the first step is selected as the starting city, and then the nearest city (in terms of geodesic distance)
is selected as the next city to image, and so on until a route of 8 cities that are in consecutive geographical order
(i.e. are more or less in a line in terms of their longitude, obviously with variation in latitude) is reached. 
This is then repeated for the remaining 6 days until a full list of ordered cities is reached.

The differet tasks are organised into functions with params, which are themselves chained via a main pipeline function for readability.

The final dataframe is exported to CSV, to GeoJSON, as well as to my Postgres database on GCP (which I had already deployed for my UHI project).
This was for the visualisation, testing different time periods for the cloud covers etc. I wanted to make sure that it was possible to quickly
update my Map Series Atlas in QGIS with updated points for different time periods with minimal manual input. I connected my GCP Postgres database
to QGIS, so that when I re-run the program, I just have to quickly refresh the Atlas in QGIS and the series and dynamic text elements will simply
reference the new points. This saved having to manually import GeoJSON files etc. 


Things to note:

I've left some old, commented-out code instead of deleting it to show you my thought process. 

I went through 2-3 different methods for performing the ordering, using different distance calculation methods / libraries etc.
When I looked at the points in QGIS I realised that using a simple nearest-neighbour calculation (SciPy CDist or Shapely nearest()) 
was resulting in imaging route switching direction, i.e. going towards east for a few locations and then selecting a location that was actually back west 
(becasue that locationed happened to be nearest in terms of absolute distance).
I realised that this was because the loop was simply selecting the nearest point with no accounting for direction or starting position. 
So I changed the logic to specify a starting position and to use the geopy package to calculate the next nearest geodesic (instead of 2D) distance.
Since the original Shapefile data was in EPSG:4326, which uses degrees as a unit, geodesic calculation is straightforward. 

I wanted to use earthengine-api Python library to utilise Google Earth Engine Python functions, but I didn't have time to implement this, and I am relatively
new to that Python library and to the API, how to find cloud covers for different AOIs, etc. 
I have used GEE before, for my UHI project, to find matching summer/winter pairs of Landsat-2 and Sentinel-2 images,
but my code on the GEE code editor, in JavaScript, didn't seem readily adaptable to this problem, and I felt more confident to start from scratch. 
I would definitely like to implement this in the future!
"""


def identify_opportunities(cloud_df, start_date, window):

    date1 = datetime.strptime(start_date, "%Y-%m-%d")

    #print(date1)
    #date1 = date1.strftime("%Y-%m-%d")

    end_date = date1 + timedelta(days=window-1)
    date1 = date1.strftime("%Y-%m-%d")
    end_date = end_date.strftime("%Y-%m-%d")


    print(f"Determining 8.No cities to image between {start_date} and {end_date}...")

    #timespan = 7 #days

    #start_date = '2022-10-04'
    date1 = datetime.strptime(start_date, "%Y-%m-%d")
    #print(date1)
    #date1 = date1.strftime("%Y-%m-%d")

    #end_date = '2022-10-10'
    #date2 = date1 + timedelta(days=window-1)

    #opportunities_list = []

    # opportunities_dict = defaultdict(list)
    # opportunities_dict_geom = defaultdict(list)        ## XXX Found this library when I was searching for ways to use a dictionary whose keys are not known yet in a loop
    # opportunities_dict_cloud = defaultdict(list)       ## This is because in the foor loop below, I wanted to update / append a new Dataframe in every iteration with the 8 cities corresponding to the 
    #                                                     ## 8 smallest values for cloud cover, but Dataframes and GeoDataframes do not have a reliable append method (the opinion of a few people on StackExchange)
                                                        ## So I had the idea to store the values in a dictionary, adding a new key in each iteration corresponding to the date, creating the keys on the fly.

                                                        ## I thought it would save time / typing, but this method of creating a separate dictionary for each label locked me into having to create separate dataframes for each label
                                                        ## and having to implement annoying, convoluted logic to stack() each dataframe into a columnar shape, and then explicitly combining all of the 
                                                        # stacked GeoDataframes into a single GeoDataframe, manually defining the columns by referencing the stacked GeoDataframes etc.
                                                        # This was very onerous, so I decided to just create a dictionary with the labels as keys and values as lists 
    ## Loop through each date in the time window


    opportunities_dict = {                    ## Decided to use a dedicated dictionary and initialise it myself, since it makes things simpler
        'date':[],
        'city':[],
        'geometry':[],
        'cloud_cover':[],
        'pop_max':[],
        'row_order':[],                       ## Need something to store row order, as I learned from GeoPandas-exported GeoJSONS not being read by QGIS. See XXX Comments in opportunities_pipeline()
    }


    for i in range(window):         ## Loop through each day

        date_i = date1 + timedelta(days=i)
        print(f"...{date_i}...")
        indexlist = list(cloud_df[date_i].nsmallest(8).index) ## Select the indexes corresponding to the 8 lowest values of cloud cover.
        print(cloud_df[date_i].nsmallest(8))

        for list_idx, city_idx in enumerate(indexlist):         ## Loop through rows corresponding to the 8 smallest cloud cover values 

            city = cloud_df.at[city_idx, 'city_name'] 
            # print(city)
            exists = any(city in lst for lst in opportunities_dict.values())  # Was searching for a way to loop through a dictionary which had lists as its values
                                                                                # and found this fancy, if a little unreadable method, which takes the current city,
                                                                                # and searches for it within the dictionary to see if it exists. If it exists, the any()
                                                                                # builtin method returns True 
            
            if exists:

                print(f"{city} exists! Skipping city")  # Wanted to add logic to skip the city if it had already been imaged, but different clients have different requirements
                                                        # Some clients need continuous imaging for time-series data, others require single images  
                #continue                               # For the logic to work, the n value in cloud_df[date_i].nsmallest(n).index would need to be increased by the same number of cities that were already imaged at previous dates
                                                        # So if, on x date, y number of cities had already been imaged, then we would do cloud_df[date_i].nsmallest(n+y).index, and then remove the rows corresponding to the indexes of the 
                                                        # already imaged cities, so that all 8 opportunities could be used. 

            # opportunities_dict[date_i].append(str(cloud_df.at[city_idx, 'city_name']))  ### XXX There are some occurrences of cities with very low cloud forecasts during a certain time of year being selected for multiple dates
            # opportunities_dict_geom[date_i].append(cloud_df.at[city_idx, 'geometry'])   ### XXX This creates a lot of duplicates. Possible idea - add logic to check if city has already been imaged
            # opportunities_dict_cloud[date_i].append(cloud_df.at[city_idx, date_i])      ### XXX There is probably a faster way to do this other than splitting up the columns like this, but I didn't want to rewrite my code too much!
            
            opportunities_dict['date'].append(date_i)
            opportunities_dict['city'].append(str(cloud_df.at[city_idx, 'city_name']))      ## Still have to manually append (or can implement a loop through the dict keys)
            opportunities_dict['geometry'].append(cloud_df.at[city_idx, 'geometry'])        ## but at least we don't have to manually stack() with multiple GeoDataframes
            opportunities_dict['cloud_cover'].append(cloud_df.at[city_idx, date_i])         ## and can keep all columns labels in one GeoDataframe
            opportunities_dict['pop_max'].append(cloud_df.at[city_idx, 'pop_max'])
            opportunities_dict['row_order'].append(list_idx)                        ## This is needed to record the order of imaging. Dictionaries do not natively respect order / indexes like Dataframes
                                                                                    ## There might be a better way to do this
    
    opprtunities_gdf_full = gpd.GeoDataFrame(opportunities_dict, crs="EPSG:4326")  # Can keep to using one GeoDataframe instead of one for each field(!). Ensure that originale Shapefile CRS is specified.
    #opprtunities_gdf_full = opprtunities_gdf_full.to_crs("EPSG:3857")               # And specify QGIS CRS. The reason I'm using 3857 is because the unit of 4326 is degrees, which was making things difficult in QGIS.
                                                                                     # Make the reprojection to 3857 in the opportunities_pipeline below
                                                                                     # However, it's good to keep it in EPSG:4326 prior to exporting, because we can then calculate geodesic distance
    # opportunities_df = gpd.GeoDataFrame.from_dict(opportunities_dict)
    # opportunities_df_geom = gpd.GeoDataFrame.from_dict(opportunities_dict_geom)
    # opportunities_df_cloud  = gpd.GeoDataFrame.from_dict(opportunities_dict_cloud)  ## Realised that the final exports didn't include the cloud percentage, so this is a quick way of adding it back in

    print("Cities selected.")

    print(opprtunities_gdf_full)

    return opprtunities_gdf_full        ## With the previous defaultdict / stack() method, a separate gdf has to be defined for each label, which necessitated
                                        ## a separate gdf to be returned, which made the number of params / returs a bit convoluted. So changed the method to one 
                                        ## that allowed a single object to be returned

    # for i in range(timespan):
        
    #     date_i = date1 + timedelta(days=i)
    #     print(opportunities_df_geom[date_i])
    #     #print(opportunities_df_geom.iloc[i])


def order_nearest(opportunities_gdf_full):

    print("Ordering imaging schedule based on geographic locations...")


    # cities_sorted = gpd.GeoDataFrame(index=cities_df.index)
    # geoms_sorted = gpd.GeoDataFrame(index=geoms_df.index)
    # clouds_sorted = gpd.GeoDataFrame(index=cloud_df.index) ## Again, from the previous method of using stack(), had to include too many params and then tied me into manually sorting them

    ordered_rows = []
    previous_end_idx = None  ## Thought it was a good idea to try to set the start location of each day as equal to the end location of the previous day
                             ## But for simplicity, assume the satellite begins and ends at the same position each day, since I don't have any information on orbital speeds etc.

    for date, group in opportunities_gdf_full.groupby('date'):

        print(f"...{date}...")

        start_idx = group.geometry.x.idxmax() ## Start at the easternmost side the group. 
    
        unvisited = set(group.index)  ## Creates a set of all of the indexes for the group, following the same logic as the exists logic above 
        route = [start_idx]           ## The imaging route list, starting with the starting index
        unvisited.remove(start_idx)   ## Since the start idx is already in the order list, remove it from the unvisited set.
        
        # geoms_col = geoms_df[date]  ## Gives a Series representing the column of point geometries of given date
        #geoms = group.geometry.reset_index(drop=True) ## Reset_index ensures geometries stat aligned with row_order in each iteration


        #n=len(geoms) ## Get number of items in column 
        #unvisited = set(range(n)) ## Need some way to track which locations have been imaged and which haven't. List of city indexes for each iteration. 
        #order = [0] ## List to store 
        #unvisited.remove(0) ## Mark the starting city as already imaged by removing first item. 

        while unvisited:            ## The unvisited variable decreases with each loop until it is empty, at which point the while condition will be false and the loop will end 

            current_idx = route[-1]   ## Get the latest location in the route (last/end index in the route list) so that its geom / coords can be extracted
            current_point = group.loc[current_idx].geometry  ## Get the current point geometry from the current index
            current_coords = (current_point.y, current_point.x)  ## Getting the lat / long for geodesic distance calculation

            distances = {}      # Initialise the dictionary which will contain the distances from the current point to all other points for that date / day
                                # with the keys as the indexes of those points, the the values as the actual distances

            ## Loop through each city in the unvisited set, calculate the geodesic distances from the current point and all other points in the group 

            for idx in unvisited:
                next_point = group.loc[idx].geometry  ## Extract geom of current idx in the unvisited set
                next_coords = (next_point.y, next_point.x)  # Extract Lat / long

                distance = geodesic(current_coords, next_coords).kilometers   ## Calculate GEODESIC distance using geopy instead of the previous nearest neighbour / Euclidean 2D methods
                distances[idx] = distance   ## Add distance to distance between current (unvisited) pont and next point dictionary, creating a new key containing the index

            nearest_idx = min(distances, key=distances.get)  ## After looping through unvisited, calculate the minimum geodesic distance from current point and unvisited points
                                                             ## to find the next point

            route.append(nearest_idx)                  ## Add it to the route
            unvisited.remove(nearest_idx)           ## Remove it from the unvisited list

        
        ordered_group = group.loc[route].copy()    ## Take the current group and order it by the idexes in route, and copy to a new group object
        ordered_group['row_order'] = range(len(ordered_group))  ## To preserve daily order
        ordered_rows.append(ordered_group)


        print("Ordering complete.")
    
        ordered_df = pd.concat(ordered_rows, ignore_index=True)  ## Make a dataframe from the ordered rows 

    return ordered_df

            #current_coords = coords[current]
            # current = order[-1] ## Get index of most recently added city to the ordered cities list
            # current_point = geoms.iloc[current]

            # distances = {
            #     idx: current_point.distance(geoms.iloc[idx])        ## Creates a dictionary using for loop comprehension of distances from the current point to all other unvisited points
            #     for idx in unvisited                                    ## Using Shapely
            # }

            # nearest_idx = min(distances, key=distances.get)     ## Finds the index of the closest unvisited point to the current point
            # #nearest = min(distances, key=distances.get)
            # order.append(nearest_idx) ## Adds the index of the nearest city to the order list
            # unvisited.remove(nearest_idx) ## Removes the index of the current city from the unvisited variable 
            # #current = nearest

            # dists = cdist([coords[current]], coords[unvisited_list := list(unvisited)])[0] ## Calculate distances from current city to ALL unvisited cities, using cdist from SciPy
            # nearest_idx = unvisited_list[np.argmin(dists)]                                  ## coords[current] returns coords of current city
            #                                                                                 ## coords[unvisited_list := list(unvisited)] returns coords of all unvisited cities 
            # distances = {                                                                 ## nearest_idx finds the minimum of the distances between current city and unvisited
            #     idx: np.sqrt(                                                             ## Could also use Shapely
            #         (coords[idx][0] - current_coords[0])**2 +          # Euclidean distance 
            #                  (coords[idx][1] - current_coords[1])**2
            #     )
            #     for idx in unvisited

            # }
            

        # cities_sorted[date] = cities_df[date].values[order]  ## After the while loop is finished and we have a completed order list, sort the current date column by the values in the order list. For loop then continues 
        # geoms_sorted[date] = geoms_df[date].values[order]  ## Same for geoms.
        # clouds_sorted[date] = cloud_df[date].values[order] ## Same for clouds

            



def opportunities_pipeline(start_date, window):

    result_dir = Path('./result')
    result_dir.mkdir(parents=True, exist_ok=True)
     
    cloud_df = cloud_covers_pipeline(start_date, window)

    print(cloud_df)

    opportunities_gdf = identify_opportunities(cloud_df, start_date, window)
    opportunities_gdf = opportunities_gdf 

    print(opportunities_gdf)

    opportunities_gdf_ordered = order_nearest(opportunities_gdf)
    opportunities_gdf_ordered['date'] = pd.to_datetime(opportunities_gdf_ordered['date']).dt.date

    print(opportunities_gdf_ordered)

    opportunities_gdf_ordered.to_file(result_dir / 'ordered_points_with_cities.geojson', driver="GeoJSON")
    opportunities_gdf_ordered.to_csv(result_dir / 'result/ordered_points_with_cities.csv')

    
    connection_string = f"postgresql://${PGUSER}:${PGPASS}@${VM_IP}:5432/coburg_uhi" ## Redacted in line with security best practices
    engine = create_engine(connection_string)

    opportunities_gdf_ordered.to_postgis(       ### XXX Upload GeoDataframe directly as a new table to my previously deployed Postgres with PostGIS database
    'planet_challenge',                         ### XXX Which I deployed as Docker image using a custom image I found online (https://github.com/kartoza/docker-postgis/blob/develop/docker-compose.yml)
    engine,                                     ### XXX I used deployment scripts to push to Artifact Registry, tie to Compute Engine, create a VM, run the Docker image (starting the Postgres server) add firewall rules, and connect with CARTO
    if_exists='replace',                        ### XXX My CARTO trial has now unfortunately expired, so I cannot use it for visualisation 
    index=False
    )                                           ### XXX I originally deployed this for my UHI project for the CARTO connection (mapping hot spots and cold spots), I'm just reusing it here for convenience. This is why it's called "coburg_uhi"
                                                ### XXX I thought it would be useful to have as a persistent database so that minimal work would have to be done to generate another Map Series / Atlas in QGIS (since the data should already be linked)




    for date, group in opportunities_gdf_ordered.groupby('date'):

        date = date.strftime("%Y-%m-%d")
        group.to_file(result_dir / f'{date}.geojson', driver="GeoJSON")

        


        


    #geoms_reordered.to_file('./result/geoms_reordered.geojson', driver="GeoJSON") ## To compare 
#
    #test = gpd.GeoDataFrame(cities_reordered)
    #test.to_file('./result/cities_reordered.geojson', driver="GeoJSON")

    #filepath = Path('../result/daily_imaging_locations_geoms.gpkg')
    #geoms_reordered.to_file(filepath, driver="GPKG")

    ## Output to format readable by QGIS

    # geoms_stacked = geoms_reordered.stack().reset_index()   ## XXX Tried to export the _reordered dataframes directly to GeoJSON, but QGIS could not read it as a layer
    # cities_stacked = cities_reordered.stack().reset_index() ## This was due to the fact that _reordered dataframes had dates as column headers (it was transposed in the weather_api_clouds.py module), which violates GeoJSON spec
    # clouds_stacked = clouds_reordered.stack().reset_index() ## stacking the dataframe un-transposes them so that they're in column form before combining them into one geodataframe below
                                                            ## Since the dataframes all went through an identical transformation in the same order, alignment is preserved
    #cities_stacked = gpd.GeoDataFrame(cities_stacked)      ## reset_index() is needed because otherwise the dates are expressed as indexes, in addition to the index itself,
                                                            ## which creates a "Multiindex" which isn't compatible with GeoJSON
    #cities_stacked.to_csv("./result/cities_stacked.csv")    ## XXX This method has now been superseded, eliminating the need for .stack().reset_index() and separate dataframes.


    # Because we're resetting the indexes of the above, we need to check that everything is still aligned:
    # I just noticed the reset_index() and wondered if this would cause the rows of the different dataframes not to correspond to each other anymore!

    # print("Checking cities, geoms, and clouds dataframes spatial alignment and that rows match...")

    # time.sleep(2.5)

    # assert (cities_stacked['level_0'] == clouds_stacked['level_0']).all(), "Cities dataframe rows do not align with clouds dataframe rows!"
    # assert (cities_stacked['level_1'] == clouds_stacked['level_1']).all(), "Cities dataframe dates do not align with clouds dataframe dates!"
    # assert (geoms_stacked['level_0'] == clouds_stacked['level_0']).all(), "Geometry dataframe rows does not align to clouds dataframe rows!"

    # print("All dataframes are aligned, and rows match!")

    

   # time.sleep(2.5)



    # gdf_export = gpd.GeoDataFrame({
    #     'row order':cities_stacked['level_0'],      ## Combine stacked columns into a single GeoDataframe. Level0 stores the original row order before the stacking took place
    #     'date':cities_stacked['level_1'],           ## level_1 stores the original column names from before the stacking. See cities_stacked.csv for the structure. 
    #     'city':cities_stacked[0],
    #     'cloud_cover':clouds_stacked[0],
    #     'geometry':geoms_stacked[0]
    # },crs="EPSG:4326")

    # print(gdf_export.head())

    # gdf_export.to_file('./result/ordered_points_with_cities.geojson', driver='GeoJSON')


