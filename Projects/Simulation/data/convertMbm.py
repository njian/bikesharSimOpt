import cPickle
import numpy
import operator
import datetime

def convertKeyAddDur():
    ''' Makes mbm2: a different-key version of mbm '''
    ''' Also takes the duration from mbmold, if available; otherwise, takes from googleMap data '''
    ''' Note: 3230 and 3236 are depots '''
    mbm = eval(open('mbm.txt').read()) # keys 0 to 47
    mbmold = cPickle.load(open('mbm30minOld.p','r')) # keys 30 times above
    durations = eval(open('PairwiseCyclingDurations.txt').read())
    mbm2 = {}
    count = 0
    total = 0
    for t in mbm.keys():
    	mbm2[t*30] = mbm[t].copy()

    # missingDurationDic = {}
    for t in mbm2.keys():
    	for sid in mbm2[t].keys():
    		mbm2[t][sid]['durations'] = {}
    		if mbmold[t].has_key(sid):
    			for dest in mbm2[t][sid]['dests']:
    				if mbmold[t][sid]['durations'].has_key(dest):
    					mbm2[t][sid]['durations'][dest] = mbmold[t][sid]['durations'][dest]
    				else:
    					mbm2[t][sid]['durations'][dest] = durations[sid][dest]
    		else:
    			for dest in mbm2[t][sid]['dests']:
    				# if not durations.has_key(sid):
    				# 	missingDurationDic[sid] = 1
    				# elif not durations[sid].has_key(dest):
    				# 	missingDurationDic[dest] = 1
    				# else:
    				mbm2[t][sid]['durations'][dest] = durations[sid][dest]
    # missingDuration = missingDurationDic.keys()
    # cPickle.dump(missingDuration, open('MissSidInGoogleDuration.p', 'wb'))
    cPickle.dump(mbm2, open('mbm30min.p', 'wb'))

def convertKey():
    mbm = eval(open('mbm-dec1-20-multiplied 15.txt').read()) # keys 0 to 4
    mbm2 = {}
    for t in mbm.keys():
        mbm2[t*30] = mbm[t].copy()

    cPickle.dump(mbm2, open('mbm30minDec_15x.p', 'wb'))

def addDurationMbm():
    ''' Records duration into the data by taking from googleMap data '''
    ''' Note: 3230 and 3236 are depots '''
    mbm = cPickle.load(open('mbm30min.p','r'))
    mbmold = cPickle.load(open('mbm30minOld.p','r')) # keys 30 times above
    durations = eval(open('PairwiseCyclingDurations.txt').read())

    for t in mbm.keys():
        for sid in mbm[t].keys():
            mbm[t][sid]['durations'] = {}
            if mbmold[t].has_key(sid):
                for dest in mbm[t][sid]['dests']:
                    if mbmold[t][sid]['durations'].has_key(dest):
                        mbm[t][sid]['durations'][dest] = mbmold[t][sid]['durations'][dest]
                    else:
                        mbm[t][sid]['durations'][dest] = durations[sid][dest]
            else:
                for dest in mbm[t][sid]['dests']:
                    mbm[t][sid]['durations'][dest] = durations[sid][dest]

    # for t in mbm.keys():
    #     for sid in mbm[t].keys():
    #         mbm[t][sid]['durations'] = {}
    #         for dest in mbm[t][sid]['dests']:
    #                 mbm[t][sid]['durations'][dest] = durations[sid][dest]

    cPickle.dump(mbm, open('mbm30minDec_x2_v2.p', 'wb'))

