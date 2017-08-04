import cPickle

mbm = cPickle.load(open('mbm30min_v2.p','r'))
duration = {}
for t in mbm.keys():
    for s1 in mbm[t].keys():
        duration[s1] = {}
for t in mbm.keys():
    for s1 in mbm[t].keys():
        for s2 in mbm[t][s1]['dests'].keys():
            duration[s1][s2] = []

# check
for t in mbm.keys():
    for s1 in mbm[t].keys():
        if not duration.has_key(s1):
            print "error1"
        for s2 in mbm[t][s1]['dests'].keys():
            if not duration[s1].has_key(s2):
                print "error2", s1, s2

cPickle.dump(duration, open('duration.p', 'wb'))