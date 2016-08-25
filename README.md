ANALYZING CLIMATE DATABASES
===========================

Python codes for climate data modeling and analysis


Observational data
==================

create_icoads_database.py:

    Main code for storing climate data in database.  

    location: analyzing_climate_databases/

    Current data sets: ICOADS 3.0.0


icoads_data_tables.py:

    ORM for icoads data.

    location: analyzing_climate_databases/orm/


Map box data
============

ocean_grid_overlay.py:

    location: analyzing_climate_databases/

    Main code for generate boxes over ocean of prescribed size.

    To do:
        Need to keep partial areas for boxes that overlap ocean and land?

        Numpy: index each box - should contain:
            (ids, coordinates, area)

ocean_box_tables.py:

    location: analyzing_climate_databases/orm/

    ORM code for storing box data in database


Merging box data and observational data
=======================================

merge_box_obs.py

    location: analyzing_climate_databases/

    Contains box_lookup(), a function to locate a box by lat/lon in order to store observational data in that box 

merge_box_icoads_tables.py:

    location: analyzing_climate_databases/orm/

    ORM code for merging ICOADS data and box data into a single database


Updates
=======

    8/25/2016
        Restructuring: moving main modules to the top level and renamed:
            ocean_sampling.py --> ocean_grid_overlay - creates grid 
            cover over the ocean

            get_icoads_data --> create_icoads_database.py - main 
            feature, extracts data from the icoads data set and loads 
            it into a database

            merge_box_obs.py - merges the ocean grid cover data with 
            icoads data

        Restructuring: moved all orm table files to single folder, orm

        Restructuring: all databases now created under single folder, 
        databases

    7/27/2016
        Tried optimization by using continent data at restricted latitude as 
        foreknowledge when placing boxes.  No need for this, checking whether in
        polygons is simple enough and not computationally heavy.  Tried first 
        with coast data, too complicated.

    7/26/2016
        Added optimizations
        Timing benchmark (without showing plot):
        • parameters
            lon_0 = 0.
            lat_0 = -45.
            del_lon = 90.
            del_lat = 90.0
            box_size = 1600.
        • No face color on boxes & without showing plot:  27.3 s
        • With PolyCollection instead of Polygon: 24.1 s
        • Replaced projected coordinates zip with np.dstack: 23.6
    
    7/25/2016
        Added logic so boxes only appear on oceans, not land
        Boxes drawn in spherical coordinates, 1 mile on each of three sides, most
        northern depends on latutide

To do
=====


