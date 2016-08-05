from peewee import *

db = SqliteDatabase('ocean_data.db')

class BaseModel(Model):
    class Meta:
        database = db

class Box(BaseModel):
    name = CharField()
    x_coords = CharField()
    y_coords = CharField()

    class Meta:
        # primary_key = False
        order_by = ('name',)

if __name__ == '__main__':
    print(db)