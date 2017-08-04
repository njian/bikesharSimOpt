import cPickle
import operator
import numpy
import matplotlib.pyplot as plt
# import SimulationRunnerMbm

def processSolns(f1, f2, objID):
    d1 = {}
    for i in f1.keys():
        temp = []
        for j in range(len(f1[i])):
            temp.append(f1[i][j][objID])
        d1[i] = numpy.mean(temp, axis=0)
    sortedd1 = sorted(d1.items(), key=operator.itemgetter(0))
    old_y = [ sortedd1[i][1] for i in xrange(len(sortedd1)) ]
    old_x = [ sortedd1[i][0] for i in xrange(len(sortedd1)) ]

    d2 = {}
    for i in f2.keys():
        temp = []
        for j in range(len(f2[i])):
            temp.append(f2[i][j][objID])
        d2[i] = numpy.mean(temp, axis=0)
    sortedd2 = sorted(d2.items(), key=operator.itemgetter(0))
    new_y = [ sortedd2[i][1] for i in xrange(len(sortedd2)) ]
    new_x = [ sortedd2[i][0] for i in xrange(len(sortedd2)) ]

    return old_x, old_y, new_x, new_y

def basicVSPlot(old_x, old_y, name_old, new_x, new_y, name_new, xlimUB, name, saveName):
    plt.clf()
    plt.figure()
    plt.plot(old_x, old_y, color='b', label = name_old)
    plt.plot(new_x, new_y, color='r', label = name_new)
    plt.legend()
    # plt.xlim(0,5000)
    # plt.ylim(0,350)
    ax = plt.gca()
    # ax.set_autoscale_on(False)
    ax.set_xlim([0,xlimUB])
    # plt.text(0, 520, 'CTMC solution')
    plt.title(("Comparison of Selective Search from Different Starts: "+name))
    plt.xlabel("Number of Simulation Days")
    plt.ylabel(("number of: "+name))
    # plt.show()
    plt.savefig(saveName)

def plotObjectives(solnName1, solnName2, name_old, name_new):
    fileName1 = "./outputsDO/"+solnName1+"Results.p"
    fileName2 = "./outputsDO/"+solnName2+"Results.p"
    f1 = cPickle.load(open(fileName1, 'r'))
    f2 = cPickle.load(open(fileName2, 'r'))
    old_x, old_y = sortDict(f1)
    new_x, new_y = sortDict(f2)
    basicVSPlot(old_x, old_y, name_old, new_x, new_y, name_new, 'totalObj')

def basicVSPlot2(heuristic, toCompare, toCompareNames, colors, xlimUB, fileName):
    plt.clf()
    plt.figure()
    ax = plt.gca()
    ax.set_xlim([0,xlimUB])
    plt.title(('Comparison of Heuristic %i from Different Starts' % heuristic))
    plt.xlabel("Number of Simulation Days")
    plt.ylabel(("Objective Value"))
    for i in toCompare.keys():
        x, y = toCompare[i]
        plt.plot(x, y, color=colors[i], label = toCompareNames[i])
    plt.legend()
    plt.savefig(fileName)
    plt.show()

def sortDict(f1, components):
    d1 = {}
    for i in f1.keys():
        temp = []
        for j in range(len(f1[i])):
            temp.append(sum(f1[i][j][0:components]))
        d1[i] = numpy.mean(temp, axis=0)
    sortedd1 = sorted(d1.items(), key=operator.itemgetter(0))
    old_y = [ sortedd1[i][1] for i in xrange(len(sortedd1)) ]
    old_x = [ sortedd1[i][0] for i in xrange(len(sortedd1)) ]
    return old_x, old_y

