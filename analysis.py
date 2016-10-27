"""
Analysis program does sql queries and data manipulations.  Basically, fetching 
different combinations, relations, and formats of data from the database.
"""
from peewee import *
from mpl_toolkits.basemap import Basemap, pyproj
from datetime import date,datetime
from orm.icoads_data_tables import *
from icoads3.create_dictionary import load_yearly_intervals
import numpy as np
import matplotlib.pyplot as plt
import math
import pandas as pd
import scipy.stats as stats
import sys
import time_series
import pickle

# --------------- 
writing = False #  FLAG FOR OCEAN_BOX_TABLES
# ---------------  
from orm.ocean_box_tables import *
from merge_box_obs import box_lookup

def pickle_list(lst,file='save.p'):
    pickle.dump(lst, open( file, "wb" ) )

def load_pickle_list(file='save.p'):
    return pickle.load(open(file,"rb"))

def conv_pent_hmth(pentad):
    """Input pentad, output the corresponding half month."""
    pentad = str(pentad)
    d = load_yearly_intervals()
    # print(d,'\n')
    for month in d:
        for hmth in d[month]:
            if pentad in d[month][hmth]['pentads']:
                return hmth

def conv_hmth_pentad(hmonth):
    """Input half-month, return set of corresponding pentads."""
    hmonth = str(hmonth)
    d = load_yearly_intervals()
    for month in d:
        for hmth in d[month]:
            if hmth == hmonth:
                return(d[month][hmth]['pentads'])

def str_fmt_join(variable,delimit="','"):
    """Simple string formatting code for joining strings for reuse in sql
    statements.
    """
    if isinstance(variable,(str,int)):
        variable = [variable]
    variable = map(str,variable)
    return delimit.join(variable)

def process_years(years):
    """Utility to handle different inputs for years and generate title of 
    plot.
    """
    if isinstance(years,(list,tuple)):
        years = tuple(sorted(years))
    elif isinstance(years,(int,str)):
        years = (years,years)
    date_min = str(years[0])+'-01-01'
    date_max = str(years[1])+'-12-31'
    return date_min,date_max

def box_sst_data(names,years,pentads=None):
    """Get all data for box in the years specified."""
    date_min,date_max = process_years(years)
    sql = "select lon_obs,lat_obs,sst,date "\
    + "from obsdata "\
    + "where name in ('{}') ".format(str_fmt_join(names))\
    + "and date between '{}' and '{}' ".format(date_min,date_max)
    if pentads:
        sql = sql + "and pentad in ('{}') ".format(str_fmt_join(pentads))    
    sql = sql + ";"
    # print(sql)
    try:
        lon_obs,lat_obs,sst,date = zip(*db_box.execute_sql(sql))
    except:
        lon_obs,lat_obs,sst,date = list(),list(),list(),list()
    return lon_obs,lat_obs,sst,date

def data_locations(name,years):
    """Get locations of data for in a box in a given range of years."""
    date_min,date_max = process_years(years)
    sql = "select lon_obs,lat_obs "\
    + "from obsdata "\
    + "where name = '{}' ".format(name)\
    + "and date between '{}' and '{}' ".format(date_min,date_max)\
    + ";"
    # print(sql)
    try:
        lon_obs,lat_obs = zip(*db_box.execute_sql(sql))
    except:
        lon_obs,lat_obs = list(),list()
    return lon_obs,lat_obs

def sst_year_hmonth(name,years):
    date_min,date_max = process_years(years)
    sql = "select sst, strftime('%Y',date), pentad "\
    + "from obsdata "\
    + "where name = '{}' ".format(name)\
    + "and date between '{}' and '{}' ".format(date_min,date_max)
    sql = sql + "order by strftime('%Y',date);"
    # print(sql)
    ssts,yrs,pentads= zip(*db_box.execute_sql(sql))
    hmonths = [conv_pent_hmth(int(p)) for p in pentads]
    return ssts,yrs,hmonths

