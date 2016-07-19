import json

def sort_dict(d):
    """Return keys of dictionary sorted accorded to 'id', found in nested 
    dictionary.
    """
    return sorted(d,key=lambda x: int(d[x]['id']))

def load_dict():
    """Load dictionary of metadata according to imma.txt."""
    with open('store_dictionary.json','r') as f:
        try:        
            d = json.load(f)
        except Exception as e:
            print(e)
    return d

def print_sorted_dict(d):
    """Print out the dictionary with keys in order according to imma.txt."""
    for key in sort_dict(d):
        print(key,d[key])

def get_position(key,line,sorted_keys,d):
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

def get_value(key,line,d,sorted_keys):
    """Get value corresponding to 'key' from a line of ICOADS data."""
    key = key.upper()
    pos = get_position(key,line,sorted_keys,d)
    print(line,'\n','\n')
    print(pos)
    value = line[int(pos[0]):int(pos[1])]
    print(value)
    return value

# def get_value_line(key,line,d,sorted_keys):
#     """Get value corresponding to 'key' from all lines of ICOADS data."""
#     pass

def main():
    """Main execution sequence."""
    d = load_dict()
    sorted_keys = sort_dict(d)
    with open('IMMA-MarineObs_icoads3.0.0_d185401_c20160608080000.dat') as f:
        line = f.readline()
    get_value('slp',line,d,sorted_keys)
    

if __name__ == '__main__':
    main()    