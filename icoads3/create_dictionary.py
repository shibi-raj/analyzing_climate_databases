#!/usr/bin/python3
"""
Set of functions to create and write out to file a nested dictionary called
'stored_dictionary.json'.  The main keys of the dictionary are fields according
to the IMMA convention, laid out in the file 'imma.txt'.  The nested 
dictionaries contain meta data for that particular field, described as follows:
    id: IMMA field id
    description: field description (see imma.txt)
    length: # of spaces field occupies in the data text line
    position: position of the field in the data text line

Creates dictionary in two parts.  First, add_first_fields() sets up the main key
with nested dictionary containing ['id','length','description'].  Then,
add_position_field() does what it says using the 'length' field from the first
step.

Write the dictionary to file, 'stored_dictionary.json', using function 
write_dict().


Examples of key and nested dictionary:
    YR {'id': '1', 'description': 'year UTC 1600 2024 (AAAA)', 'length': '4', 
        'position': [0, 4]}
    MO {'id': '2', 'description': 'month UTC1 1 12 (MM)', 'length': '2', 
        'position': [4, 6]}
    SST {'id': '35', 'description': 'sea surface temp. –99.9 99.9 0.1°C (∆ sn, 
          TwTwTw)', 'length': '4', 'position': [85, 89]}
"""
import json

def add_first_fields():
    """Process input file and create nested dictionary with its info."""
    with open('imma.txt','r') as f:
        d = dict()
        # order for rearranging input, description fields added in a bit
        order = [2,0,1] 
        # keys for nested dictionary => to 0,1 in order, + description field 
        # follows
        labels = ['id','length','description']
        for line in f.readlines():
            try:
                rearrange = []
                if not line[0].isalpha():
                    line_split = line.split()
                    rearrange = [line_split[i] for i in order]
                    rearrange.append(" ".join(line_split[3:]))
                    d_nest = dict((key,value) for (key,value) in \
                             zip(labels,rearrange[1:]))
                    d[rearrange[0]] = d_nest
            except:
                pass
    return d

def add_position_field(d):
    """Adds position field to the stored dictionary, derived from the 'length'
    field already contained in it.
    """
    sorted_keys = sort_keys(d)
    for key in sorted_keys:
        d[key]['position'] = get_position(key,sorted_keys,d)
    return d

def get_position(key,sorted_keys,d):
    """Return the key's space position interval in the line."""
    start_pos = 0
    for sk in sorted_keys:
        if sk == key:
            break
        else:
            start_pos += int(d[sk]['length'])
    end_pos = start_pos + int(d[key]['length'])
    pos = [start_pos,end_pos]
    return pos

def sort_keys(d):
    """Return keys of dictionary sorted accorded to 'id', found in nested 
    dictionary.
    """
    return sorted(d,key=lambda x: int(d[x]['id']))

def print_sorted_dict(d):
    """Print out the dictionary with keys in order according to imma.txt."""
    sorted_keys = sort_keys(d)
    for key in sorted_keys:
        print(key,d[key])
        # print(key,get_position(key,sorted_keys,d))

def write_dict(d,filename='icoads3/lib/stored_dictionary.json'):
    """Write out the dictionary in JSON format"""
    with open(filename,'w') as f:
        json.dump(d,f)

def check_dump(filename='icoads3/lib/stored_dictionary.json'):
    """Verify dictionary contents match those in 'imma.txt'."""
    with open(filename,'r') as f:
        try:        
            d = json.load(f)
            for each in d:
                print(each,d[each])
        except Exception as e:
            print(e)

def create_dict():
    d = add_first_fields()
    d = add_position_field(d)
    print_sorted_dict(d)
    write_dict(d)



