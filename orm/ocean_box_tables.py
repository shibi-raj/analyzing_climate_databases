from peewee import *

db_box = SqliteDatabase('databases/ocean_box_data.db')

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
    x_coords = CharField()  
    y_coords = CharField()
    lons = CharField()      
    lats = CharField()
    area = FloatField(null=True) 
    sst = FloatField(null=True)  
    class Meta:
        order_by = ('name',)

class GridPoint(BaseModel):
    """Store of ocean grid created in ocean_sampling module.
    
    For each unique latitude a row of boxes are created longitudinally, hench
    latitude is a unique key.
    """
    lat_box = FloatField(unique=True)
    lat_index  = IntegerField()
    class Meta:
        order_by = ('lat_box','lat_index',)

class Longitude(BaseModel):
    lat_box = ForeignKeyField(GridPoint)
    lon_box = FloatField()
    lon_index = IntegerField()
    on_land = BooleanField()
    class Meta:
        order_by = ('lon_box','lon_index',)


if __name__ == '__main__':
    i_lon,i_lat = box_lookup(4.,-3.6)
    name = str(i_lat)+'_'+str(i_lon)
    
    Box.update(sst=1.8).where(Box.name==name).execute()
    
    for b in Box.select().where(Box.name==name):
        print(b.sst,b.name,b.lons,b.lats)
    
    db_box.close()

