#!/usr/bin/env/python3
"""Set of functions to put equal area boxes on the worlds' oceans."""
from mpl_toolkits.basemap import Basemap, pyproj
from matplotlib.patches import Polygon
from matplotlib.collections import PolyCollection
from matplotlib.path import Path
# from zodb.ocean_data import *
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import math
import transaction
from orm.ocean_box_tables import *
from orm.icoads_data_tables import *
from observations_on_map import map_lons

def lon_distance(Proj,pt1,pt2):
    """Meant to return distance longitudinally between two points at the same
    latitude.  If the angular difference between the two points is greater 
    than 180 degrees, pyproj.Geod.inv returns the smaller segment, so have to
    break interval into modulo 180 degrees to find correct total distance.  
    Points are reordered to go from East to West.

    Args:
        Proj: instance of a Basemap projection
        pt1: first point of type tuple: (lon,lat)
        pt2: second point of type tuple: (lon,lat)

    Examples:
        pt1=(-180,0), pt2=(180,0) => 40030154.742485 (circumference @ equator)
        pt1=(-180,80), pt2=(180,80) => 4447794.971387

    Useful Numbers:
        Circumference @ equator: 40030154.742485 
        # of meters per mile: 1609.344 
        Earth surface area: 510 million square kilometers 
        Ocean surface area: 361,900,000 square kilometers
        Ocean surface area percentage: 71% of the Earth's surface
    """
    # Reorder points from East to West
    if pt1[1] != pt2[1]:
        raise ValueError("lon_distance() intended for points with equal \
                latitude: pt1 {}, pt2 {}".format( pt1[1] ,pt2[1] ) )
    
    # Switch order according to longitude, if necessary
    if pt2[0] < pt1[0]:
        pt1, pt2 = pt2, pt1

    # Create points separated by 180 degrees in longitude + remainder
    difflon = abs(pt2[0]-pt1[0])
    decimal, whole= math.modf(difflon/180.)
    whole = int(whole)
    points = [pt1]
    for w in range(whole):
        points.append((pt1[0]+(w+1)*180,pt1[1]))
    if decimal > 0:
        points.append((pt1[0]+(whole + decimal)*180,pt1[1]))

    # Create pairs of points and find distance in longitude btw them
    pairs = tuple(zip(points,points[1:]))

    # Sum distances in longitude between consecutive points
    distance = 0.
    gc = pyproj.Geod(a=Proj.rmajor,b=Proj.rminor)
    for pair in pairs:
        az1, az2, dist12 = gc.inv(pair[0][0],pair[0][1],pair[1][0],pair[1][1])
        distance += dist12
    return distance

def lat_angle(proj,pt1,dist,longitude=False):
    """Given a point (lon,lat) and a distance, calculate the map coordinates 
    after moving that distance in either the latitudinal or longitudinal 
    direction.
    """
    # Get map projection coordinates
    x,y = proj(pt1[0],pt1[1])
    # Add distance to latitude or longitude, return new point in polar coords
    if not longitude:
        lon2, lat2 = proj(x,y+dist,inverse=True)
    else:
        lon2, lat2 = proj(x+dist,y,inverse=True)
    return [lon2,lat2]

def make_box(proj,lon,lat,delphi,delthe):
    """Given the location of the lower-left corner of a patch and the length of
    the sides, calculate the coordinates of a square patch at that location.
    
    Args:
        lon: longitude ll corner
        lat: latitude ll corner
        side: length of side of the square patch

    Order of output:
        clockwise starting at ll corner
        lower left, upper left, upper right, lower right
    """
    aug_lon = lon+delphi
    aug_lat = lat+delthe
    pt00 = [lon,lat]
    pt01 = [lon,aug_lat]
    pt11 = [aug_lon,aug_lat]
    pt10 = [aug_lon,lat]
    pts = [pt00,pt01,pt11,pt10]
    lons,lats = zip(*pts)
    lons = list(lons)
    lats = list(lats)
    return lons,lats