def mean_sst_by_half_month(name, years):
    """If half-month data not in database (currently it is not, 10/5/2016),
    get half months from the pentad information.

    Returns:
        years of the series
        half months when data collected
        mean of sst in that half month, in that year
        number of data points in that half month, in that year, from which
            mean calculated
    """
    # get the data converted already to hmonths
    ssts,yrs,hmonths = sst_year_hmonth(name,years)
    # set up loop to average ssts by hmonth
    avg_sst = list()
    results = list()
    iter_1 = True
    for a,b,c in zip(yrs,hmonths,ssts):
        if iter_1:
            iter_1 = False
            the_year = a
            the_hmonth = b
            avg_sst.append(c)
            continue
        if a == the_year and b == the_hmonth:
            avg_sst.append(c)
        else:
            l = len(avg_sst)
            results.append((the_year,the_hmonth,sum(avg_sst[:])/l,l))
            # reset for next iteration
            the_year = a
            the_hmonth = b
            avg_sst[:] = []
            avg_sst.append(c)
    # pick up the remaining not caught in loop
    if avg_sst:
        l = len(avg_sst)
        results.append((the_year,the_hmonth,sum(avg_sst[:])/l,l))
    # output
    yrs,hmonths,avg_ssts,counts = zip(*results)
    return yrs,hmonths,avg_ssts,counts

def mean_sst_by_year(names,years,pentads=None):
    """Gives avg sst series for specified year, as well as number of obs per 
    year.  Optionally, can specify the pentad.
    """
    date_min,date_max = process_years(years)
    # if names:
    if isinstance(names,str):
        names = [names]
    name_query = " and name in ('{}') ".format(str_fmt_join(names))

    sql = "select avg(sst), count(*), strftime('%Y',date) "\
    + "from obsdata "\
    + "where name in ('{}') ".format(str_fmt_join(names))\
    + "and date between '{}' and '{}' ".format(date_min,date_max)
    if pentads:
        sql = sql + "and pentad in ({}) ".format(','.join(map(str,pentads)))
    sql = sql + "group by strftime('%Y',date);"
    # print(sql)
    avg_ssts,counts,yrs= zip(*db_box.execute_sql(sql))
    return avg_ssts,counts,yrs

def mean_sst_by_pentad(names,years):
    """Retrieve avg(sst) for each pentad over the specified years.  Can specify
    'name' fields to focus on a specific box.
    """
    date_min,date_max = process_years(years)
    if names:
        if isinstance(names,str):
            names = [names]
        name_query = " and name in ('{}') ".format("','".join(names))
    else:
        name_query = ''
    sql = "select pentad, avg(sst) "\
    + "from obsdata "\
    + "where date between '{}' and '{}' ".format(date_min,date_max)\
    + name_query \
    + "group by pentad;"
    # print(sql)
    pentads, avg_ssts = zip(*db_box.execute_sql(sql))
    return pentads,avg_ssts

def all_sst_by_pentad(years,name=None):
    """Retrieve sst data for each pentad over the specified years.  Can specify
    'name' fields to focus on a specific box.
    """
    date_min,date_max = process_years(years)
    if name:
        name_query = " and name = '{}' ".format(name)
    else:
        name_query = ''
    sql = "select pentad, sst "\
    + "from obsdata "\
    + "where date between '{}' and '{}' ".format(date_min,date_max)\
    + name_query \
    + ';'
    # print(sql)
    pentads, all_ssts = zip(*db_box.execute_sql(sql))
    return pentads,all_ssts

def sst_spread_by_pentad(years,name=None):
    pentads, ssts = all_sst_by_pentad(years=years,name=name)
    data = list(zip(pentads,ssts))
    print(data)
    return pentads, ssts

def dense_boxes(years,limit=10):
    """Retrieve boxes in order of most populated to least populated with 
    data.
    """
    date_min,date_max = process_years(years)
    sql = "select name, count(name) "\
    + "from obsdata "\
    + "where date between '{}' and '{}' ".format(date_min,date_max)\
    + "group by name "\
    + "having count(name) > 0 "\
    + "order by count(name) desc "\
    + "limit {};".format(limit)
    # print(sql)
    name, counts = zip(*db_box.execute_sql(sql))
    return name, counts

