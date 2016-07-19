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
import json
from IPython import embed
embed() 

def load_dict():
    """Load dictionary, stored_dictionary.json, of metadata according to 
    imma.txt.
    """
    with open('stored_dictionary.json','r') as f:
        try:        
            d = json.load(f)
        except Exception as e:
            print(e)
    return d

def key_pos(key,d):
    """Uses the dictionary derived from 'stored_dictionary.json' to retrieve the 
    position of the value of a key.
    """
    return d[key]['position']

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
    
    # extract keys' values
    values = list()
    for p in pos:
        values.append(line[p[0]:p[1]].strip())
    return values

def main():
    """Main execution sequence."""
    d = load_dict()
    with open('IMMA-MarineObs_icoads3.0.0_d185401_c20160608080000.dat') as f:
        line = f.readline()
    print(get_value(['sst','slp'],line,d))



if __name__ == '__main__':
    main()    