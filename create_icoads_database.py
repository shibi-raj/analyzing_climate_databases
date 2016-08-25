#!/usr/bin/python3
"""These are a set of functions that extract the data from an ICOADS data set.

The code relies on an external dictionary called 'stored_dictionary.json.'
The dictionary has the fields names as keys, e.g. 'YR', 'SST', etc., and the
corresponding value is a dictionary with keys 'id,' 'length,' and 'description.'

Note: data fields are incomplete:
The code relies on an external dictionary called 'stored_dictionary.json,'
produced in 'create_dictionary.py.'  This dictionary relies on the input from
'imma.txt,' which is, at this time, a truncated list of variables taken from the 
full list in 'R3.0-imma1_short.pdf.' To add more variables, copy and paste them
from the latter into the former, then run 'create_dictionary.py.'

Note: inefficiency in finding field position
Positions of fields should be stored in a separate file, such as the 
'stored_dictionary.json' file described above.  Currently, each time a field is
requested from the input file, e.g., 'SST', the position is recalculated each 
time, and, thus, very inefficient.
"""
from os import walk
from orm.icoads_data_tables import *
from icoads3.create_dictionary import load_yearly_intervals
from datetime import date, datetime, timedelta
from dateutil import relativedelta
import json
import logging

data_location = 'data_sets/icoads3.0.0/'

def load_dict():
    """Load dictionary, stored_dictionary.json, of metadata according to 
    imma.txt.
    """
    with open('icoads3/lib/stored_dictionary.json','r') as f:
        try:        
            d = json.load(f)
        except Exception as e:
            print(e)
    return d

def key_pos(key,d):
    """Uses the dictionary derived from 'stored_dictionary.json' to retrieve the 
    line positions, [begin,end], of the value of a key.
    """
    return d[key]['position']

def add_decimal(value,dposition):
    """Add decimals to compact IMMA fields."""
    if not value:
        return
    negative = False
    if value and value[0] == '-':
        negative = True
        value = value[1:]
    if 0 < len(value) < 3:
        value = value.zfill(3)
    if negative:
        value = '-'+value
    return value[0:dposition]+'.'+value[dposition:]

def get_value(keys,line,d):
    """Get value corresponding to 'key' from a line of ICOADS data.

    Arguments:
        keys: list of desired key 
        line: a single line from the input
        d: external metadata dictionary
    """
    # make sure keys are in a list
    if isinstance(keys,str):
        keys = [keys]
    
    # list of position arguments
    pos = list()  
    for key in keys:
        key = key.upper()
        pos.append(key_pos(key,d))
    
    # extract keys' values, add decimals where they are missing
    values = list()
    for (k,p) in zip(keys,pos):
        value = line[p[0]:p[1]].strip()
        if k == 'lat' or k == 'lon':
            value = add_decimal(value,-2)
        elif k == 'sst':
            value = add_decimal(value,-1)
        values.append(value)
    return values

def imma_data_files():
    (_, _, filenames) = next(walk(data_location))
    filenames = [fn for fn in filenames if '.dat' in fn]
    filenames.sort()
    return filenames

def icoads_data_dates(month,year):
    """From month and  year, find corresponding ICOADS data file."""
    return 'd'+str(year)+str(month).zfill(2)

def date_span(start_mth,start_yr,end_mth,end_yr):
    """For beginning/end month and year, return all month-year pairs betwee, and
    return substring to match in ICOADS data file names.

    Example:
        call:   date_span(11,1854,1,1856)
        output: ['d185411', 'd185412', 'd185501', 'd185502', 'd185503', 
                 'd185504', 'd185505', 'd185506', 'd185507', 'd185508', 
                 'd185509', 'd185510', 'd185511', 'd185512', 'd185601']
    """
    # get time difference between the two dates
    FMT = '%Y%m'
    start_date = datetime.strptime(str(start_yr)+str(start_mth),FMT)
    end_date   = datetime.strptime(str(end_yr)+str(end_mth),FMT)
    r = relativedelta.relativedelta(end_date,start_date)

    # count up all months between the two dates
    count_months = r.months
    for num_years in range(r.years):
        count_months += 12
    count_months += 1

    # go through each month and find icoads filename date substring
    month = start_mth
    year = start_yr
    file_substrings = list()
    for cm in range(count_months):
        if month % 13 == 0:
            month =1
            year += 1
        file_substrings.append(icoads_data_dates(month,year))
        month += 1
    return file_substrings

def retrieve_data_files(start_mth,start_yr,end_mth,end_yr,filenames):
    """Retrieve data files in the specified date range."""
    extraction_files = list()
    date_strings = date_span(start_mth,start_yr,end_mth,end_yr)
    for substring in date_strings:
        for fn in filenames:
            if substring in fn:
                extraction_files.append(fn)
                break
    return extraction_files