def haversine(lon1,lat1,lon2,lat2):
    """Same function as in earth_angle_calcs.
    Calculate the great circle distance between two points on the earth 
    (specified in decimal degrees).
    Source: http://gis.stackexchange.com/a/56589/15183
    """
    # convert decimal degrees to radians 
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    # haversine formula 
    dlon = lon2 - lon1 
    dlat = lat2 - lat1 
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a)) 
    km = 6371 * c
    return km

def radius_stats(radius,name,years,pentad=None):
    """Find all data in a given radius relative to a box center."""
    # Find center of box
    sql_center = "select box_center_lon,box_center_lat "\
    + "from box "\
    + "where name = '{}';".format(name)
    lon1,lat1 = list(db_box.execute_sql(sql_center))[0]
    
    # Narrow search range for observations within radius
    zonal_dist = 111.19 # 111.19 km at equator corresponds 1 degree
    zonal_dist = 0.9 * zonal_dist # increase search a little
    degrees = radius/zonal_dist

    # Find nearby data
    sql = "select name,lon_obs,lat_obs,sst,date,pentad "\
    + "from obsdata "\
    + "where ("\
    + "  strftime('%Y',date) between '{}' and '{}' ".format(years[0],years[1])\
    + "  and lon_obs between {} and {} ".format(lon1-degrees,lon1+degrees)\
    + "  and lat_obs between {} and {} ".format(lat1-degrees,lat1+degrees)
    if pentad:
        sql = sql + " and pentad = {} ".format(pentad)
    sql = sql + ") "\
    + ";"
    # Add data to output
    results = list()
    for data in db_box.execute_sql(sql):
        distance = haversine(lon1,lat1,data[1],data[2])
        if distance <= radius:
            results.append(data)
    return results

def radius_stat_profiles(name,years,pentad=None,magnitudes=(0,4),filename=None):
    """Edit this function instead of radius stats() to get whatever you want."""
    
    # SST, STD(SST), vs. Radius
    title = ['MEAN SST', 'STD(SST)', 'Radius from box {} (km)'.format(name),
        'Pentad']
    title = ",".join(title)
    print(title)

    with open(filename,'a') as f:

        for i in range(magnitudes[0],magnitudes[1]):
            radii = range(int(10**(i)),int(10**(i+1)),int(10**i))
            for radius in radii:
                if radius == 0:
                    continue
                sst = [rd[3] for rd in radius_stats(radius,name,years,pentad=pentad)]
                # sst = [rd[3] for rd in results]
                if (sst):
                    out = ",".join(
                        [str(np.mean(sst)), str(np.std(sst)), str(radius), 
                            str(len(sst)), str(pentad)])
                    f.write(out+'\n')
                    print(out)
                    sys.stdout.flush()

def box_centers(names):
    """Return box center coordinates of boxes.  If names is a single box string,
    also return box size.  If names is a list/tuple with more than one value,
    return its box center coordinates, (lon,lat), and the box name.
    """
    if isinstance(names,(list,tuple)):
        sql = "select box_center_lon,box_center_lat "\
        + "from box where name in ('{}'); ".format("','".join(names))
        # print(sql)
        output = list()
        for center,name in zip(db_box.execute_sql(sql),names):
            output.append((center[0],center[1],name))
        return output
    else:    
        sql = "select box_center_lon,box_center_lat,box_side "\
        + "from box where name = '{}'; ".format(names)
        c_lon,c_lat,box_size = zip(*db_box.execute_sql(sql))
        return c_lon[0],c_lat[0],box_size[0]