def plotObjective(fsoln, indOld, solnType):
    solnName = (fsoln+"id"+str(indOld)+solnType)
    fileName = "./outputsDO/"+solnName+"Results.p"
    f = cPickle.load(open(fileName, 'r'))

    x, y = sortDict(f)

    plt.clf()
    plt.figure()
    plt.plot(x, y, color='r', label = solnName)
    plt.legend()
    # plt.xlim(0,5000)
    # plt.ylim(0,350)
    ax = plt.gca()
    # ax.set_autoscale_on(False)
    # ax.set_xlim([0,6000])
    # plt.text(0, 520, 'CTMC solution')
    plt.title(solnName)
    plt.xlabel("Number of Simulation Days")
    plt.ylabel("Objective")
    plt.show()
    plt.savefig("./outputsDO/" + solnName +".png")

def plotDecomp(f1soln, f2soln, indOld, indNew):
    fileName1 = "./outputsDO/"+f1soln+str(indOld)+"results.p"
    fileName2 = "./outputsDO/"+f2soln+str(indNew)+"results.p"

    # file: keys: number of simulated days, item: obj over all reps
    f1 = cPickle.load(open(fileName1, 'r'))
    f2 = cPickle.load(open(fileName2, 'r'))

    # failed (bad) ends
    old_x, old_y, new_x, new_y = processSolns(f1, f2, 0)
    basicVSPlot(old_x, old_y, new_x, new_y, 'failedEnds')

    # failed starts
    old_x, old_y, new_x, new_y = processSolns(f1, f2, 1)
    basicVSPlot(old_x, old_y, new_x, new_y, 'failedStarts')

    # alt ends
    old_x, old_y, new_x, new_y = processSolns(f1, f2, 2)
    basicVSPlot(old_x, old_y, new_x, new_y, 'altEnds')

def plotMbm(sid, mbm):
    outflow = []
    totalTime = 24
    inflow = [0 for i in range(totalTime*60)]
    # for i in range(t):
    #     mbm.update(eval(open('./mbmData/minbymin' + str(i) + '.txt').read()))

    for t in range(totalTime*60):
        i = t-t%30
        if mbm[i].has_key(sid):
            outflow.append(mbm[i][sid]['total'])
        else: outflow.append(0)
        count = 0
        for s2 in mbm[i].keys():
            # count inflow at sid after duration time
            if mbm[i][s2]['dests'].has_key(sid):
                intime = int(round(t+mbm[i][s2]['durations'][sid]/60.0)-1)
                if intime <= totalTime*60-1:
                    inflow[intime] += mbm[i][s2]['dests'][sid]

    plt.figure()
    plt.title(('mbm flow rates (bikes/hr) for sid '+str(sid)))
    plt.plot(outflow, color='b', label = 'outflows (inc. failedStarts)')
    plt.plot(inflow, color='r', label = 'inflows (inc. failedEnds)')
    plt.xlim([0,1439])
    plt.legend()
    # plt.show()
    plt.savefig(("./mbmData/sid"+str(sid)+"mbm.png"))

def obtainLevels(mbm, sM, durations, listID, rep, startTime, numIntervals):
    import SimulationRunnerCapsMbm
    # fileName1 = ("./outputsDO/%s.p" % (solutionName + 'Level'))
    # level = cPickle.load(open(fileName1, 'r'))
    # fileName1 = ("./outputsDO/%s.p" % (solutionName + 'Capacity'))
    # capacity = cPickle.load(open(fileName2, 'r'))
    level = {} # level of bikes at each station at the beginning of the day
    capacity = {} # capacity of each station
    for sid in sM.keys():
        level[sid] = sM[sid]['bikes']
        capacity[sid] = sM[sid]['capacity']

    ''' Creat empty pickles '''
    lvl = {}
    for sid in listID:
        for i in range(rep):
            cPickle.dump(lvl, open( ('./outputsDO/lvlInDay/sid' + str(sid) + "lvlInDay" + str(i+1) + ".p"),'wb'))

    ''' Simulate and record '''
    numpy.random.seed(8)
    for i in range(rep):
        SimulationRunnerCapsMbm.testVehicles2(i+1, level, capacity, sM, mbm, durations, "AltCond", startTime, numIntervals, listID)

