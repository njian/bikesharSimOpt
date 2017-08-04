import cPickle

solID = 90
bikes = cPickle.load(open('./outputsDO/CTMCVaryRate6-24_15xid%iCapsLevel.p'%solID,'r'))
capacity = cPickle.load(open('./outputsDO/CTMCVaryRate6-24_15xid%iCapsCapacity.p'%solID,'r'))
ctmc = eval(open('./data/CTMCVaryRate6-24_15x.txt').read())
diffBikes = 0
diffCapacity = 0
print bikes[382]
print ctmc[382]['bikes']
for sid in ctmc.keys():
	diffBikes += abs(bikes[sid] - ctmc[sid]['bikes'])
	diffCapacity += abs(capacity[sid] - ctmc[sid]['capacity'])

print diffBikes, diffCapacity