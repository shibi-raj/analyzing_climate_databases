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

def write_dict(d):
    """Write out the dictionary in JSON format"""
    with open('stored_dictionary.json','w') as f:
        json.dump(d,f)

def check_dump():
    """Verify dictionary contents match those in 'imma.txt'."""
    with open('store_dictionary.json','r') as f:
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


if __name__ == '__main__':
    create_dict()