def boxes_within_radius(center,radius):
    """Determine all of the boxes within a given radius relative a central 
    box.  The distance is the great circle between the centers.
    """
    # center box indices
    c_ilat,c_ilon = map(int,center.split('_'))
    # retrieve center coords of center box
    c_lon,c_lat,box_size = box_centers(center)
    # box size in km
    box_size = box_size/1000.
    # narrow search range by limiting box indices
    delta_index = int((radius+2*box_size)/box_size)
    i_lats = list(range(c_ilat-delta_index,c_ilat+delta_index+1,1))
    i_lons = list(range(c_ilon-delta_index,c_ilon+delta_index+1,1))
    # create indices of narrowed list of boxes to search 
    search_boxes = list()
    for i_lat in i_lats:
        for i_lon in i_lons:
            search_boxes.append("{}_{}".format(i_lat,i_lon))
    # find boxes within given radius
    near_boxes = list()
    for center in box_centers(search_boxes):
        dist = haversine(c_lon,c_lat,center[0],center[1])
        if dist <= radius:
            near_boxes.append(center[2])
    return near_boxes

def sim_series(series,times,num_sims=100):
    """Simulating the null hypothesis of the time series.  Simulation starts at 
    beginning point of the series, then creates random increments with std. 
    devation of the series at each time step.
    """
    # time series data info
    # series = np.array(list(map(float,series)))
    # times = np.array(list(map(float,times)))
    # m, b = np.polyfit(times,series,1)
    m, b, r_value, p_value, std_err = stats.linregress(times,series)
    # slope, intercept, r_value, p_value, std_err = stats.linregress(yrs,avg_ssts)

    # set up simulations 
    std = np.std(series,ddof=1)
    start = series[0]

    simulations = list()
    for i_sim in range(num_sims):
        sim = [start]
        for i,step in enumerate(np.random.normal(0, std, series.size-1)):
            sim.append(sim[i]+step)
        plt.plot(times,sim,'gray',alpha=0.1)
        simulations.append(sim)

    slopes = list()
    for sim in simulations:
        slope, intercept = np.polyfit(times,sim,1)
        slopes.append(slope)

    # print('here',np.std(slopes,ddof=1))
    # scale = var(errors)/sum(times-mean(time))
    interval = stats.norm.interval(
        alpha=.95, loc=np.mean(slopes), scale=std_err
    )
    return m,b,simulations,interval,slopes,std_err

def complete_decades(years):
    years = list(map(int,years))
    period = years[-1]-years[0]+1
    period = (period - 9)//10 * 10
    upper = years[0]+period-1
    if years[1] != upper:
        print('Changing years for decade completion.')
        years = (years[0],upper)
        print('Years: ',years,'\n')
    return years

def decades(years,half_decs=False):
    """Diveide range of years into smaller ranges of decades.  'half_decs' 
    for periods of 5 years instead of decades.
    """
    years = complete_decades(years)
    decades = list()
    if half_decs == True:
        per_size = 5
        per_end = 4
    else:
        per_size = 10
        per_end = 9
    for i,yrs in enumerate(range(years[0],years[1],per_size)):
        # decades.append(list(range(yrs,yrs+10)))
        decades.append((yrs,yrs+per_end))
    return decades

def group_series_in_decades(name,years,hmonth):
    # make sure years make complete decades 
    years = complete_decades(years)

    avg_ssts,counts,yrs = yearly_data_time_series(name,years,hmonth=hmonth)


    # print(avg_ssts,counts,yrs)

    # result lists
    results = list()

    # loop lists
    dec_ssts = list()
    dec_counts = list()
    print()
    for i,dec in enumerate(range(years[0],years[1]+1,10)):
        for s,c,y in zip(avg_ssts,counts,yrs):
            if dec <= int(y) <= dec+9:
                dec_ssts.append(s)
                dec_counts.append(c)
        try:
            results.append([sum(dec_ssts)/len(dec_ssts), sum(dec_counts), "{}-{}".format(dec, dec+9),i+1])
            # print(sum(dec_ssts)/len(dec_ssts), sum(dec_counts), "{}-{}".format(dec, dec+9),i+1)
        except:
            results.append([0,sum(dec_counts),"{}-{}".format(dec, dec+9),i+1])
            # print(0,sum(dec_counts),"{}-{}".format(dec, dec+9),i+1)
        dec_ssts[:] = []
        dec_counts[:] = []
    return results

