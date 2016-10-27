"""Creating map with box_and_obs.db database."""
from mpl_toolkits.basemap import Basemap, pyproj
from orm.merge_box_icoads_tables import *
from orm.icoads_data_tables import *
import matplotlib.pyplot as plt
import numpy as np
import os 

def map_lons(lons,low=-180.,hi=180.):
    if not isinstance(lons,list):
        lons = [lons]
    new_lons = list()
    for lon in lons:
        if lon > hi:
            new_lons.append(lon-(hi-low))
        else:
            new_lons.append(lon)
    return new_lons


def main():

    data_coords = list()

    print(IcoadsData.select().count())

    # for od in ObsData.select():
    for data in IcoadsData.select():
        data_coords.append([data.lon_obs, data.lat_obs])

    lons,lats = zip(*data_coords)

    lons = map_lons(lons)

    # fig = plt.figure()
    # ax = fig.add_subplot(1,1,1)
    # plt.subplot(2,1,1)
    # m = Basemap(projection='hammer',lat_0=0.,lon_0=0.)
    m = Basemap(projection='merc',llcrnrlat=-80,urcrnrlat=80,\
            llcrnrlon=-180,urcrnrlon=180,lat_ts=0.,resolution='c')
    x,y = m(lons,lats)

    m.drawcoastlines()
    m.scatter(x,y,.0001,marker='o',color='b')
    # m.drawmeridians(np.arange(70,290,10.))

    # # ax = fig.add_subplot(1,1,1)
    # plt.subplot(2,1,2)
    # # m = Basemap(projection='hammer',lat_0=0.,lon_0=180.)
    # m = Basemap(projection='merc',llcrnrlat=-80,urcrnrlat=80,\
    #         llcrnrlon=-180,urcrnrlon=180,lat_ts=20,resolution='c')
    # x,y = m(lons,lats)
    # m.drawcoastlines()
    # m.scatter(x,y,.005,marker='o',color='b')

    plt.show()

if __name__ == '__main__':
    main()