def plotLevels(sid, sM, rep, plotID=1):
    plt.figure(plotID)
    plt.title(('sid'+str(sid)+'capacity'+str(sM[sid]['capacity'])+'level in the day'))
    for i in range(rep):
        levels = cPickle.load(open(('./outputsDO/lvlInDay/sid'+str(sid)+"lvlInDay"+str(i+1)+".p"),'r'))
        sortedlvl = sorted(levels.items(), key=operator.itemgetter(0))
        plt.plot(sorted(levels.keys()), sortedlvl)
    plt.axis([360,1439,0,sM[sid]['capacity']])
    plt.savefig(("./outputsDO/lvlInDay/sid"+str(sid)+"lvlInDay.png"))
    # plt.show()

def plotLevelsOne(sid, sM, rep, plotID=1):
    plt.figure(plotID)
    plt.title(('sid'+str(sid)+'capacity'+str(sM[sid]['capacity'])+'level in the day'))
    for i in range(rep):
        levels = cPickle.load(open(('./outputsDO/lvlInDay/sid'+str(sid)+"lvlInDay"+str(i+1)+".p"),'r'))
        sortedlvl = sorted(levels.items(), key=operator.itemgetter(0))
        plt.plot(sorted(levels.keys()), sortedlvl)

def plotLevelsAll(sidList):
# row and column sharing
    f, ((ax1, ax2), (ax3, ax4)) = plt.subplots(3, 2, sharex='col', sharey='row')
    ax1.plot(x, y)
    ax1.set_title('Sharing x per column, y per row')
    ax2.scatter(x, y)
    ax3.scatter(x, 2 * y ** 2 - 1, color='r')
    ax4.plot(x, 2 * y ** 2 - 1, color='r')

def plotObjectivesH1():
    import cPickle
    f1 = cPickle.load(open('./outputsDO/AverageAllocationFromNamesid73Results.p','r'))
    f1key = sortDict(f1,3)[0]
    x1 = f1key
    y1 = sortDict(f1,3)[1]

    f4 = cPickle.load(open('./outputsDO/CTMCVaryRateBikesOnly6-10_15xid60Results.p','r'))
    f4key = sortDict(f4,3)[0]
    x2 = f4key
    y2 = sortDict(f4,3)[1]

    xaxisUB = 30000 #max(max(x1),max(x2))
    basicVSPlot2(1, {0: (x1,y1), 1: (x2,y2)}, ["Equal Alloc", "CTMC"], ['b', 'r'], xaxisUB, "./outputsDO/wscplots/H1plot1.png")
    basicVSPlot2(1, {0: (x2,y2)}, ["CTMC"], ['r'], 32000, "./outputsDO/wscplots/H1plot2.png")

def plotObjectivesH2():
    import cPickle
    f1 = cPickle.load(open('./outputsDO/AverageAllocationFromNamesid19DecompResults.p','r'))
    f2 = cPickle.load(open('./outputsDO/AverageAllocationFromNamesid9DecompResults.p','r'))
    f3 = cPickle.load(open('./outputsDO/AverageAllocationFromNamesid12DecompResults.p','r'))
    f1key = sortDict(f1,5)[0]
    f2key = sortDict(f2,5)[0]
    f3key = sortDict(f3,5)[0]
    f2key = [f + max(f1key) for f in f2key]
    f3key = [f + max(f2key) for f in f3key]
    x1 = f1key + f2key + f3key
    y1 = sortDict(f1,5)[1] + sortDict(f2,5)[1] + sortDict(f3,5)[1]

    f4 = cPickle.load(open('./outputsDO/CTMCVaryRateBikesOnly6-24_15xid66DecompResults.p','r'))
    f4key = sortDict(f4,5)[0]
    x2 = f4key
    y2 = sortDict(f4,5)[1]

    xaxisUB = max(max(x1),max(x2))
    basicVSPlot2(2, {0: (x1,y1), 1: (x2,y2)}, ["Equal Alloc", "CTMC"], ['b', 'r'], 32000, "./outputsDO/wscplots/H2plot1.png")
    basicVSPlot2(2, {0: (x2,y2)}, ["CTMC"], ['r'], 32000, "./outputsDO/wscplots/H2plot2.png")