def yearly_data_time_series(name,years,hmonth=None,month=None,pentads=None):
    """Create a yearly time series from the data where SST is averaged over the
    same time period in the year.  
    
    For example, find the SST average for the month of January for every year 
    between 1861-1870.
    """
    date_min,date_max = process_years(years)
    if hmonth:
        pentads = conv_hmth_pentad(hmonth)
    sql = "select avg(sst), count(sst), strftime('%Y',date) from obsdata "\
    + "where name = '{}' ".format(name)\
    + "and pentad between {} and {} ".format(pentads[0],pentads[-1])\
    + "and date between '{}' and '{}' ".format(date_min,date_max)\
    + "group by strftime('%Y',date);"
    # print(sql)
    avg_ssts,counts,yrs = zip(*db_box.execute_sql(sql))
    return avg_ssts,counts,yrs

def single_box_dist(name, years):
    """Simple returns coordinates of all data in given box in a given range of
    years.
    """
    years = process_years(years)
    sql = "select lon_obs,lat_obs from obsdata "\
    + "where name = '{}' ".format(name)\
    + "and date between '{}' and '{}' ".format(*years)\
    + ";"
    lons,lats = zip(*db_box.execute_sql(sql))
    return lons, lats

def plain_time_series(name,years,hmonth=None,pentad=None):
    date_min,date_max = process_years(years)
    sql = "select sst, date from obsdata "\
    + "where name = '{}' ".format(name)
    if years:
        sql = sql + "and date between '{}' and '{}' ".format(date_min,date_max)
    if hmonth:
        pentads = conv_hmth_pentad(hmonth)
        sql = sql + "and pentad in ({}) ".format(','.join(map(str,pentads)))
    if pentad:
        sql = sql + "and pentad = '{}' ".format(pentad)
    sql = sql + "order by date;"
    print(sql)
    ssts,dates = zip(*db_box.execute_sql(sql))
    dates = [datetime.strptime(date,'%Y-%m-%d').date() for date in dates ]
    return ssts,dates

# def ols_by_decade(name,years):
#     decs = decades(years)
#     for decade in decs:
#         print(decade)


if __name__ == '__main__':
    name = '739_1853'
    years = (1850,1900)
    ols_by_decade(name,years)
    # ssts,dates = plain_time_series(name,years,hmonth=1)
    # regression_by_decade(name,years)

    # name,counts = dense_boxes(years,limit=100)
    # name = '694_3810'
    

    # # avg_ssts,counts,yrs = mean_sst_by_year(name,years,pentad=None)
    # # m,interval = sim_series(avg_ssts,yrs)[0:2]
    # # print(m,interval,interval[0]<=m<= interval[1])

    # hmonth=12
    # avg_ssts,counts,yrs = yearly_data_time_series(name,years,hmonth=hmonth)
    # yrs = np.array(list(map(int,yrs)))
    # avg_ssts = np.array(list(map(float,avg_ssts)))
    
    # plt.plot(yrs,avg_ssts)
    # plt.show()
    # print(yrs, avg_ssts)
    # slope, intercept, r_value, p_value, std_err = stats.linregress(
    #     yrs,avg_ssts)
    # print(slope, intercept, r_value**2, p_value, std_err)
    # for result in group_series_in_decades(name,years,hmonth):
    #     print(result)


    # name = '739_1853'
    # principal = StatBoxTests(name,years)
    # test_name = '694_3810'

    # names = ['739_1853','739_1852','739_1854',
    #          '740_1853','740_1852','740_1854','740_1855',
    #          '738_1851','738_1850','738_1852','738_1853','738_1854']

    # name = '739_1853'
    # principal = StatBoxTests(name,years)
    # radius = 20.
    # names = boxes_within_radius(name,radius)

    # keep = list()
    # reject = list()
    # # principal.perform_tests(names)

    
    # principal.means_t_test(names[0])
    
    # for name in names:
    #     try:
    #         if principal.perform_tests(name):
    #             keep.append(name)
    #         else:
    #             reject.append(name)
    #         # print()
    #     except:
    #         pass
    #         # reject.append(name)
    #     # sys.stdout.flush()

    # print(len(keep))
    # print(len(reject))