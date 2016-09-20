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
    index_query = "select lat_index_id, lon_index-1 from longitude " \
        + "join latitude on longitude.lat_index_id = latitude.lat_index " \
        + "where lon_box > {} and lat_index_id ".format(obs_lon) \
        + "in (select lat_index-1 " \
        + "from latitude where lat_box > {} limit(1))".format(obs_lat) \
        + " limit(1);"
    
    # print(index_query)
    i_lat, i_lon = list(db_box.execute_sql(index_query))[0]

    # Deprecated

    # # latitude index
    # i_lat = Latitude.select(Latitude.lat_index).where(
    #     Latitude.lat_box > obs_lat).limit(1).scalar()  - 1
    # # longitude index
    # i_lon = Longitude.select(Longitude.lon_index).join(Latitude).where(
    #     Latitude.lat_index==i_lat,
    #     Longitude.lon_box > obs_lon).limit(1).scalar() - 1 
    return i_lat,i_lon

def icoads_to_boxes():
    # Created (recreate) merged box and observations database
    if ObsData.table_exists():
        db_box.drop_table(ObsData)
        db_box.create_table(ObsData)
    else:
        db_box.create_table(ObsData)

    # set up data structures for database
    dict_obs = dict()
    data_obs = list()

    # counting indices
    total_icoads_inserts = 0
    icoads_errors = 0

    with db_box.atomic():
        for i, ic in enumerate(IcoadsData.select().iterator()):
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
            if i % 10000 == 0 and data_obs:    
                with db_box.atomic():
                    insert_limit = 400
                    n_inserts = 0
                    last_index = len(data_obs)-1
                    while n_inserts <= last_index:
                        upper = n_inserts + insert_limit
                        if upper >= last_index:
                            upper = last_index+1
                        # print(n_inserts,upper, data_obs[n_inserts:upper])
                        ObsData.insert_many(data_obs[n_inserts:upper]).execute()
                        n_inserts = upper
                    total_icoads_inserts += len(data_obs)
                    print("Total ICOADS inserts: ", total_icoads_inserts)
                    sys.stdout.flush()
                    data_obs[:] = []

        # populating database tables, catch leftover
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

if __name__ == '__main__':
    icoads_to_boxes()
