from mpl_toolkits.basemap import Basemap, pyproj
from matplotlib.path import Path
from matplotlib.patches import Polygon
import matplotlib.patches as patches
from matplotlib.collections import PolyCollection
from observations_on_map import map_lons
from datetime import date
from time_series import *
import matplotlib.pyplot as plt
import numpy as np
import math
import transaction
import ast
import sys

# --------------- 
writing = False #  FLAG FOR OCEAN_BOX_TABLES
# ---------------  
from orm.ocean_box_tables import *
from plots import *
# from analysis import dense_boxes
# def populated_boxes(m,patches=False):
#     """Find boxes that have any data at all in them, add centers of these boxes
#     to the map.
#     """
#     # get ids of boxes that contain prescribed amount of data
#     distinct_box_q = str(
#         "select name " +
#         "from obsdata " + 
#         "group by name "  + 
#         "having count(name) > 5 "
#         "order by count(name) "  +
#         ";"
#     )
#     query_ids = db_box.execute_sql(distinct_box_q)
#     box_ids = list()
#     for q in query_ids:
#         box_ids.append(q[0])

#     # calculate percentage of sampled boxes
#     total_grid_boxes = Box.select().count()
#     query_length=len(box_ids)
#     print("Percent of ocean coverage = ",query_length/total_grid_boxes*100,'%')
#     sys.stdout.flush()    

#     if patches:
#         all_vertices = list()
#         for box in Box.select().limit(1000):
#             all_vertices.append(list(zip(ast.literal_eval(box.box_x_coords), 
#                 ast.literal_eval(box.box_y_coords))))
#         coll = PolyCollection(all_vertices,facecolor='r',closed=True)
#         ax.add_collection(coll)
#     else:
#         # get central coordinates of boxes
#         box_center_lons = list()
#         box_center_lats = list()
#         for box_id in box_ids:
#             for q in Box.select().where(Box.name==str(box_id)):
#                 box_center_lons.append(float(q.box_center_lon))
#                 box_center_lats.append(float(q.box_center_lat))

#         x,y = m(box_center_lons,box_center_lats)
#         m.scatter(x,y,.5,marker='o',color='g')

def reconstruct_grid(m,ax=None):
    all_vertices = list()
    for box in Box.select(box.box_x_coords,box.box_y_coords):
        all_vertices.append(list(zip(ast.literal_eval(box.box_x_coords), 
            ast.literal_eval(box.box_y_coords))))
    coll = PolyCollection(all_vertices,facecolor='w',closed=True)
    ax.add_collection(coll)

def populated_boxes(m,ax=None,num_pts=0,years=None):
    """Find the boxes that contain required data.  Then, add patches to map."""
    # select date range of data (by year for now)
    if years:
        query = years_query(years)
    else:
        # otherwise, select all data
        query = ObsData.select(ObsData.name)

    populated_boxes = list()
    for i,dat in enumerate(query.group_by(ObsData.name).having(
            fn.Count(ObsData.name)>num_pts).iterator()):
        for box in Box.select().where(Box.name==dat.name).iterator():
            populated_boxes.append(list(zip(ast.literal_eval(box.box_x_coords), 
                ast.literal_eval(box.box_y_coords))))
    coll = PolyCollection(populated_boxes,facecolor='r',closed=True)
    ax.add_collection(coll)
    return populated_boxes

def years_query(years):
    """Perform query on obsdata for a given range of years and on specific
    'name' fields.
    """
    date_min = date(years[0],1,1)
    date_max = date(years[-1],12,31)
    return ObsData.select().where(ObsData.date.between(date_min,date_max))

def data_coordinates(num_pts=0,years=None):
    # data_query = ObsData.select().group_by(ObsData.name).having(
    #     fn.Count(ObsData.name)>num_pts).naive().dicts()
    # account for year selection in the query, if there is any
    if years:
        data_query = years_query(years)
    for dat in data_query.iterator():
        yield dat['lon_obs'], dat['lat_obs']

def plot_data(m,years=None):
    try:
        lons,lats = list(zip(*data_coordinates(years=years)))
        x,y = m(lons,lats)
        m.scatter(x,y,s=.5,marker='*',facecolor='b')
    except:
        pass

def process_years(years):
    """Utility to handle different inputs for years and generate title of 
    plot.
    """
    if isinstance(years,(list,tuple)):
        years = tuple(sorted(years))
        if years[0] == years[-1]:
            title_dates = str(years[0])
        else:
            title_dates = str(years[0])+" - "+str(years[-1])
    else:
        title_dates = str(years)
        years = (years,years)

    return years,title_dates




def mark_predom_boxes(m, ax=None,limit=5,years=None):
    """Mark boxes that are most predominant on the map."""
    date_min = date(years[0],1,1)
    date_max = date(years[-1],12,31)
    
    # query most populated boxes
    subquery = (ObsData
        .select(ObsData.name)
        .where(ObsData.date.between(date_min,date_max))
        .group_by(ObsData.name)
        .order_by(-fn.Count(ObsData.name))
        .limit(limit)
        .alias('subquery')
    )
    
    # main query on time and most populated boxes
    query = (ObsData
        .select()
        .join(subquery, on=(ObsData.name==subquery.c.name))
        .where(ObsData.date.between(date_min,date_max)
    ))

    # for sq in subquery:
    #     print(sq.name)
    # print(list(subquery))
    # print(len(list(query)))