def findMissingSid():
    '''  Find missing sid of mbm in the given duration file '''
    mbm = cPickle.load(open('mbm30min.p', 'r'))
    durations = eval(open('PairwiseCyclingDurations.txt').read())
    # durations = eval(open('GoogleDuration_Jaffe.txt').read()) # keys 0 to 47
    count = 0

    missingDurationDic = {}
    for t in mbm.keys():
        for sid in mbm[t].keys():
            if durations.has_key(sid):
                for dest in mbm[t][sid]['dests']:
                    if durations[sid].has_key(dest):
                        mbm[t][sid]['durations'][dest] = durations[sid][dest]/60.0
                    else:
                        print "dest", dest, "not found in Jaffe durations"
                        missingDurationDic[dest] = 1
            else:
                print "sid", sid, "not found in Jaffe durations"
                missingDurationDic[sid] = 1
    missingDuration = missingDurationDic.keys()
    print missingDuration
    # cPickle.dump(missingDuration, open('MissSidInJaffeDuration.p', 'wb'))
    cPickle.dump(mbm, open('mbm30min_LNduration.p', 'wb'))

    ''' Check if there is any duration missing '''
    # missingDurationDic2 = {} # the missing stations from mbm
    # for t in mbm.keys():
    #   for sid in mbm[t].keys():
    #       for dest in mbm[t][sid]['dests']:
    #           if not durations.has_key(sid):
    #               missingDurationDic2[sid] = 1
    #           elif not durations[sid].has_key(dest):
    #               missingDurationDic2[dest] = 1
    # missingDuration2 = missingDurationDic2.keys()
    # print missingDuration2
    # cPickle.dump(missingDuration2, open('MissSidInGoogleDuration_v2.p', 'wb'))

    ''' Check how many durations are not available from the old mbm '''
    # mbm2 = cPickle.load(open('mbm30min.p', 'r'))
    # for t in mbm2.keys():
    #   for sid in mbm2[t].keys():
    #       for dest in mbm2[t][sid]['dests'].keys():
    #           total += 1
    #           if not mbmold[t].has_key(sid):
    #               count += 1
    #           elif not mbmold[t][sid]['durations'].has_key(dest):
    #               count += 1
    # print 'total dests in new mbm without duration data', count
    # print 'total dests in new mbm', total
    # print 'percent of dests without duration data:', float(count)/float(total)

    ''' Check if there's any sid = -1 in mbm '''
    # mbm = cPickle.load(open("mbm30min.p", 'r'))
    # for t in mbm.keys():
    #   for sid in mbm[t].keys():
    #       if sid == -1:
    #           count += 1
    #       for dest in mbm[t][sid]['dests']:
    #           if dest == -1:
    #               print "sid", sid, 'dest', -1

def checkLogNormalDuration():
    ''' Check if the generated duration is reasonable '''
    mbm = cPickle.load(open('mbm30minDec_2x.p', 'r'))
    durations = eval(open('PairwiseCyclingDurations.txt').read())
    intercept= 0.576887855816 
    slope= 0.911625572273
    sigma_2= 0.0570636366697
    sigma = numpy.sqrt(sigma_2)
    durList = []
    for t in mbm.keys():
        for sid in mbm[t].keys():
                for dest in mbm[t][sid]['dests']:
                    if durations[sid][dest] < 50000 and sid != dest:
                        dur = numpy.exp(intercept)*(durations[sid][dest]**(slope))*numpy.random.lognormal(0,sigma)/60.0
                        durList.append(dur)
                        if dur < 0.0001:
                            print "small duration", sid, dest
    print min(durList), max(durList)
    print numpy.mean(durList)
    print numpy.percentile(durList, 25), numpy.percentile(durList, 50), numpy.percentile(durList, 75)

def addNamesOrds(sM, names, fileName):
    ''' Add names and ords to the solutions '''
    for sid in sM.keys():
    	sM[sid]['name'] = names[sid]['name']
    	sM[sid]['ords'] = names[sid]['ords']

    file = open(fileName,'w')
    file.write(str(sM))
    file.close()

