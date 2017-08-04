import cPickle
sid = 521

mbm = cPickle.load(open("mbm30minDec_15x.p", 'r'))
total = 0
for t in mbm.keys():
	if mbm[t].has_key(sid):
		total += mbm[t][sid]['total']*30.0

print sid, total