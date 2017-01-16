#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

Merge ocean data databases with the Box database.  Every piece of data is 
matched by lon/lat coordinates to the respective box in a fixed-sized grid
covering the ocean.  

"""
import sys
import os
import logging
from peewee import *
from orm.ocean_box_tables import *

def box_lookup(obs_lat,obs_lon):
    """
    Look up the box indices for a measurement taken at coordinates obs_lat 
    and obs_lon.
    
    """
    index_query = "select lat_index_id, lon_index-1 " \
        + "from longitude " \
        + "where " \
        + "lat_index_id in " \
        +   "(select lat_index-1 " \
        +   "from latitude where lat_box > {} limit(1)) ".format(obs_lat) \
        + "and " \
        + "lon_box > {} ".format(obs_lon) \
        + "limit(1); " 

    i_lat, i_lon = list(db_box.execute_sql(index_query))[0]
    return i_lat,i_lon

def map_lons(lons,low=-180.,hi=180.):
    """
    Map longitude coordinate from (0,360) -> (-180,180).

    """
    if not isinstance(lons,list):
        lons = [lons]
    new_lons = list()
    for lon in lons:
        if lon > hi:
            new_lons.append(lon-(hi-low))
        else:
            new_lons.append(lon)
    return new_lons

def icoads_to_boxes():
    # Import ICOADS data tables - they only pertain to this function
    from orm.icoads_data_tables import IcoadsData, db_obs

    # Created (recreate) merged box and observations database
    if ObsData.table_exists():
        db_box.drop_table(ObsData)
        db_box.create_table(ObsData)
    else:
        db_box.create_table(ObsData)

    # set up objects for database inserts
    dict_obs = dict()
    data_obs = list()

    # counting indices
    total_icoads_inserts = 0
    icoads_errors = 0

    with db_box.atomic():
        for i, ic in enumerate(IcoadsData.select().iterator()):
            try:
                
                # raises error if box_lookup does not work, i.e., can't find box
                # map longitudes to the proper cooridnate system for processing
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
            if i % 10000 == 0 and data_obs:    
                with db_box.atomic():
                    insert_limit = 400
                    n_inserts = 0
                    last_index = len(data_obs)-1
                    while n_inserts <= last_index:
                        upper = n_inserts + insert_limit
                        if upper >= last_index:
                            upper = last_index+1
                        ObsData.insert_many(data_obs[n_inserts:upper]).execute()
                        n_inserts = upper
                    total_icoads_inserts += len(data_obs)
                    print("Total ICOADS inserts: ", total_icoads_inserts)
                    sys.stdout.flush()
                    data_obs[:] = []

        # populating database tables, catch leftovers not inserted in the loop
        with db_box.atomic():
            if data_obs:
                n_inserts = 0
                last_index = len(data_obs)-1
                while n_inserts <= last_index:
                    upper = n_inserts + insert_limit
                    if upper >= last_index:
                        upper = last_index+1
                    ObsData.insert_many(data_obs[n_inserts:upper]).execute()
                    n_inserts = upper
                total_icoads_inserts += len(data_obs)

    print("total inserts of ICOADS data: ", total_icoads_inserts)
    print("total errors inserting data:  ", icoads_errors)

def wod_to_boxes():
    # import WOD data tables - they only pertain to this function
    from orm.wod_data_tables import StdDepth,WodData,db_wod
    
    # Created (recreate) observations' database in ocean_box_tables
    if WodMeta.table_exists():
        db_box.drop_table(WodMeta)
    if WodDepthData.table_exists():
        db_box.drop_table(WodDepthData)        
    db_box.create_table(WodMeta)
    db_box.create_table(WodDepthData)

    # set up objects for database inserts
    dict_wod = dict()
    data_wod = list()
    dict_std = dict()
    data_std = list()

    # counters
    total_wod_inserts = 0
    total_std_inserts = 0
    total_wod_errors = 0

    with db_box.atomic():

        for i, wod in enumerate(WodData.select().iterator()):
        
            try:
                name = '_'.join(map(str,box_lookup(wod.lat_obs,wod.lon_obs)))
                
                # Create list of obs meta data for insert
                dict_wod.update({
                    'name':name,
                    'cast_id':wod.cast_id,
                    'exp_type':wod.exp_type,
                    'num_levels':wod.num_levels,
                    'lat_obs':wod.lat_obs,
                    'lon_obs':wod.lon_obs,
                    'date':wod.date,
                    'pentad':wod.pentad}
                )
                data_wod.append(dict_wod.copy())

                # Create list for standard depth inserts with same cast_id
                # For this work, there should be an index on cast_id in StdDepth
                cast_query = StdDepth.select().where(
                    StdDepth.cast_id==wod.cast_id)

                for j, std in enumerate(cast_query.iterator()):
                    dict_std.update({
                        'cast_id':wod.cast_id,
                        'depth':std.depth,
                        'temperature':std.temp}
                    )
                    data_std.append(dict_std.copy())


            except Exception as e:
                logging.exception(e)    
                break
                total_wod_errors = total_wod_errors + 1

            # populating Box database tables, WodMeta and WodDepthData
            if (i + 1) % 1000 == 0 and data_wod:    
                with db_box.atomic():
                    
                    # insert into WodMeta
                    insert_limit = 400
                    n_inserts = 0
                    last_index = len(data_wod)-1
                    while n_inserts <= last_index:
                        upper = n_inserts + insert_limit
                        if upper >= last_index:
                            upper = last_index+1
                        WodMeta.insert_many(data_wod[n_inserts:upper]).execute()
                        n_inserts = upper
                    total_wod_inserts += len(data_wod)
                    print("\nTotal WOD inserts: ", total_wod_inserts)
                    sys.stdout.flush()
                    data_wod[:] = []

                    # insert into WodDepthData
                    n_inserts = 0
                    last_index = len(data_std)-1
                    while n_inserts <= last_index:
                        upper = n_inserts + insert_limit
                        if upper >= last_index:
                            upper = last_index+1
                        WodDepthData.insert_many(data_std[n_inserts:upper]).execute()
                        n_inserts = upper
                    total_std_inserts += len(data_std)
                    print("Total WodDepthData inserts: ", total_std_inserts)
                    sys.stdout.flush()
                    data_std[:] = []

        # populating database tables, catch leftovers not inserted in the loop
        with db_box.atomic():
            insert_limit = 400
            
            # insert into WodMeta
            n_inserts = 0
            last_index = len(data_wod)-1
            while n_inserts <= last_index:
                upper = n_inserts + insert_limit
                if upper >= last_index:
                    upper = last_index+1
                WodMeta.insert_many(data_wod[n_inserts:upper]).execute()
                n_inserts = upper
            total_wod_inserts += len(data_wod)
            sys.stdout.flush()
            data_wod[:] = []

            # insert into WodDepthData
            n_inserts = 0
            last_index = len(data_std)-1
            while n_inserts <= last_index:
                upper = n_inserts + insert_limit
                if upper >= last_index:
                    upper = last_index+1
                WodDepthData.insert_many(data_std[n_inserts:upper]).execute()
                n_inserts = upper
            total_std_inserts += len(data_std)
            sys.stdout.flush()
            data_std[:] = []

    print("\nTotal inserts of WodMeta data:         ", total_wod_inserts)
    print("Total inserts of WodDepthData data: ", total_std_inserts)
    print("Total errors inserting data:           ", total_wod_errors)



if __name__ == '__main__':
    wod_to_boxes()
