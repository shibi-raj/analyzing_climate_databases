from peewee import *
from orm.merge_box_icoads_tables import *
from orm.ocean_box_tables import *
from orm.icoads_data_tables import *
import sys
import os

def box_lookup(obs_lat,obs_lon):
    """Look up location on grid of experimental data taken at longitude/latitude
    values, obs_lon/obs_lat.  
    
    Look up starts with latitude, then longitude at the fixed latitude.
    """
    # print("     Observations",obs_lat,"(lat)",obs_lon,"(lon)","\n")

    # latitude min and max 
    lat_extrm = GridPoint\
        .select(fn.Min(GridPoint.latitude),fn.Max(GridPoint.latitude))\
        .scalar(as_tuple=True)
    if not (lat_extrm[0] < obs_lat < lat_extrm[1]):
        raise ValueError(
            'Latitude not found on grid. Min/max interval {}, value given {}.'\
            .format(lat_extrm,obs_lat))

    # obs_lat latitude box index 
    i_lat,lat = GridPoint.select(GridPoint.lat_index,GridPoint.latitude)\
        .where(GridPoint.latitude > obs_lat)\
        .limit(1)\
        .scalar(as_tuple=True)
    i_lat -= 1

    # min and max longitudes at obs_lat latitude level 
    lon_extrm_at_lat = Longitude\
        .select(fn.Min(Longitude.longitude),fn.Max(Longitude.longitude))\
        .join(GridPoint).where(GridPoint.lat_index == i_lat)\
        .scalar(as_tuple=True)
    if not (lon_extrm_at_lat[0]<obs_lon<lon_extrm_at_lat[1]):
        raise ValueError(
            'Longitude not found on grid. Min/max interval {}, value given {}.'\
            .format(lon_extrm_at_lat,obs_lon))

    # obs_lon longitude box index
    i_lon,lon = Longitude.select(Longitude.lon_index,Longitude.longitude)\
        .join(GridPoint)\
        .where(GridPoint.lat_index == i_lat and Longitude.longitude > obs_lon)\
        .limit(1)\
        .scalar(as_tuple=True)
    i_lon -= 1

    return i_lon,i_lat

def icoads_to_boxes():
    db_merge.create_table(BoxObs)

    i = 0
    for ic in IcoadsData.select():
        try:
            print(box_lookup(ic.latitude,ic.longitude))
            i+=1
            print(ic.longitude,ic.latitude)
        except:
            pass
        if i > 10:
            break

if __name__ == '__main__':
    icoads_to_boxes()