def getAverageAllocation(sM, names):
    solution = sM.copy()
    totalBikes = float(sum(sM[i]['bikes'] for i in sM.keys()))
    print totalBikes
    totalDocks = float(sum(names[i]['capacity'] for i in sM.keys()))
    print totalDocks
    for sid in solution.keys():
        solution[sid]['capacity'] = names[sid]['capacity']
        solution[sid]['bikes'] = round((names[sid]['capacity']/totalDocks)*totalBikes)

    excessBikes = totalBikes - int(sum(solution[i]['bikes'] for i in solution.keys())) #8
    remainBikes = excessBikes
    while remainBikes > 0:
        sid = numpy.random.choice(solution.keys())
        if solution[sid]['bikes'] + 1 <= solution[sid]['capacity']:
            solution[sid]['bikes'] += 1
            remainBikes -= 1
    print int(sum(solution[i]['bikes'] for i in solution.keys()))
    print int(sum(solution[i]['capacity'] for i in solution.keys()))
    file = open('AverageAllocationFromNames.txt','w')
    file.write(str(solution))
    file.close()

def getRealTotalBikes():
    realBikes = eval(open('RealBikeAlloc.txt').read())
    totalBikes = realBikes[72].copy()
    for t in totalBikes.keys():
        totalBikes[t] = 0

    for sid in realBikes.keys():
        for t in realBikes[sid].keys():
            totalBikes[t] += realBikes[sid][t]
    print totalBikes
    print "max, min ", max([totalBikes[t] for t in totalBikes.keys()]), min([totalBikes[t] for t in totalBikes.keys()])
    print "mean", numpy.mean([totalBikes[t] for t in totalBikes.keys()])
    print "stdev", numpy.std([totalBikes[t] for t in totalBikes.keys()])

    import matplotlib.pyplot as plt
    sortedd2 = sorted(totalBikes.items(), key=operator.itemgetter(0))
    new_y = [ sortedd2[i][1] for i in xrange(len(sortedd2)) ]
    new_x = [ sortedd2[i][0] for i in xrange(len(sortedd2)) ]
    plt.bar(new_x, new_y, align='center')
    plt.ylim([5400, 5900])
    plt.show()

def getLogNormalDurationMultiplier():
    durations = eval(open('PairwiseCyclingDurations2.txt').read())
    intercept = 0.529757703409 
    slope = 0.927357409351

    mult = durations.copy()
    for s1 in mult.keys():
        for s2 in mult[s1].keys():
            mult[s1][s2] = (durations[s1][s2]**slope) * (numpy.exp(intercept))/60.0
    
    file = open('durationsLNMultiplier2.txt','w')
    file.write(str(mult))
    file.close()

def checkSolution(fileName):
    solution = eval(open(fileName).read())
    print fileName, sum(solution[i]['bikes'] for i in solution.keys()), sum(solution[i]['capacity'] for i in solution.keys())

def totalDailyTripsMbm(mbm):
    total = 0
    for t in mbm.keys():
        for sid in mbm[t].keys():
            total += 30*mbm[t][sid]['total']
    return total

def totalDailyStationTripsMbm(mbm, sid):
    total = 0
    for t in mbm.keys():
        if mbm[t].has_key(sid):
            total += 30*mbm[t][sid]['total']
    return total

if __name__ == '__main__':
    # fileName = 'CTMCVaryRateBikesOnly6-10_15x.txt'
    # sM = eval(open(fileName).read())
    # names = eval(open('CoordsAndNames.txt').read())

    # getAverageAllocation(sM, names)
    # addNamesOrds(sM, names, fileName)
    # getRealTotalBikes()
    # convertKey()
    # addDurationMbm()
    # getLogNormalDurationMultiplier()
    # checkLogNormalDuration()

    # checkSolution('CTMCVaryRate6-10_15x.txt')
    # checkSolution('CTMCVaryRateBikesOnly6-10_15x.txt')
    # checkSolution('CTMCVaryRate6-24_15x.txt')
    # checkSolution('CTMCVaryRateBikesOnly6-24_15x.txt')
    # checkSolution('AverageAllocationFromNames.txt')

    mbm = cPickle.load(open("mbm30minDec_15x.p", 'r'))
    totalDailyTripsMbm(mbm)

    



    ######