def lon_box_chain(proj,upper_lat,size=100000.,lon_0=0.,lat_0=0.,del_lon=50.):
    """Create adjoining boxes same latitude through specified longitudinal 
    angle.  Boxes start at Prime Meridian and travels East.

    Also, returns the box angular width and height
    """
    # Calculate increment of longitude (angular width), delta phi
    R = 6371000.
    delphi = size/R*math.cos(lat_0*math.pi/180.)
    delphi = delphi*180/math.pi

    # Calculate increment in latitude (angular height), delta theta
    delthe = size/R
    delthe = delthe*180./math.pi
    if lat_0 + delthe > upper_lat:
        delthe = upper_lat - lat_0 
    
    # Calculate lons/lats for ll corner of each box
    lons = lon_0 + np.arange(0.,del_lon,delphi)
    lats = [lat_0 for lon in lons]
    pts = list(zip(lons,lats))
    boxes = list()
    last = len(pts)-1
    for ipt,pt in enumerate(pts):
        if ipt == last:
            delphi = lon_0 + del_lon - lons[-1]
        boxes.append(make_box(proj,pt[0],lat_0,delphi,delthe))
    return delthe,delphi,boxes

def pick_polygons(m,polygons,lat,delthe=1.):
    """Optimizing on-land box recognition by choosing only land polygons having
    values within latitudes spanned by the box.

    Example:
        If we circle the equator, lat = 0, and the box has a mile side, 
        ~.9 degree:
            lats = [0,.9] 
        Greenland, for example, does not fall within this range, so do not check
        it.
    """
    lats = [lat-1.5,lat+1.5]
    lons = [0.,0.]
    x,y = m(lons,lats)

    polygons = polygons

    inds = list()
    for i,array in enumerate(polygons):
        if np.where(np.logical_and(array[:,1] > y[0],array[:,1] < y[1]))[0].any():
            inds.append(i)

    polygons = [Path(polygons[i]) for i in inds]
    return polygons

def poly_bool(pts,closed_paths):
    """Returns generator with one entry for each polygon indicating:
        True: points are contained within the closed paths in question;
        False: points are not contained within the closed paths.
    Generator can be used with any()/all() more efficiently.
    """
    # print("inside poly_bool")
    # print("removing .any()")
    # return (p.contains_points(pts).any() for p in closed_paths)
    return (p.contains_points(pts) for p in closed_paths)

