from peewee import *

db_box = SqliteDatabase('data_sets/databases/ocean_box_data.db',
    pragmas=(
    ('journal_mode', 'WAL'),
    ('cache_size', 980000),
    ('synchronous',0),
    ('mmap_size', 1024 * 1024 * 32),
    )
)

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
    name = CharField(primary_key=True)      
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
    """For each unique latitude a row of boxes are created longitudinally.
    Hence, the latitude index is a unique for each row of longitude boxes.
    """
    lat_box = FloatField() # the ll corner latitude of box
    lat_index  = IntegerField(primary_key=True) # latitude index integer
    class Meta:
        order_by = ('lat_box',)

class Longitude(BaseModel):
    """Longitude boxes reference their fixed latitude value.  'name' is also
    specified longitude index created.
    """
    #       reference to Box
    name = ForeignKeyField(Box,to_field='name',related_name='longitudes') 
    # lat_box = ForeignKeyField(Latitude,related_name="longitudes") # ref Latitude
    lon_box = FloatField() # the ll corner longitude of box
    lon_index = IntegerField() # longitude index
    
    # temporary modifications
    lat_index = ForeignKeyField(Latitude,to_field='lat_index',related_name="longitudes") # ref Latitude

    class Meta:
        order_by = ('lon_box',)

class ObsData(BaseModel):
    """Observational data."""
    name = ForeignKeyField(Box,to_field='name',related_name='data')
    lat_obs = FloatField()
    lon_obs = FloatField()
    sst = FloatField()
    date = DateField()
    pentad = IntegerField(null=True)
    half_mth = IntegerField(null=True)

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
