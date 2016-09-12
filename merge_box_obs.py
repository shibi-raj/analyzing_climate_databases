from peewee import *
from orm.ocean_box_tables import *
from orm.icoads_data_tables import *
from observations_on_map import map_lons
import sys
import os


def box_lookup(obs_lat,obs_lon):
    """Look up the box indices for a measurement taken at coordinates obs_lat 
    and obs_lon.
    """
    # retrieve latitude index
    # t0 = time.time()
    i_lat = Latitude.select(Latitude.lat_index).where(
        Latitude.lat_box > obs_lat).limit(1).scalar() - 1
    # t1 = time.time()
    # print("total time1: ", t1-t0)

    # get latitude object corresponding to that index
    # latitude = Latitude.get(Latitude.lat_index == i_lat)

    i_lon = Longitude.select(Longitude.lon_index).join(Latitude).where(
        Latitude.lat_index==22,
        Longitude.lon_box>-65.0).limit(1).scalar() - 1 

    # now, retrieve longitude index
    # t2 = time.time()
    # for lon in latitude.longitudes:
    #     if lon.lon_box > obs_lon:
    #         i_lon = lon.lon_index - 1
    #         break
    # t3 = time.time()
    # print("total time2: ", t3-t2)

    return i_lat,i_lon

import time

def icoads_to_boxes():
    # Created (recreate ) merged box and observations database
    db_box.drop_table(ObsData)
    db_box.create_table(ObsData)

    # set up data structures for database
    dict_obs = dict()
    data_obs = list()

    # counting indices
    total_icoads_inserts = 0
    icoads_errors = 0

    with db_box.atomic():
        for i, ic in enumerate(IcoadsData.select().limit(1000)):
            try:
                # raises error if box_lookup does not work, i.e., can't find box
                modified_lon = map_lons(ic.lon_obs)[0]
                name = '_'.join(map(str,box_lookup(ic.lat_obs,modified_lon)))
                
                # Creating list of obs data for insert
                dict_obs.update({
                    'name':name,
                    'lat_obs':ic.lat_obs,
                    'lon_obs':modified_lon,
                    'sst':ic.sst,
                    'date':ic.date,
                    'pentad':ic.pentad,
                    'half_mth':ic.half_mth}
                )
                data_obs.append(dict_obs.copy())
            except:
                icoads_errors+=1

            # populating database tables
            if i % 200 == 0 and data_obs:    
                with db_box.atomic():
                    ObsData.insert_many(data_obs).execute()
                    total_icoads_inserts += len(data_obs)
                    # print("... # inserts: ", total_icoads_inserts)
                    # print("... # errors:  ", icoads_errors)
                    sys.stdout.flush()
                    data_obs[:] = []
            # if i % 1000 == 0 and data_obs:    
            #     ObsData._meta.auto_increment = False
            #     with db_box.transaction():
            #         for obsdata in data_obs:
            #             ObsData.insert(**obsdata).execute()
            #         total_icoads_inserts += len(data_obs)
            #         # print("... # inserts: ", total_icoads_inserts)
            #         # print("... # errors:  ", icoads_errors)
            #         sys.stdout.flush()
            #         data_obs[:] = []
            #     ObsData._meta.auto_increment = True



        # populating database tables, catch leftover
        with db_box.atomic():
            if data_obs:
                ObsData.insert_many(data_obs).execute()
                total_icoads_inserts += len(data_obs)

    print("total inserts of ICOADS data: ", total_icoads_inserts)
    print("total errors inserting data:  ", icoads_errors)

if __name__ == '__main__':
    icoads_to_boxes()
    # lat_obs = 5.0
    # lon_obs = -150.0