def ocean_grid(plot=False,with_icoads=False):
    """Create plot for creating boxes of (nearly) equal side lengths.  The map
    plot is a visual representation of the most important part, the grid.  The
    grid is an indexed by the lower lefthand corner of the boxes. 

    Useful info:
        meters/mile = 1609.344
    """
    # Set up figure and map if plot=True
    if plot:
        fig = plt.figure()
        ax = fig.add_subplot(1,1,1)
        # Old map with hammer projection
        # m = Basemap(projection='hammer',lat_0=0.,lon_0=-180.,ax=ax)
        m = Basemap(projection='merc',llcrnrlat=-85,urcrnrlat=85,\
            llcrnrlon=-180,urcrnrlon=180,lat_ts=0.,resolution='c')
        m.drawcoastlines()
        # m.drawmeridians(np.arange(0,40,10.))
    else:
        m = Basemap(projection='hammer',lat_0=50.,lon_0=-40.)
    # get boundaries of all land polygons
    polygons = [p.boundary for p in m.landpolygons]
    # set up sql tables
    db_box.create_tables([Box,Latitude,Longitude,ObsData])
    # parameters for ocean grid
    lon_0 = -180.      # starting lat/lon
    lat_0 = -85
    del_lon = 360.     # lat/lon spanned
    del_lat = 170.
    box_size = 100000. # length of each side of box in meters
    # set up for loop
    d_box, d_lon = dict(), dict()    # dictionaries and lists sql insert 
    data_box, data_lon = list(), list()
    # d_
    upper_lat = lat_0 + del_lat
    all_vertices = list()
    check_verts = [1,2]
    lat = lat_0
    row, col = -1, -1

    number_of_boxes = 0
    number_near_land = 0

    while lat < upper_lat:
        d_box.clear()   # clear contents of dictionary for db insert
        d_lon.clear()
        row += 1    # latitude (row) 
        col = -1    # longitude (col)
        # return angular height, width, and the contiguous boxes
        delthe,delphi,boxes = lon_box_chain(
                    m,
                    size=box_size,
                    lon_0=lon_0,
                    lat_0=lat,
                    del_lon=del_lon,
                    upper_lat=upper_lat
                    )
        # subset of land polynomial within relevant lat range
        subpolys = pick_polygons(m,polygons,lat,delthe)
        with db_box.transaction():  # add latitude to grid
            latitude = Latitude.create(lat_box=lat,lat_index=row)
        # out atomic, acts as a transaction
        with db_box.atomic():
            for ibox,box in enumerate(boxes):
                x,y = m(box[0],box[1])
                vertices = list(zip(x,y))
                east_verts = [vertices[i] for i in [2,3]]

                col += 1                        # longitude index (col)
                name = str(row)+"_"+str(col)    # db name of box
                if col == 0:            # check western side of the box on land
                    containing_polygons = poly_bool(
                        [vertices[i] for i in [0,1]],subpolys
                        )
                    last_on_land_count = 0
                    for cp in containing_polygons:
                        if cp.any():
                            last_on_land_count = sum(cp)
                            break

                # keep if all box vertices are on water
                containing_polygons = list(poly_bool(east_verts,subpolys))
                next_on_land_count = 0
                for cp in containing_polygons:
                    if cp.any():
                        next_on_land_count = sum(cp)
                        break # only one polygon

                # count total vertices on land
                total_on_land_count = last_on_land_count + next_on_land_count

                # if vertices on land less than specified amount, keep them
                if total_on_land_count < 2:
                    
                    if total_on_land_count == 0:
                        number_of_boxes +=1 
                    else:
                        number_near_land +=1

                    # update box table values
                    d_box.update({'name':name ,
                              'box_x_coords':x.__repr__(),
                              'box_y_coords':y.__repr__(),
                              'box_lons':box[0].__repr__(),
                              'box_lats':box[1].__repr__(),
                              'box_side':box_size,
                              'on_land':False}
                            )
                    data_box.append(d_box.copy())

                    # update longitude table values
                    d_lon.update({'lat_box':latitude,
                               'lon_box':box[0][0],
                               'lon_index':col}
                            )
                    data_lon.append(d_lon.copy())

                    # add points to plot
                    if plot:
                        all_vertices.append(vertices)

                # update value, next become last on next iteration
                last_on_land_count = next_on_land_count
                if ibox % 100 == 0:
                    if data_box:
                        with db_box.atomic(): # insert rows atomically - savepoints
                            Box.insert_many(data_box).execute()
                            data_box[:] = []
                    if data_lon:
                        with db_box.atomic():
                            Longitude.insert_many(data_lon).execute()
                            data_lon[:] = []

            # next latitude
            lat = lat+delthe

            # pick up rest of unstored data
            if data_box:
                with db_box.atomic():
                    Box.insert_many(data_box).execute()
                    data_box[:] = []
            if data_lon:
                with db_box.atomic():
                    Longitude.insert_many(data_lon).execute()
                    data_lon[:] = []
    db_box.close()

    print("Total number of boxes off land: ", number_of_boxes)
    print("Total near land: ", number_near_land)
    print("Estimated area of ocean: ", (box_size/1000.)**2.*number_of_boxes)

    if plot:


        # show boxes on map
        coll = PolyCollection(all_vertices,facecolor='none',closed=True)
        ax.add_collection(coll)

        # show icoads data on map
        if with_icoads:
            data_coords = list()
            for data in IcoadsData.select():
                data_coords.append([data.lon_obs, data.lat_obs])
            lons,lats = zip(*data_coords)
            lons = map_lons(-180,180,lons)
            x,y = m(lons,lats)
            m.scatter(x,y,.0001,marker='o',color='b')

        # make plot
        plt.title("Box size {} km".format(str(box_size/1000.)))
        plt.show()

if __name__ == '__main__':
    ocean_grid(plot=True,with_icoads=False)

    

