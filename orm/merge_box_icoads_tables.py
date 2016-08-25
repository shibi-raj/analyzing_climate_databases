from peewee import *

db_merge = SqliteDatabase('databases/box_and_obs.db')
# print('hell', db_merge)

class BoxObs(Model):
    """Final database for merging observational data and box data."""
    # Box data
    box_index = CharField()
    x_coords = CharField()  
    y_coords = CharField()
    lons = CharField()      
    lats = CharField()
    area = FloatField(null=True) 
    on_land = BooleanField()
    
    # Observational data
    lat_obs = FloatField()
    lon_obs = FloatField()
    sst = FloatField()
    date = DateField()
    pentad = IntegerField(null=True)
    half_mth = IntegerField(null=True)

    class Meta:
        database = db_merge
