import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from geopandas import GeoSeries, GeoDataFrame
from haversine import haversine

# get the [latitude, longitude] pair via station ID
def get_location_by_ID(data, station_id):
    if station_id not in data.st_id.values:
        print('Error: the station ID not found in the database')
    location = data[data.st_id == station_id][['latitude', 'longitude']].values
    return tuple(location.flat)

# get the name of the station via station ID
def get_name_by_ID(data, station_id):
    if station_id not in data.st_id.values:
        print('Error: the station ID not found in the database')
    name = data[data.st_id == station_id]['name']
    return name

def calculate_minimum_distances2(stations_data, station_id, locations,
            dict_keys=['st_id', 'closest_loc_index', 'closest_distance']):
    num_rows = len(locations)
    distances = np.zeros(num_rows)
    loc1 = get_location_by_ID(stations_data, station_id)
    for i, loc2 in enumerate(locations):
        dist = haversine(loc1, loc2)
        distances[i] = dist
    min_dist = np.min(distances)
    min_dist_index = np.argmin(distances).astype(int)
    return {dict_keys[0]: station_id, dict_keys[1]: min_dist_index, dict_keys[2]: min_dist}

# Import original bike station data
print('Reading in Bike station information...')
bike_info = pd.read_csv('./data/processed/station_info_1.csv')

path = './data/geolocation/'

additions = {
    'colleges':
        {'file_name': 'colleges.geojson',
         'stem': 'colleges',
         'stem_key': 'college'},
    'subways':
        {'file_name': 'subway_entrances.geojson',
         'stem': 'subways',
         'stem_key': 'subway'},
    'theaters':
        {'file_name': 'theaters.geojson',
         'stem': 'theaters',
         'stem_key': 'theater'},
    'museums':
        {'file_name': 'museums.geojson',
         'stem': 'museums',
         'stem_key': 'museum'}
 }

for addition in additions.keys():
    file_name = additions[addition]['file_name']
    file_path = path + file_name
    stem = additions[addition]['stem']
    stem_key = additions[addition]['stem_key']
    stem_name = 'closest_' + stem_key

    print('Reading in geolocations for ' + stem + '...')
    geo = gpd.read_file(file_path)
    geo_loc_key = stem_key + '_location'
    geo[geo_loc_key] = None
    for ind in geo.index:
        lat = geo.geometry[ind].y
        lng = geo.geometry[ind].x
        geo[geo_loc_key].iloc[ind] = tuple([lat, lng])

    print('Appending geolocation information for ' + stem + '...')
    labels1 = ['st_id',
               ('closest_' + stem_key + '_ind'),
               ('closest_' + stem_key +'_distance')]
    distances = []
    for st in bike_info.st_id:
        res = calculate_minimum_distances2(bike_info, st,
                    geo[geo_loc_key], dict_keys=labels1)
        res[stem_name] = geo.iloc[res[labels1[1]]]['name']
        distances.append(res)
    additional_info = pd.DataFrame(distances)
    bike_info = pd.merge(bike_info, additional_info, on='st_id')
    bike_info = bike_info.drop(labels1[1], axis=1)

# Save file
print('Saving to a file...')
bike_info.to_csv('./data/processed/station_info_extended.csv')
print('...PRCESSING COMPLETE')