def map_boxes(m,boxes,ax=None,centers=False,color='r'):
    """Specify box names, put them on the map."""
    all_boxes = list()
    lons = list()
    lats = list()
    for box_name in boxes:
        # print(box_name)    
        sql = "select box_x_coords,box_y_coords,box_center_lon,box_center_lat "\
        + "from box "\
        + "where name = '{}';".format(box_name)
        try:
            box_x_coords,box_y_coords,lon,lat = zip(*db_box.execute_sql(sql))
            all_boxes.append(list(
                zip(ast.literal_eval(box_x_coords[0]),ast.literal_eval(box_y_coords[0]))
                )
            )
            lons.append(lon[0])
            lats.append(lat[0])
        except:
            pass
    coll = PolyCollection(all_boxes,facecolor=color,closed=True)
    ax.add_collection(coll)
    # map the center of box marker
    if centers == True:
        x,y = m(lons,lats)
        m.scatter(x,y,s=100,alpha=.5)
    return all_boxes

def map_single_box_dist(names,years,m,ax=None,f=2.):
    # names should be iterable
    if not isinstance(names,(list,tuple)):
        names = [names]

    # plot boxes and get vertices
    vertices = map_boxes(m,names,ax=ax)

    # centering plot on box close-up
    for i,v in enumerate(vertices):
        x,y = zip(*v)
        if i == 0:
            xmin=min(x)
            xmax=max(x)
            ymin=min(y)
            ymax=max(y)
        else:
            xmin=min(min(x),xmin)
            xmax=max(max(x),xmax)
            ymin=min(min(y),ymin)
            ymax=max(max(y),ymax)
    w=xmax-xmin
    h=ymax-ymin
    plt.axis(
        [(xmin+w/2)-f*w/2,(xmax-w/2)+f*w/2,(ymin+h/2)-f*h/2,(ymax-h/2)+f*h/2]
    )

    # for each box, map all data contained in it
    m.drawcoastlines()
    for name in names:
        lons,lats = data_locations(name,years)
        print(name, len(lons))
        # print(lons,lats)
        sys.stdout.flush()
        m.scatter(*m(lons,lats))

def make_plot(m,boxes=None,ax=None,data=False,patches=False,grid=False,coast=True,
        years=None,top_pop=None):
    """Main function for creating maps with various flagged options."""

    # preprocess years
    if years:
        years,title_dates = process_years(years)

    # set up inital title
    box_size = Box.select(Box.box_side).limit(1).scalar()
    title = '{}, Box Size of {} km'.format(title_dates,box_size/1000.)

    # draw coastline
    if coast == True:
        m.drawcoastlines()

    # recreate grid for map
    if grid == True:
        reconstruct_grid(m,ax1)
        x,y = m(12.85,55.6)
        m.scatter(x,y,s=40,alpha=.5)

    # add patches of populated boxes
    if patches == True:
        # percentage of ocean sampled
        num_patches = len(populated_boxes(m,ax,years=years))
        tot_boxes = Box.select(Box.id).order_by(-Box.id).limit(1).scalar()
        print(num_patches,tot_boxes)
        percentage = (num_patches/tot_boxes)*100.

        # set up map title
        title = title+', {}% Sampled'.format(round(percentage,2))
    
    # add data points to the plot
    if data == True:
        plot_data(m,years)

    if top_pop:
        mark_predom_boxes(m,ax=ax,limit=top_pop,years=years)

    if boxes:
        map_boxes(m,ax,boxes)

    # set map title
    ax.set_title(title)

    plt.show()



if __name__ == '__main__':

    # data = False
    # patches = False
    # grid = False
    # top_pop = False
    # # years = (1861,1861)
    # years = (1861,1890)
    # boxes = ['1504_1221','494_1813','739_1853']
    # ('1568_1069', '1504_1221', '494_1813', '494_1822', '505_1881', '505_1862', '505_1890', '739_1853', '494_1804', '728_1856')
    # set up figure
    # make_plot(m,boxes,ax1,data=data,patches=patches,grid=grid,years=years,
        # top_pop=top_pop)

    fig = plt.figure()
    ax1 = fig.add_subplot(1,1,1)

    # set up map
    m = Basemap(projection='merc',llcrnrlat=-85,urcrnrlat=85,\
            llcrnrlon=-180,urcrnrlon=180,lat_ts=0.,resolution='c',ax=ax1)
    m.drawcoastlines()

    yr = 1883
    years = (yr,yr)
    name = '739_1853'
    hmonth = 1
    pentads = conv_hmth_pentad(hmonth)
    radius = 1000.

    keep,throw,ratio = corr_radius_boxes(name,radius,years,hmonth=hmonth)
    print(len(keep))
    print(len(throw))
    print(ratio)
    sys.stdout.flush()

    map_boxes(m,keep,ax=ax1,color='blue')
    map_boxes(m,throw,ax=ax1,color='red')
    
    plt.show()