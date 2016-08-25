from peewee import *
import os

db_obs = SqliteDatabase('databases/icoads_1861_1870.db')

class BaseModel(Model):
    class Meta:
        database = db_obs

class IcoadsData(BaseModel):
    lat  = FloatField()
    lon = FloatField()
    sst = FloatField()
    date = DateField()
    pentad = IntegerField(null=True)
    half_mth = IntegerField(null=True)