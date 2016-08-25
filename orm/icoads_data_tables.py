from peewee import *
import os

db_file = 'icoads_1861_1870.db'
db_obs = SqliteDatabase(db_file)

class BaseModel(Model):
    class Meta:
        database = db_obs

class IcoadsData(BaseModel):
    latitude  = FloatField()
    longitude = FloatField()
    sea_surface_temp = FloatField()
    date = DateField()
    pentad = IntegerField(null=True)
    half_mth = IntegerField(null=True)