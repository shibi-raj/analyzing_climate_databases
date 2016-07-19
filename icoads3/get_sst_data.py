#!/usr/bin/python3
"""
"""
from get_icoads_data import *
import codecs
import matplotlib.pyplot as plt
import numpy as np


def file_len(fname):
    """Returns the number of lines in a file."""
    with open(fname,'r',encoding='utf-8',errors='ignore') as f:
        for i, l in enumerate(f):
            pass
    return i + 1

def get_data_array(key,fname):
    """Enter a field name, and the corresponding value is returned from the 
    specified IMMA data file.
    """
    d = load_dict()
    sorted_keys = sort_dict(d)    
    with codecs.open(fname,'r',encoding='utf-8',errors='ignore') as f:
        values = [] 
        for i,line in enumerate(f.readlines()):
            try:
                value = str(get_value('sst',line,d,sorted_keys)).strip()
                values.append(float(value))
            except Exception as e:
                pass
    return values

if __name__ == '__main__':

    fname = 'IMMA-MarineObs_icoads3.0.0_d185401_c20160608080000.dat'

    values = get_data_array('SST',fname)
    values = np.array(values)
    plt.hist(values,bins=10)
    plt.show()