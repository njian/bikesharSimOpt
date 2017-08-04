'''
Simulate and get counts of alterEnds, failedStarts in the objective

Nanjing Jian, last updated 2016/11
'''

import SimulationRunnerCounts as SimulationRunnerCaps
import math, random
import numpy
import time
import cPickle
from collections import Counter, defaultdict
import operator
import logging

def simulate(level, capacity, sM, rep, seed, mbm, durations,
             simMethod="AltCond", startTime=420, numIntervals=4):
    ''' Simulate the system for the inputted period and station configurations.

    Args:
        level: {sid: starting bike levels at sid}.
        capacity: {sid: starting capacity at sid}.
        sM: see randomSearch().
        rep: requested simulation replications.
        seed: starting random seed for the requested replications.
        mbm: see randomSearch().
        durations: see randomSearch().
        simMethod: simulation method. See BikeSim.
        startTime: see randomSearch().
        numIntervals: see randomSearch().

    Returns:
        solutionList: starts with the list of outputs from
                      SimulationRunner.runDay(), followed by the objective
                      value.
        obj: Monte Carlo estimator of the obj value from reps or replicatins.
        ciwidth: 95% CI half width.
        arrowDict: {sid: a list of 1's (trip in) and -1's (trip out) in time
                    order}

    Todo:
    '''
    numpy.random.seed(seed)
    soln = 0
    s1 = []
    s2 = []
    solutionList = {}
    solutionList2 = []
    arrowDict = {}
    failedStartCount = defaultdict(int)
    alterEndCount = defaultdict(int)

    for i in range(rep):
        data = SimulationRunnerCaps.testVehicles2(level, capacity, sM, mbm, durations,
            simMethod, startTime, numIntervals)
        solutionList[i] = data[0:3]
        solutionList2.append(float(sum(data[0:3])))
        arrowDict[i] = data[3]
        for sid in data[4].keys():
            failedStartCount[sid] += data[4][sid]
        for sid in data[5].keys():
            alterEndCount[sid] += data[5][sid]

    for sid in failedStartCount.keys():
        failedStartCount[sid] = round(failedStartCount[sid] / float(rep))
    for sid in alterEndCount.keys():
        alterEndCount[sid] = round(alterEndCount[sid] / float(rep))

    obj = round(numpy.mean(solutionList2, axis=0), 2)
    ciwidth = round(numpy.std(solutionList2)*1.96/numpy.sqrt(rep), 2)

    return (solutionList, obj, ciwidth, arrowDict, failedStartCount, alterEndCount)


if __name__ == '__main__':
    ''' Configurations '''
    seed = 9
    start = 6
    end = 24
    rep = 30 # replications to evaluate each trial solution
    startTime = int(start*60) # simulation start time (minutes, from 0 to 1439)
    numIntervals = int(2*(end-start)) # number of 30-minute intervals to simulate

    solutionFile = 'fluidModelUB_Dec15x'
    solutionName = 'FluidModel'
    fileInd = numpy.random.randint(1,99)
    fileName = "CTMCVaryRate6to24_15xid12id62CapsTableRnCaps"

    # get state map info (caps, ords)
    # sM = eval(open(('./data/'+solutionFile+'.txt')).read())
    sM = cPickle.load(open('./data/%s.p' % solutionFile, 'r'))
    capacity = cPickle.load(open(('./outputsDO/%sCapacity.p' % fileName), 'r'))
    level = cPickle.load(open(('./outputsDO/%sLevel.p' % fileName), 'r'))
    for sid in sM:
        sM[sid]['bikes'] = level[sid]
        sM[sid]['capacity'] = capacity[sid]
    sM[-1000] = {'bikes':-1000, 'capacity':-1000, 'ords':(0,0), 'name':"null"}

    # get durations
    durationMult = eval(open('./data/durationsLNMultiplier2.txt').read())

    # get min-by-min data
    mbm = cPickle.load(open("./data/mbm30minDec_15x.p", 'r'))

    ''' Just Simulate! '''
    level = {} # level of bikes at each station at the beginning of the day
    capacity = {} # capacity of each station
    for sid in sM:
        level[sid] = sM[sid]['bikes']
        capacity[sid] = sM[sid]['capacity']
    _, _, _, _, failedStartCount, alterEndCount = simulate(level, capacity, sM, rep, seed, mbm, durationMult, "AltCond", 360, 8)
    cPickle.dump(failedStartCount, open(("./outputsDO/%sFailedStarts.p" % fileName), 'wb'))
    cPickle.dump(alterEndCount, open(("./outputsDO/%sAlterEnds.p" % fileName), 'wb'))
    print "Finished."
