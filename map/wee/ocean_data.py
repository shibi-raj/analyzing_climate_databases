from peewee import *

db = SqliteDatabase('ocean_data.db')

class BaseModel(Model):
    class Meta:
        database = db

class Box(BaseModel):
    """Class assigning data fields to each box row."""
    name = CharField()      # id of box: (lat_index)_(lon_index)
    x_coords = CharField()  # projected map coordinates
    y_coords = CharField()
    lons = CharField()      # geographic coordinates of box corners
    lats = CharField()
    area = CharField(null=True) # box area
    # Sea-surface temperature, will get this value from ICOADS
    sst = CharField(null=True)
    class Meta:
        # primary_key = False
        order_by = ('name',)

class GridPoint(BaseModel):
    """Store of ocean grid created in ocean_sampling module.
    For each unique latitude a row of boxes are created longitudinally, hench
    latitude is a unique key.
    """
    latitude = CharField(unique=True)
    lat_index  = IntegerField()
    class Meta:
        order_by = ('latitude',)

class Longitude(BaseModel):
    lat = ForeignKeyField(GridPoint)
    lon = CharField()
    lon_index = IntegerField()
    on_land = BooleanField()
    class Meta:
        order_by = ('lon',)

if __name__ == '__main__':
    if not GridPoint.table_exists():
        db.create_table(GridPoint)

    try:
        with db.transaction():
            latitude = GridPoint.create(
                latitude=0.12
            )
    except IntegrityError:
        flash('That latitude is already taken.')

    if not Longitude.table_exists():
        db.create_table(Longitude)

    with db.transaction():
        Longitude.create(lat=latitude,lon=0.13)

    query = Longitude.select().join(GridPoint).where(GridPoint.latitude == 0.12)
    for each in query:
        print (each.lon)