def plotObjectivesH3():
    import cPickle
    f1 = cPickle.load(open('./outputsDO/AverageAllocation6to10_15xid6CapsResults.p','r'))
    f1key = sortDict(f1,3)[0]
    x1 = f1key
    y1 = sortDict(f1,3)[1]

    f4 = cPickle.load(open('./outputsDO/CTMCVaryRate6to10_15xid31CapsResults.p','r'))
    f4key = sortDict(f4,3)[0]
    x2 = f4key
    y2 = sortDict(f4,3)[1]

    f6 = cPickle.load(open('./outputsDO/FluidModel6to10_15xid10CapsResults.p','r'))
    x3 = sortDict(f6,3)[0]
    y3 = sortDict(f6,3)[1]

    xaxisUB = max(max(x1),max(x2))
    basicVSPlot2(3, {0: (x1,y1), 1: (x2,y2), 2: (x3, y3)}, ["Equal Alloc", "CTMC", "Fluid Model"], ['b', 'r', 'g'], xaxisUB, "./outputsDO/wscplots/H3plot1.png")
    basicVSPlot2(3, {0: (x3,y3), 1: (x2,y2)}, ["Fluid Model", "CTMC"], ['g', 'r'], max(max(x2),max(x3)), "./outputsDO/wscplots/H3plot2.png")

def plotObjectivesH4():
    import cPickle
    f1 = cPickle.load(open('./outputsDO/AverageAllocationFromNamesid5CapsDecompResults.p','r'))
    f2 = cPickle.load(open('./outputsDO/CTMCVaryRate6-24_15xid86CapsDecompResults.p','r'))
    f3 = cPickle.load(open('./outputsDO/AverageAllocationFromNamesid73CapsDecompResults.p','r'))
    f1key = sortDict(f1,5)[0]
    f2key = sortDict(f2,5)[0]
    f3key = sortDict(f3,5)[0]
    f2key = [f + max(f1key) for f in f2key]
    f3key = [f + max(f2key) for f in f3key]
    x1 = f1key + f2key + f3key
    y1 = sortDict(f1,5)[1] + sortDict(f2,5)[1] + sortDict(f3,5)[1]

    f4 = cPickle.load(open('./outputsDO/CTMCVaryRate6-24_15xid89CapsDecompResults.p','r'))
    f5 = cPickle.load(open('./outputsDO/CTMCVaryRate6-24_15xid94CapsDecompResults.p','r'))
    f4key = sortDict(f4,5)[0]
    f5key = sortDict(f5,5)[0]
    f5key = [f + max(f4key) for f in f5key]
    x2 = f4key + f5key
    y2 = sortDict(f4,5)[1] + sortDict(f5,5)[1]

    f6 = cPickle.load(open('./outputsDO/FluidModel (6-24 Optimal Allocation with UB)id78CapsDecompResults.p','r'))
    x3 = sortDict(f6,5)[0]
    y3 = sortDict(f6,5)[1]

    xaxisUB = max(max(x1),max(x2))
    basicVSPlot2(4, {0: (x1,y1), 1: (x2,y2), 2: (x3, y3)}, ["Equal Alloc", "CTMC", "Fluid Model"], ['b', 'r', 'g'], xaxisUB, "./outputsDO/wscplots/H4plot1.png")
    basicVSPlot2(4, {0: (x3,y3), 1: (x2,y2)}, ["Fluid Model", "CTMC"], ['g', 'r'], max(max(x2),max(x3)), "./outputsDO/wscplots/H4plot2.png")

