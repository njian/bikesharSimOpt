import cPickle

tInt = 30
mbm2 = {}
for i in range(int(1440/tInt)): # 48 files
	mbm = eval(open('./mbmData/minbymin' + str(i) + '.txt').read())
	for t in mbm.keys():
		if mbm[t] != mbm[t - t%30]:
			print "Warning! mbm at %i is not consistent", t
	mbm2[mbm.keys()[0] - mbm.keys()[0]%30] = mbm[t].copy()

cPickle.dump(mbm2, open('mbmDec30min.p', 'wb'))