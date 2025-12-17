import openmeteo_requests

import time
from pathlib import Path 
import pandas as pd
import requests_cache
from retry_requests import retry
import datetime
from datetime import timedelta, datetime

from planet_challenge.geocode import geocoded_cities_pipeline



### 

# THIS COULD POSSIBLY BE DONE IN POSTGRESQL / SQL IN A POSTGRES DATABASE 
# FOUND A WAY TO DO IT IN PANDAS

# XXX ANOTHER POSSIBLE SOLUTION WAS PYTHON LIBRARIES THAT HANDLE TIME-SERIES DATA LIKE geopy, xarray, 
# XXX ANOTHER WAS USING ee (earthengine-api), but I've only used it to find all images within a certain date range for a single AOI, 
# XXX ANOTHER WAS TO USE rasterio WITH IMAGES FROM GOOGLE EARTH ENGINE 
# XXX I CHECKED THE RESULTS OF THIS API WITH THE CLOUD COVERS IN THE PASTEBIN LINK YOU PROVIDED AND THEY ARE ROUGHLY THE SAME, BUT DO ALSO DIFFERET SIGNIFICANTLY IN PLACES


### BRLOW LOGIC WAS LIFTED FROM OPEN-METEO API PAGE 
# https://open-meteo.com/en/docs/historical-weather-api?start_date=2022-10-04&end_date=2022-10-04&latitude=35.6895&longitude=139.6917&hourly=cloud_cover,cloud_cover_low,cloud_cover_mid,cloud_cover_high