"""
Create persistent dictionary of varied yearly time intervals: months, 
half-months, half-month dates, and pentads.  Given a date, the dictionary will 
be accessed with another routine to return the corresponding pentad.

Example:
    
    date(March 4, 2011):
        March 
        -> month '3': 
                {
                '5': {
                        'pentads': [13, 14, 15, 16], 
                        
                        'dates': [datetime.date(2016, 3, 2), 
                                datetime.date(2016, 3, 21)]
                }
                '6': {
                        'pentads': [17, 18, 19], 
                        'dates': [datetime.date(2016, 3, 22),
                                  datetime.date(2016, 4, 5)]
                }
        -> 'pentads': [13, 14, 15, 16]
        -> pentad 13
      
      }

Note: to make datetime.date work, all fields (year,month,day) are required.  The 
time intervals do not depend on the year, so the year occuring in the code is 
arbitrarily set to 2016.  Made sure to choose a leap year so as to account for
the date February 29 to be used as an input, and its pentad returned.
"""
from datetime import date, datetime, timedelta

def yearly_time_intervals():
    """Function for creating yearly time intervals for analysis purposes.  Data
    to be stored in nested dictionary, and the dates are converted to strings
    for serialization.  


    Nested dictionary key:value structure:

        month number key:

            half-month number key:

                dates key: list of beginning and end dates of half-month period
                       list(datetime beg, datetime end) 

                pentads key: list of pentad indices corresponding to the 
                        half-month, mostly 3 per half-month, except in March.

    Supplemental functions:
        
        create_yearly_intervals(): write dictionary to file 
        
        load_yearly_intervals(): fetch dictionary, convert date strings to
            datetime.date objects
    """
    this_date = date(2016,1,1) # arbitrary
    d_month = dict()
    d_hmonth = dict()
    d_intervals = dict()

    delta = timedelta(days=14)
    one_day = timedelta(days=1)

    # initilize loop
    next_year = this_date.year + 1
    pentads = [-2,-1,0]
    month = -1
    halfmonth = 0
    while this_date.year < next_year:
        month = halfmonth//2 + 1

        halfmonth += 1
        
        beg = this_date
        end = this_date + delta
        pentads = [p+3 for p in pentads[-3:]]
        
        # February and March have pentad irregularities, 
        #   see Table A1.1 Bottomley
        if beg.month == 2 and beg.day == 15:
            end = end.replace(day=1)
            end = end.replace(month=3)

        if beg.month == 3 and beg.day == 2:
            end = end.replace(day=21)
            pentads.append(pentads[-1]+1)

        d_intervals['pentads'] = pentads
        d_intervals['dates'] = [beg.__str__(),end.__str__()]
        if halfmonth % 2 == 1:
            d_hmonth.clear()
            d_hmonth[str(halfmonth)] = d_intervals.copy()
        else:
            d_hmonth[str(halfmonth)] = d_intervals.copy()
            d_month[str(month)] = d_hmonth.copy()

        this_date = end + one_day
    return d_month

def load_yearly_intervals(filename='icoads3/lib/yearly_time_intervals_store.json'):
    """Load dictionary containing the correspondence of the different varied
    intervals, e.g., pentads, half-months, etc.  

    Note: the datetime objects were not serializable, so they were converted to
    strings when written to file.  Below, they are returned to datetime.date
    objects.
    """

    with open(filename,'r') as f:
        try:        
            d = json.load(f)
        except Exception as e:
            print(e)

    # convert dates in dictionary to datetime.date objects
    for month in d:
        for half_month in d[month]:
            d[month][half_month]['dates'][0] = datetime.strptime(
                d[month][half_month]['dates'][0],'%Y-%m-%d').date()
            d[month][half_month]['dates'][1] = datetime.strptime(
                d[month][half_month]['dates'][1],'%Y-%m-%d').date()
    return d

def create_yearly_intervals():
    "Write yearly time interval dictionary to file."
    filename = 'lib/yearly_time_intervals_store.json'
    d = yearly_time_intervals()
    write_dict(d,filename)
    print(load_yearly_intervals(filename))


if __name__ == '__main__':
    # 1st: imma dictionary
    # check_dump() # can be called on stored dictionary without an argument
    # # create_dict()   # recreate the dictionary if desired

    # 2nd: yearly time interval dictionary
    print(load_yearly_intervals()) # run to print dictionary contents
    # # create_yearly_intervals() # recreated dictionary if desired