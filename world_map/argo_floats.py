"""
Matplotlib actually had the ARGO dataset on their examples page:
http://matplotlib.org/basemap/users/examples.html.
"""
import sys
sys.path.insert(0, '/home/shibi/jobs/upwork/clients/Alastair_Mactaggart/world_map/netcdf4-python/netCDF4')
from netCDF4 import Dataset, num2date
import time, calendar, datetime, numpy
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import urllib, os
# data downloaded from the form at
# http://coastwatch.pfeg.noaa.gov/erddap/tabledap/apdrcArgoAll.html
filename, headers = urllib.request.urlretrieve('http://coastwatch.pfeg.noaa.gov/erddap/tabledap/apdrcArgoAll.nc?longitude,latitude,time&longitude>=0&longitude<=360&latitude>=-90&latitude<=90&time>=2010-01-01&time<=2010-01-08&distinct()')
print(filename, headers)
dset = Dataset(filename)
lats = dset.variables['latitude'][:]
lons = dset.variables['longitude'][:]
time = dset.variables['time']
times = time[:]
t1 = times.min(); t2 = times.max()
date1 = num2date(t1, units=time.units)
print(date1)
date1 = date1.strftime("%m-%d-%Y")
print(date1)
date2 = num2date(t2, units=time.units)
print(date2)
date2 = date2.strftime("%m-%d-%Y")
print(date2)
dset.close()
os.remove(filename)
# draw map with markers for float locations
"""
map.drawcoastlines(linewidth=0.25)
map.drawcountries(linewidth=0.25)
map.fillcontinents(color='coral',lake_color='aqua')
"""
m = Basemap(projection='hammer',lon_0=180)
x, y = m(lons,lats)
m.drawmapboundary(fill_color='#6495ed')
m.drawcoastlines(linewidth=0.25)
m.fillcontinents(color='#cc9966',lake_color='#99ffff')
m.scatter(x,y,3,marker='o',color='#2f4f4f')
plt.title('Locations of %s ARGO floats active between %s and %s' %\
        (len(lats),date1,date2),fontsize=12)
plt.show()