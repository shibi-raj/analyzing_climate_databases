#!/usr/bin/env/python3
"""Set of functions to put equal area boxes on the worlds' oceans.  

Updates:
    
    7/25/2016
    Added logic so boxes only appear on oceans, not land
    Boxes drawn in spherical coordinates, 1 mile on each of three sides, most
        northern depends on latutide

To do:
    Optimize land recognition
    Numpy: index each box - should contain:
        (ids, coordinates, area)
    May need partial areas for boxes that overlap ocean and land    
"""
from mpl_toolkits.basemap import Basemap, pyproj
from matplotlib.patches import Polygon
from matplotlib.collections import PolyCollection
from matplotlib.path import Path
import matplotlib.patches as patches

import matplotlib.pyplot as plt
import numpy as np
import math

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

def make_patch(proj,lon,lat,delphi,delthe):
    """Given the location of the lower-left corner of a patch and the length of
    the sides, calculate the coordinates of a square patch at that location.
    
    Args:
        lon: longitude ll corner
        lat: latitude ll corner
        side: length of side of the square patch
    """
    aug_lon = lon+delphi
    aug_lat = lat+delthe
    pt00 = [lon,lat]
    pt01 = [lon,aug_lat]
    pt10 = [aug_lon,lat]
    pt11 = [aug_lon,aug_lat]
    pts = [pt00,pt01,pt11,pt10]
    lons,lats = zip(*pts)
    lons = list(lons)
    lats = list(lats)
    return lons,lats

def lon_box_chain(proj,lat,del_lon,size,lon_0=0.):
    """Create adjoining boxes same latitude through specified longitudinal 
    angle.  Boxes start at Prime Meridian and travel East.
    """
    # Calculate increment of longitude, delta phi
    R = 6371000.
    delphi = size/R*math.cos(lat*math.pi/180.)
    delphi = delphi*180/math.pi

    # Calculate increment in latitude, delta theta
    delthe = size/R
    delthe = delthe*180/math.pi

    # print('angle increments',delphi,delthe,math.cos(lat*math.pi/180)*delphi)

    # Same for angles
    lons = lon_0 + np.arange(0.,del_lon,delphi)
    lats = [lat for lon in lons]
    pts = list(zip(lons,lats))
    boxes = list()
    for pt in pts:
        boxes.append(make_patch(proj,pt[0],pt[1],delphi,delthe))
    return boxes

def main():

    fig = plt.figure()
    ax = fig.add_subplot(1,1,1)

 
    m = Basemap(projection='hammer',lat_0=50.,lon_0=-40.,ax=ax)
    # m = Basemap(projection='merc', resolution='c')
    m.drawcoastlines()
    m.fillcontinents(color='coral')
    m.drawmeridians(np.arange(0,40,10.))

    # Parameters for contiguous boxes
    lon_0 = 0.
    lat_0 = 0.
    del_lon = 50.
    box_size = 10000.

    boxes = lon_box_chain(m,lat_0,del_lon,box_size,lon_0)
    polygons = [Path(p.boundary) for p in m.landpolygons]

    # View individual continent polygon patches
    # poly = patches.PathPatch(polygons[6], facecolor='b', lw=2)
    # ax.add_patch(poly)

    all_boxes = list()
    for box in boxes:
        # Get x,y from lon,lat of box corners
        x,y = m(box[0],box[1])
        vertices = tuple(zip(x,y))

        # Set up generator of booleans for continental intersection
        poly_bool = (p.contains_points(vertices).any() for p in polygons)
        if not any(poly_bool):
            # all_boxes.append(box)
            coll = Polygon(vertices,closed=True)
            ax.add_patch(coll)
    plt.show()

if __name__ == '__main__':

    main()