if __name__ == '__main__':
    # plotObjectivesH3()
    # plotObjectivesH4()

    # sidList = [487,490]
    # print sidList
    # rep = 10
    # sM = eval(open('./data/CTMCVaryRateBikesOnly6-24_15x.txt').read())
    # sM[-1000] = {'bikes':-1000, 'capacity':-1000, 'ords':(0,0), 'name':"null"}
    # durationMult = eval(open('./data/durationsLNMultiplier2.txt').read())
    # mbm = cPickle.load(open("./data/mbm30minDec_15x.p", 'r'))
    # obtainLevels(mbm, sM, durationMult, sidList, rep, 360, 36)
    # i = 1
    # for sid in sidList:
    #     plotLevels(sid, sM, rep, i)
    #     i += 1

    f1 = cPickle.load(open('./outputsDO/AverageAllocationid17CapsTableRnCapsResults.p','r'))
    f1b = cPickle.load(open('./outputsDO/AverageAllocationid17CapsResults.p','r'))
    x1 = sorted(f1.keys())
    x1 = [key for key in x1 if key < 10000]
    x1b = sorted(f1b.keys())
    f1bkey = [key + max(x1) for key in x1b]
    f1key = x1 + f1bkey
    y1 = [f1[ite] for ite in x1] + [f1b[ite] for ite in x1b]
    x1 = f1key

    f2 = cPickle.load(open('./outputsDO/FluidModelid50CapsTableRnCapsResults.p','r'))
    x2 = sorted(f2.keys())
    y2 = [f2[ite] for ite in x2]

    f3 = cPickle.load(open('./outputsDO/CTMCVaryRate6to24_15xid12CapsTableRnCapsResults.p','r'))
    x3 = sorted(f3.keys())
    y3 = [f3[ite] for ite in x3]

    f4 = cPickle.load(open('./outputsDO/wsc/wscdata/AvgAlloc/AverageAllocationid90CapsDecompResults.p','r'))
    x4 = sorted(f4.keys())
    y4 = [f4[ite] for ite in x4]
    # f4key = sortDict(f4,3)[0]
    # x4 = f4key
    # y4 = sortDict(f4,3)[1]

    f5 = cPickle.load(open('./outputsDO/wsc/wscdata/CTMC/CTMCVaryRate6-24_15xid89CapsDecompResults.p','r'))
    f5b = cPickle.load(open('./outputsDO/wsc/wscdata/CTMC/CTMCVaryRate6-24_15xid94CapsDecompResults.p','r'))
    f5key = sortDict(f5,5)[0]
    f5bkey = sortDict(f5b,5)[0]
    f5bkey = [f + max(f5key) for f in f5bkey]
    x5 = f5key + f5bkey
    y5 = sortDict(f5,5)[1] + sortDict(f5b,5)[1]

    f6 = cPickle.load(open('./outputsDO/wsc/wscdata/FluidModel/FluidModel (6-24 Optimal Allocation with UB)id78CapsDecompResults.p','r'))
    f6key = sortDict(f6,5)[0]
    x6 = f6key
    y6 = sortDict(f6,5)[1]

    plt.clf()
    plt.figure()
    plt.plot(x4, y4, color='y', label = "id90, wsc Heuristic: Average Allocation")
    plt.plot(x1, y1, color='b', label = "id17, Table Method: Average Allocation")
    plt.plot(x6, y6, color='k', label = "id78, wsc Heuristic: Fluid")
    plt.plot(x2, y2, color='r', label = "id50, Table Method: Fluid")
    plt.plot(x5, y5, color='c', label = "id89, wsc Heuristic: CTMC")
    plt.plot(x3, y3, color='g', label = "id12, Table Method: CTMC")
    plt.legend(bbox_to_anchor=(0., 1.02, 1., .102), loc=3,
           ncol=3, mode="expand", borderaxespad=0.)
    plt.legend(loc=1, prop={'size':12})
    # plt.xlim(0,5000)
    # plt.ylim(0,350)
    ax = plt.gca()
    # ax.set_autoscale_on(False)
    # ax.set_xlim([0,20000])
    # plt.text(0, 520, 'CTMC solution')
    plt.title("Optimizing Bike and Dock in 6am-12am")
    plt.xlabel("Number of Simulation Days")
    plt.ylabel(("Objective Value"))
    plt.savefig("./outputsDO/tablePlots/table_method_new_6-24_vs.png")


    #