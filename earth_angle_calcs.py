"""Set of codes for determining properties of boxes defined by angle, rather
than by distance."""
from mpl_toolkits.basemap import Basemap, pyproj
from ocean_grid_overlay import make_box
import math

def factors(n=90): 
    """Return list of factors of an integer."""   
    return list([i, n//i] for i in range(1, int(n**0.5) + 1) if n % i == 0)

def search_factors(degrees,n=90):
    """Look for integer, n, in the list of factors and return the sublist."""
    factor_list = factors(n)
    for sublist in factor_list:
        for item in sublist:
            if degrees == item:
                return sublist
    raise ValueError('The value, {}, is not allowed.  '.format(degrees) +
        'An allowed value must exist somewhere in the following list: {}'
        .format(factors()))

def latitude_divide(degrees,matching_factors):
    """Find the number of boxes of width 'degrees' between 0 and 90 degrees 
    latitude.
    """
    return [mf for mf in matching_factors if mf != degrees][0]

def global_box_count(degrees,number_in_ninety):
    """Given degrees and number of boxes in string from 0 to 90 lat, get total
    box count.
    """
    # square for number of boxes in patch of 90 degrees in both lat and lon
    number_boxes = number_in_ninety*number_in_ninety
    # multiply by 2 for southern hemisphere and 4 around the globe
    number_boxes = 2 * 4 * number_boxes
    return number_boxes

def areas_of_boxes(degrees,number_boxes):
    """Return area of a total number of boxes, 'number_in_ninety', from 0 to 90 
    latutide of size, 'degrees'."""
    r_earth = 6371
    latitude = 0.
    areas = list()
    latitudes = list()
    delphi = degrees*math.pi/180.
    for i in range(1,number_boxes+1):
        next_lat = i*degrees*math.pi/180.
        area = r_earth*r_earth*delphi*(math.sin(next_lat)-math.sin(latitude))
        areas.append(area)
        latitudes.append(latitude*180./math.pi)
        # set start latitude for next box
        latitude = next_lat
    return areas,latitudes

def area_stats(areas):
    """Return average area of input boxes spanning from 0 to 90 latutide."""
    area_dict = dict()
    
    # get number of boxes
    total_areas = len(areas)
    
    # calculate average
    average_area = sum(areas)/total_areas
    area_dict['average'] = average_area
    
    # calculate std_dev
    devs = [(area-average_area)**2. for area in areas]
    variance = sum(devs)/total_areas
    std_dev = variance**.5
    area_dict['std_dev'] = std_dev
    
    # calculate min and max areas
    max_area = max(areas)
    min_area = min(areas)
    area_dict['min'] = min_area
    area_dict['max'] = max_area
    return area_dict


def haversine(lon1,lat1,lon2,lat2):
    """Calculate the great circle distance between two points on the earth 
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

def box_side_dist(box_lons,box_lats,e=True,n=True,w=True,s=True):
    
    pts = list(zip(box_lons,box_lats))

    sides = [[e,0,1],[n,1,2],[w,2,3],[s,3,0]]
    
    side_dist = list()
    for side in sides:
        if side[0]:
            side_pts = list()
            side_pts.extend(pts[side[1]])
            side_pts.extend(pts[side[2]])
            # print(side_pts)
            side_dist.append(haversine(*side_pts))
    
    return side_dist


def box_sides(degrees, lats):
    """Calculate the lengths of the sides of the string of boxes spanning 0 to
    90 degrees in set of latitudes, 'lats', and each side passing through angle, 
    'degrees'.
    """
    # m = Basemap(projection='cyl',llcrnrlat=-90,urcrnrlat=90,\
    #     llcrnrlon=-180,urcrnrlon=180,resolution='c')
    m = Basemap(projection='hammer',lat_0=50.,lon_0=-40.)
    angle = degrees*math.pi/180.


    e = True
    n = True
    w = True
    s = True
    dict_sides = dict()
    for i in range(len(lats)):
        box_lons,box_lats = make_box(m,0,lats[i],degrees,degrees)
        pts = list(zip(box_lons,box_lats))
        

        if i == 0:
            east, north, west, south = box_side_dist(box_lons,box_lats)
            dict_sides[str(i)] = [lats[i],east,north,west,south]
            south = north
            continue
        
        # calculate 
        north = box_side_dist(box_lons,box_lats,
            e=False,n=True,w=False,s=False)[0]

        dict_sides[str(i)] = [lats[i],east,north,west,south]
        south = north

    return dict_sides

def main(degrees,n=90):
    """Routines to get quantities of interest for boxes defined by degrees as
    opposed to lengths.
    """
    # get matching factor of degrees that multiplies to make 90
    matching_factors = search_factors(degrees)
    number_in_ninety = latitude_divide(degrees,matching_factors)
    
    # get the total number of boxes of size, 'degrees', around the globe
    number_boxes = global_box_count(degrees,number_in_ninety)
    
    # get latitudes and areas of boxes from 0 to 90 degrees latitude
    areas,lats = areas_of_boxes(degrees,number_in_ninety)

    # get statistics of areas ranging from 0 to 90 degrees latitude
    stats = area_stats(areas)
    print(
        'average: {},  std. dev.: {},'.format(stats['average'],stats['std_dev']) 
        +'  max: {},  min: {}'.format(stats['max'],stats['min']) 
    )

    # produces the lengths of sides of the boxes spanning 0 to 90 latitude 
    dict_sides = box_sides(degrees,lats)
    # for i in range(len(lats)):
    #     print(dict_sides[str(i)][2],dict_sides[str(i)][4])


if __name__ == '__main__':
    degrees = 6
    main(degrees)