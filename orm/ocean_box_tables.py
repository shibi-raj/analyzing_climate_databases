from peewee import *

db_box = SqliteDatabase('data_sets/databases/ocean_box_data.db')

class BaseModel(Model):
    class Meta:
        database = db_box

class Box(BaseModel):
    """Class assigning data fields to each box row.
    
    Variable definitions:
        name: string id of box, (lat_index)_(lon_index)
        x_coords/y-coords: projected map coordinates of box corners
        lons/lats: geographic coordinates of box corners
        area: area of given box
        sst: sea-surface temperature, to be filled from ICOADS data
    """
    name = CharField()      
    box_x_coords = CharField()  
    box_y_coords = CharField()
    box_lons = CharField()      
    box_lats = CharField()
    box_area = FloatField(null=True) 
    box_side = FloatField() 
    on_land = BooleanField(default=True) 
    class Meta:
        order_by = ('name',)

class Latitude(BaseModel):
    """Store of ocean grid created in ocean_sampling module.
    
    For each unique latitude a row of boxes are created longitudinally, hence
    latitude is a unique key.
    """
    # the latitude, fixed for chain of boxes along the latitude
    lat_box = FloatField()
    # integer index for the latitude which is a float
    lat_index  = IntegerField(unique=True)
    class Meta:
        order_by = ('lat_box','lat_index',)

class Longitude(BaseModel):
    lat_box = ForeignKeyField(Latitude, related_name="longitudes")
    lon_box = FloatField()
    lon_index = IntegerField()
    class Meta:
        order_by = ('lon_box','lon_index',)


if __name__ == '__main__':

    """
    !!! 
        For this example to work, you have to reset the database folder in
        'db_box' to the right one: '../data_sets/databases/ocean_box_data.db'. 

        Make to set it again properly when done!
    !!!
    """

    # Example: measurement taken at following coordinates
    lat_obs = 5.0
    lon_obs = -150.0
    print('coordinates: ', lat_obs,lon_obs)

    # retrieve latitude index
    i_lat = Latitude.select(Latitude.lat_index).where(
        Latitude.lat_box > lat_obs).limit(1).scalar() - 1
    
    # get latitude object corresponding to that index
    latitude = Latitude.get(Latitude.lat_index == i_lat)

    # now, retrieve longitude index
    for lon in latitude.longitudes:
        if lon.lon_box > lon_obs:
            i_lon = lon.lon_index-1
            break

    # create 'name' from the lat and lon indices
    name = "_".join([str(i_lat),str(i_lon)])
    print('name: ',name,'\n')

    for box in Box.select(Box.box_lons,Box.box_lats).where(Box.name==name):
        print(lat_obs,lon_obs)
        print('box lats: ',box.box_lats)
        print('box lons: ',box.box_lons)