def get_cloud_covers(cities_gdf, start_date, window):


	print("Querying Open Meteo historical weather API for ...")

	time.sleep(1.5)

	cache_session = requests_cache.CachedSession('.cache', expire_after = -1)
	retry_session = retry(cache_session, retries = 5, backoff_factor = 0.2)
	openmeteo = openmeteo_requests.Client(session = retry_session)

	# Make sure all required weather variables are listed here
	# The order of variables in hourly or daily is important to assign them correctly below
	url = "https://archive-api.open-meteo.com/v1/archive"

	#timespan = 7 #days

	#start_date = '2022-10-04'
	#start_date = datetime(start_date)
	date1 = datetime.strptime(start_date, "%Y-%m-%d")
	
	#print(date1)
	#date1 = date1.strftime("%Y-%m-%d")

	end_date = date1 + timedelta(days=window-1)
	date1 = date1.strftime("%Y-%m-%d")
	end_date = end_date.strftime("%Y-%m-%d")


	results_list = []

	for idx in cities_gdf.index:
		

		#print("idx")

		print(f"...{cities_gdf.at[idx, 'city_name']}...")
		time.sleep(0.1)

		geom = cities_gdf.at[idx, 'geometry']

		x_coord = geom.x

		y_coord = geom.y

		params = {

			"latitude": y_coord,    # y coord
			"longitude": x_coord,  # x coord
			"start_date": str(date1),
			"end_date": str(end_date),
			"hourly": ["cloud_cover"],
		}
		responses = openmeteo.weather_api(url, params=params)

		# Process first location. Add a for-loop for multiple locations or weather models
		response = responses[0]
		# print(f"Coordinates: {response.Latitude()}°N {response.Longitude()}°E")
		# print(f"Elevation: {response.Elevation()} m asl")
		# print(f"Timezone difference to GMT+0: {response.UtcOffsetSeconds()}s")

		# Process hourly data. The order of variables needs to be the same as requested.  ##### XXX Note that the .Daily endpoint of the open-meteo API does NOT return cloud_cover information
		hourly = response.Hourly()														  ##### XXX There is no way to get daily frequency cloud cover information natively from the API
																						  ##### XXX https://open-meteo.com/en/docs/historical-weather-api , see "Daily Parameter Definition"
		#print(hourly)
		hourly_cloud_cover = hourly.Variables(0).ValuesAsNumpy()
		#     hourly_cloud_cover_low = hourly.Variables(1).ValuesAsNumpy()
		#     hourly_cloud_cover_mid = hourly.Variables(2).ValuesAsNumpy()
		#     hourly_cloud_cover_high = hourly.Variables(3).ValuesAsNumpy()

		hourly_data = {"date": pd.date_range(
			start = pd.to_datetime(hourly.Time(), unit = "s", utc = True),
			end =  pd.to_datetime(hourly.TimeEnd(), unit = "s", utc = True),
			freq = pd.Timedelta(seconds = hourly.Interval()),
			inclusive = "left"
		)}

		hourly_data["cloud_cover"] = hourly_cloud_cover
		#     hourly_data["cloud_cover_low"] = hourly_cloud_cover_low
		#     hourly_data["cloud_cover_mid"] = hourly_cloud_cover_mid
		#     hourly_data["cloud_cover_high"] = hourly_cloud_cover_high

		hourly_dataframe_temp = pd.DataFrame(data = hourly_data)


		#print("\nHourly data\n", hourly_dataframe_temp)

		df_datetime_temp = hourly_dataframe_temp # Copy the dataframe to another variable just for safety
		df_cloud_temp = df_datetime_temp.set_index('date').resample(rule='24h').mean() # Set the index of the dataframe as the date column values, resample the index from hourly to daily, and calculate daily mean 
		df_cloud_temp = df_cloud_temp.reset_index() # Remove the date column as the index
		df_cloud_temp['date'] = pd.to_datetime(df_cloud_temp['date'].dt.strftime('%Y-%m-%d'))
		df_cloud_temp = df_cloud_temp.set_index(df_cloud_temp.columns[0]).transpose() # Transform the column of dates values to a row of date values (dates as column names / headers), whilst suppressing the top row being expressed as an index
		

		#   df_cities_temp = cities_gdf.head(idx +1)
		city_row = cities_gdf.loc[[idx]]

		#print(temp_df)

		df_merged_temp = pd.merge(city_row, df_cloud_temp, how="cross") ## Because there are no similar columns 
		results_list.append(df_merged_temp)

		#print(df_merged_temp)
		filepath = Path(f'./csv_check/{city_row["city_name"]}_cloud_cover.csv')
		filepath.parent.mkdir(parents=True, exist_ok=True)
		df_merged_temp.to_csv(filepath)

		print(df_merged_temp)

		#hourly_dict = hourly_dataframe.to_dict('index')
	

	final_df = pd.concat(results_list, ignore_index=True)
	print("\nFinal merged dataframe:")

	print(final_df)

	filepath = Path(f'./csv_check/final_cloud_cover.csv')
	final_df.to_csv(filepath)
	print("Cloud covers determination complete.")
	return final_df


def cloud_covers_pipeline(start_date, window):

	#print("Running cloud cover pipeline and returning GeoDataframe...")


	cities_gdf = geocoded_cities_pipeline()

	full_df = get_cloud_covers(cities_gdf, start_date, window)

	print(full_df)

	return full_df


## Check difference with Pastebin data

# url = "https://pastebin.com/raw/yxhrQ2D5"

# df_pastebin = pd.read_csv(url, delimiter='\t')



# full_df_test = cloud_covers_pipeline()

# full_df_test = full_df_test.rename(columns={'city_name':'name'})

# full_df_test = full_df_test.drop(columns=['country','adm0name','pop_max','geometry'])

# full_df_test = full_df_test.set_index('name')

# print(full_df_test)



# print(full_df_test)

# # #print(df_pastebin)

# df_pastebin = df_pastebin.set_index('name')

# print(df_pastebin)

# # df_pastebin.to_csv('./csv_check/pastebin_cloud_covers.csv')

# df_pastebin = df_pastebin.reindex_like(full_df_test)

# df_pastebin = df_pastebin.reset_index()

# print(df_pastebin)	

# df_pastebin.to_csv('./csv_check/pastebin_cloud_covers.csv')

# # #difference_df = full_df_test.compare(df_pastebin)

# # #print(difference_df)