def lookup_pentads(d,date):
    """Gets pentads corresponding to 'date.'  
    Funky piece of code:
        
        Months:
        Months in the scheme do not match with normal calender months, so given
        month may occur in the previous month, so have to search in previous 
        month if the pentad is not found in the natural month.

            Example: 
                The first month, '1', has dates Jan 1-30, whereas Jan 31 occurs
                in second month, '2'.

        Try-Except:
        Because of the above, have possibility of 0 month, which raises 
        exception.

        Return:
        Breaks nested loop and returns pentads.
    """
    m = int(date.month)
    # date may occur in previous or next calender half-month according to this 
    # scheme 
    mth_rng = [m,m-1,m+1] #list(range(m,m-2,-1))

    for mth in mth_rng:
        try:
            d_month = d[str(mth)]
            for half_month in d_month:
                dates = d_month[half_month]['dates']
                if dates[0] <= date <= dates[1]:
                    pentads = d_month[half_month]['pentads']
                    return pentads, dates
        except:
            pass

def get_pentad(d,date):
    """Input date and stored dictionary holding yearly interval data, return the
    corresponding pentad.
        
    Note on input date year:
    Reset to 2016, which is the default I am using, since the year is 
    irrelevant, but want to use datetime objects which require all parts of
    date.  The only exception is that the date must be a leap year, so that 
    those dates may be handled properly.
    """
    date = date.replace(year=2016)
    pentads, dates = lookup_pentads(d,date)
    four_days = timedelta(days=4)
    five_days = timedelta(days=5)
    for p in range(len(pentads)-1):
        beg = dates[0] + p*five_days
        end = beg + four_days
        if beg <= date <= end:
            return pentads[p]
    return pentads[-1]

def main(start_mth,start_yr,end_mth,end_yr):
    """Main execution sequence: 
        load dictionary,
        retrieve raw lines,
        get_value(keys,line,dictionary).

    Pentad and information of the like loaded from external dictionary via
    load_yearly_intervals().
    """
    # create db table
    db_obs.create_table(IcoadsData)

    # set up data structures and data input files for a given time range
    d = load_dict()
    dict_icoads = dict()
    data_icoads = list()
    filenames = imma_data_files()
    extraction_files = retrieve_data_files(
                    start_mth,
                    start_yr,
                    end_mth,
                    end_yr,
                    filenames
                )
    d_yearly_intervals = load_yearly_intervals()
    
    # loop over all data files
    err_count = 0
    insert_count = 0
    lines_count = 0
    for data_file in extraction_files:

        # open ICOADS data file
        with open(data_location+data_file,"r",
                encoding='utf-8', errors='ignore') as f:
            print(data_file)
        
            # create database transaction
            with db_obs.atomic():
                for i,line in enumerate(f.readlines()):
                    lines_count += 1
                    extract_values = get_value(
                        ['lon','lat','sst','yr','mo','dy'],
                        line,
                        d)

                    try:
                        # Store data first in a list before commit
                        float(extract_values[2])
                        this_date = date(int(extract_values[3]),
                                int(extract_values[4]),
                                int(extract_values[5]))
                        pentad = get_pentad(d_yearly_intervals,this_date)
                        dict_icoads.update({'lon':extract_values[0],
                                'lat':extract_values[1],
                                'sst':extract_values[2],
                                'date':this_date,
                                'pentad':pentad
                                })
                        data_icoads.append(dict_icoads.copy())
                    except ValueError as ve:
                        print(ve)
                        err_count += 1
                    except TypeError as te:
                        err_count += 1    
                        print(logging.exception(te))

                    if i % 100 == 50 and data_icoads:
                        # commit data to savepoint
                        with db_obs.atomic():
                            insert_count += len(data_icoads)
                            IcoadsData.insert_many(data_icoads).execute()
                            data_icoads[:] = []
        
                if data_icoads:    
                    # pick up leftover data not processed in the savepoints
                    with db_obs.atomic():
                        insert_count += len(data_icoads)
                        IcoadsData.insert_many(data_icoads).execute()
                        data_icoads[:] = []
    db_obs.close()
    print("Error count:  ",err_count)
    print("Insert count: ",insert_count)
    print("Lines count:  ",lines_count)

if __name__ == '__main__':
    # pass

    # filenames = imma_data_files()
    main(1,1861,2,1861)

    # d = load_yearly_intervals()
    # date = datetime.strptime('2016-4-6','%Y-%m-%d').date()
    # print(lookup_pentads(d,date))
    # print(get_pentad(d,date))
