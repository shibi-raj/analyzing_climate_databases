with open('imma.txt','r') as f:
    d = dict()
    # order for rearranging input, description fields added in a bit
    order = [2,0,1] 
    # keys for nested dictionary => to 0,1 in order, + description field follows
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


for each in d:
    print(each,d[each])