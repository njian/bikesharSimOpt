'''
Optimizing both bike and capacity allocations using the "table" method.
Instead of moving between one pair of stations, move between multiple pairs based on the cost table.

Nanjing Jian, last updated 2016/09
'''

import SimulationRunnerCapsTable as SimulationRunnerCaps
import math, random
import numpy
import time
import cPickle
from collections import Counter
import operator
import logging
import bisect

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

    for i in range(rep):
        data = SimulationRunnerCaps.testVehicles2(level, capacity, sM, mbm, durations,
            simMethod, startTime, numIntervals)
        solutionList[i] = data[0:3]
        solutionList2.append(float(sum(data[0:3])))
        arrowDict[i] = data[3]

    cPickle.dump(arrowDict, open('arrowDict.p','wb'))

    obj = round(numpy.mean(solutionList2, axis=0), 2)
    ciwidth = round(numpy.std(solutionList2)*1.96/numpy.sqrt(rep), 2)

    return (solutionList, obj, ciwidth, arrowDict)


def calculateStationObj(arrowDict, sid, level, capacity, deltaLevel, deltaCapacity):
    ''' Goes through the arrowList and 'simulate' the avg objective if the
        starting level and capacity is as inputted.

    Args:
    arrowDict: {rep: {sid: ordered list of [+1 for inflow, -1 for outflow]}}
    sid: The prompted station id.
    level: The trial solution for bike allocations of all stations.
    capacity: The trial solution for dock allocations of all stations.
    deltaLevel: Change in bike level for sid.
    deltaCapacity: change in dock level for sid.

    Returns: The average contributon of station sid to the objective over
             replications.
    '''
    # TODO: put this in a Class as self.minCap and maxCap
    minCap = 16
    maxCap = 60
    newLevel = level[sid] + deltaLevel
    newCapacity = capacity[sid] + deltaCapacity

    # First put huge cost on infeasible solutions
    if newLevel > newCapacity or newLevel < 0 or newCapacity < minCap or capacity > maxCap:
        return 9999

    obj = [0]*len(arrowDict.keys()) # length = #replications
    for rep in arrowDict.keys(): # replication
        l = level[sid] + deltaLevel
        for x in arrowDict[rep][sid]:
            if l + x > capacity[sid] + deltaCapacity or l + x < 0:
                obj[rep] += 1
            else: l += x
    return round(numpy.mean(obj, axis=0), 2)


def calculateTotalObj(arrowDict, level, capacity):
    ''' Returns the total objective value over all stations. '''
    obj = 0
    for sid in arrowDict[0].keys():
        obj += calculateStationObj(arrowDict, sid, level[sid], capacity[sid], 0, 0)
    return obj


def initializeEmptyDicts(keys, numToInitialize=1):
    ''' Returns a list of dictionaries with key=keys '''
    returnList = []
    for i in range(numToInitialize):
        returnList.append({})
    return returnList


def initializeEmptyLists(numToInitialize=1):
    ''' Returns a list of numToInitialize number of empty lists '''
    returnList = []
    for i in range(numToInitialize):
        returnList.append([])
    return returnList


def returnIndexSid(costList, sid):
    ''' Return the index of the entry in costList with sid as its first entry '''
    for i in range(len(costList)):
        if costList[i][0] == sid:
            return i
    return None
            

def randomSearch(sM, mbm, durations, fileName, startTime, numIntervals, config):
    ''' Performs Heuristic search.

    Args:
        sM: state map that contains the location of each sid.
        mbm: minute-by-minute flow rates at each station of thr structure
                  {second:{sid:{'dests': {sid: fraction of traffic going to this
                                               sid},
                                'total': total outflow trips/sec}}}.
        durations: the multiplier to a log-normal(0,1) rv to generate trip
                   durations.
        fileName: fileName to store the output pickles.
        startTime: starting time of the day.
        numIntervals: number of 30 minute intervals.
        config: [seed, rep, nMatch, nMove] configurations of the simulation.
                seed is the random seed that controls the same set of reps for
                    each trial solution.
                rep is number of replications to evaluate each solution.
                nMatch is the number of pairs of stations to swap bikes between
                    in each iteration.
                nMove is the number of bikes to swap between the "matched"
                    station pairs.

    Returns:
        end-start: time duration of the algorithm.
        objFinal: final objetive value.
        ciwidthFinal: final objective ci width.
        obj00: initial objective.
        ciwidth00: initial objective ci width.

    KeyboardInterrupt: pause and outputs the current objective. If prompted,
                       stop and record the results in Pickle.

    '''

    ''' Configurations '''
    simMethod = 'AltCond'
    logger1 = logging.getLogger('gradSearchCapsTable')
    daySeed = config[0]
    rep = config[1] # to evaluate each objective
    nMatch = config[2]
    nMove = config[3]
    maxInd = config[4] # generate random index between 0 and this
    maxCap = 60 # max capacity of a station when optimizing
    minCap = 16 # min capacity of a station when optimizing
    simCount = 0 # count of total simulation days
    diff = -1
    improve = 0.0

    start = time.time()
    ''' Read solution '''
    level = {} # level of bikes at each station at the beginning of the day
    capacity = {} # capacity of each station
    for sid in sM:
        level[sid] = sM[sid]['bikes']
        capacity[sid] = sM[sid]['capacity']
    obj1 = 0.0

    ''' Get initial solution '''
    objAll0, obj0, ciwidth0, arrowDict = simulate(level, capacity, sM, 30,
        daySeed, mbm, durations, simMethod, startTime, numIntervals)
    logger1.warning( ("Obj0: " + str(obj0) + " ciwidth " + str(ciwidth0)) )
    obj00 = obj0
    ciwidth00 = ciwidth0
    results = {}
    results[0] = obj00

    ''' Swapping Heuristics '''
    seed = daySeed
    failedswap = 0
    failedSinceLastChange = 0

    while True: # Stopping criteria
        try:
            time_startIter = time.time()
            # Set the trial solution to the last solution found
            TrySolnLvl = level.copy()
            TrySolnCaps = capacity.copy()

            [pBikeCost, mBikeCost, pCapCost, mCapCost, pBikeCapCost, mBikeCapCost] = initializeEmptyLists(numToInitialize=6)
            # Generate the cost table of the change in objective wrt/ +bike, -bike, +dock, -dock, +bike&dock, -bike&dock.
            for sid in sM.keys():
                currentCost = calculateStationObj(arrowDict, sid, TrySolnLvl, TrySolnCaps, 0, 0)
                pBikeCost.append([sid, calculateStationObj(arrowDict, sid, TrySolnLvl, TrySolnCaps, nMove, 0) - currentCost])
                mBikeCost.append([sid, calculateStationObj(arrowDict, sid, TrySolnLvl, TrySolnCaps, -nMove, 0) - currentCost])
                pCapCost.append([sid, calculateStationObj(arrowDict, sid, TrySolnLvl, TrySolnCaps, 0, nMove) - currentCost])
                mCapCost.append([sid, calculateStationObj(arrowDict, sid, TrySolnLvl, TrySolnCaps, 0, -nMove) - currentCost])
                pBikeCapCost.append([sid, calculateStationObj(arrowDict, sid, TrySolnLvl, TrySolnCaps, nMove, nMove) - currentCost])
                mBikeCapCost.append([sid, calculateStationObj(arrowDict, sid, TrySolnLvl, TrySolnCaps, -nMove, -nMove) - currentCost])

            # Sort by the contribution to the objective in increasing order.
            pBikeCost.sort(key=operator.itemgetter(1))
            mBikeCost.sort(key=operator.itemgetter(1))
            pCapCost.sort(key=operator.itemgetter(1))
            mCapCost.sort(key=operator.itemgetter(1))
            pBikeCapCost.sort(key=operator.itemgetter(1))
            mBikeCapCost.sort(key=operator.itemgetter(1))

            seed += 1
            random.seed(seed) # only used for selecting the sids
            for m in range(nMatch):
                # Try randomize the chosen pairs
                chosenInd = [random.randint(0, maxInd) for i in range(6)]

                # Get a target [sid, cost] in each of the following categories
                # pBike - add bike
                # mBike - remove bike
                # pCap - add dock
                # mCap - remove dock
                # pBikeCap - add bike and dock
                # mBikeCap - remove bike and dock
                pBike = pBikeCost[chosenInd[0]]
                mBike = mBikeCost[chosenInd[1]]
                pCap = pCapCost[chosenInd[2]]
                mCap = mCapCost[chosenInd[3]]
                pBikeCap = pBikeCapCost[chosenInd[4]]
                mBikeCap = mBikeCapCost[chosenInd[5]]

                # Pop remove the infeasible sids after nMove from the cost table
                # TO DO: make this prettier
                while TrySolnLvl[pBike[0]] + nMove > TrySolnCaps[pBike[0]]:
                    pBikeCost.pop(chosenInd[0])
                    s = returnIndexSid(pBikeCapCost, pBike[0])
                    if s:
                        pBikeCapCost.pop(s)
                        pBikeCap = pBikeCapCost[chosenInd[4]]
                    pBike = pBikeCost[chosenInd[0]]
                
                while TrySolnLvl[mBike[0]] - nMove < 0:
                    mBikeCost.pop(chosenInd[1])
                    s = returnIndexSid(mBikeCapCost, mBike[0])
                    if s:
                        mBikeCapCost.pop(s)
                        mBikeCap = mBikeCapCost[chosenInd[5]]
                    mBike = mBikeCost[chosenInd[1]]
               
                while TrySolnCaps[pCap[0]] + nMove > maxCap:
                    pCapCost.pop(chosenInd[2])
                    s = returnIndexSid(pBikeCapCost, pCap[0])
                    if s:
                        pBikeCapCost.pop(s)
                        pBikeCap = pBikeCapCost[chosenInd[4]]
                    pCap = pCapCost[chosenInd[2]]
                
                while TrySolnCaps[mCap[0]] - nMove < minCap:
                    mCapCost.pop(chosenInd[3])
                    s = returnIndexSid(mBikeCapCost, mCap[0])
                    if s:
                        mBikeCapCost.pop(s)
                        mBikeCap = mBikeCapCost[chosenInd[5]]
                    mCap = mCapCost[chosenInd[3]]
                
                tooManyBike = TrySolnLvl[pBikeCap[0]] + nMove > TrySolnCaps[pBikeCap[0]]
                tooManyDock = TrySolnCaps[pBikeCap[0]] + nMove > maxCap
                while tooManyBike or tooManyDock:
                    pBikeCapCost.pop(chosenInd[4])
                    if tooManyBike: 
                        pBikeCost.pop(returnIndexSid(pBikeCost, pBikeCap[0]))
                        pBike = pBikeCost[chosenInd[0]]
                    else:
                        pCapCost.pop(returnIndexSid(pCapCost, pBikeCap[0]))
                        pCap = pCapCost[chosenInd[2]]
                    pBikeCap = pBikeCapCost[chosenInd[4]]
                    tooManyBike = TrySolnLvl[pBikeCap[0]] + nMove > TrySolnCaps[pBikeCap[0]]
                    tooManyDock = TrySolnCaps[pBikeCap[0]] + nMove > maxCap

                tooFewBike = TrySolnLvl[pBikeCap[0]] + nMove > TrySolnCaps[pBikeCap[0]]
                tooFewDock = TrySolnCaps[mBikeCap[0]] - nMove < minCap
                while tooFewDock or tooFewBike:
                    mBikeCapCost.pop(chosenInd[5])
                    if tooFewBike:
                        mBikeCost.pop(returnIndexSid(mBikeCost, mBikeCap[0]))
                        mBike = pBikeCost[chosenInd[1]]
                    else:
                        mCapCost.pop(returnIndexSid(mCapCost, mBikeCap[0]))
                        mCap = mCapCost[chosenInd[3]]
                    mBikeCap = mBikeCapCost[chosenInd[5]]
                    tooFewBike = TrySolnLvl[pBikeCap[0]] + nMove > TrySolnCaps[pBikeCap[0]]
                    tooFewDock = TrySolnCaps[mBikeCap[0]] - nMove < minCap

                # Consider the following 5 movements and choose the best one. Then recalculate the cost for the chosen sids and resort table.
                # 0 - move bike from i to j
                # 1 - move empty dock from i to j
                # 2 - move bike and dock from i to j
                # 3 - remove bike and dock from i, allocate them separately to j and k
                # 4 - collect bike and dock separately from j and k. add together to i
                # TODO: 1) can heapify if not randmize (always pop 0). 2) recalculate other cost list too.
                possibeDeltaCost = [pBike[1] + mBike[1], pCap[1] + mCap[1], pBikeCap[1] + mBikeCap[1], mBikeCap[1] + pBike[1] + pCap[1], mBike[1] + mCap[1] + pBikeCap[1]] # see above for index
                bestMove = min(enumerate(possibeDeltaCost), key=operator.itemgetter(1))[0]
                if bestMove == 0:
                    s1 = pBike[0]
                    s2 = mBike[0]
                    TrySolnLvl[s1] += nMove
                    TrySolnLvl[s2] -= nMove
                    logger1.debug( ("Trying pBike, mBike = " + str(pBike[0]) + ", " + str(mBike[0])) )

                    # Recalculate cost table entries for pBike and mBike
                    pBikeCost[chosenInd[0]][1] = calculateStationObj(arrowDict, s1, TrySolnLvl, TrySolnCaps, nMove, 0) - currentCost
                    pBikeCost.sort(key=operator.itemgetter(1))
                    mBikeCost[chosenInd[1]][1] = calculateStationObj(arrowDict, s2, TrySolnLvl, TrySolnCaps, -nMove, 0) - currentCost
                    mBikeCost.sort(key=operator.itemgetter(1))
                    # Also recalculate cost table entries for pBikeCap and mBikeCap
                    i3 = returnIndexSid(pBikeCapCost, s1)
                    if i3: # may have been removed because adding dock is infeasible
                        pBikeCapCost[i3][1] = calculateStationObj(arrowDict, s1, TrySolnLvl, TrySolnCaps, nMove, nMove) - currentCost
                        pBikeCapCost.sort(key=operator.itemgetter(1))
                    i4 = returnIndexSid(mBikeCapCost, s2)
                    if i4:
                        mBikeCapCost[i4][1] = calculateStationObj(arrowDict, s2, TrySolnLvl, TrySolnCaps, -nMove, -nMove) - currentCost
                        mBikeCapCost.sort(key=operator.itemgetter(1))

                elif bestMove == 1:
                    s1 = pCap[0]
                    s2 = mCap[0]
                    TrySolnCaps[pCap[0]] += nMove
                    TrySolnCaps[mCap[0]] -= nMove
                    logger1.debug( ("Trying pCap, mCap = " + str(pCap[0]) + ", " + str(mCap[0])) )

                    # Recalculate cost table entries for pCap and mCap
                    pCapCost[chosenInd[2]][1] = calculateStationObj(arrowDict, s1, TrySolnLvl, TrySolnCaps, 0, nMove) - currentCost
                    pCapCost.sort(key=operator.itemgetter(1))
                    mCapCost[chosenInd[3]][1] = calculateStationObj(arrowDict, s2, TrySolnLvl, TrySolnCaps, 0, -nMove) - currentCost
                    mCapCost.sort(key=operator.itemgetter(1))
                    # Also recalculate cost table entries for pBikeCap and mBikeCap
                    i3 = returnIndexSid(pBikeCapCost, s1)
                    if i3:
                        pBikeCapCost[i3][1] = calculateStationObj(arrowDict, s1, TrySolnLvl, TrySolnCaps, nMove, nMove) - currentCost
                        pBikeCapCost.sort(key=operator.itemgetter(1))
                    i4 = returnIndexSid(mBikeCapCost, s2)
                    if i4:
                        mBikeCapCost[i4][1] = calculateStationObj(arrowDict, s2, TrySolnLvl, TrySolnCaps, -nMove, -nMove) - currentCost
                        mBikeCapCost.sort(key=operator.itemgetter(1))

                elif bestMove == 2:
                    s1 = pBikeCap[0]
                    s2 = mBikeCap[0]
                    TrySolnCaps[s1] += nMove
                    TrySolnCaps[s2] -= nMove
                    TrySolnLvl[s1] += nMove
                    TrySolnLvl[s2] -= nMove
                    logger1.debug( ("Trying pBikeCap, mBikeCap = " + str(pBikeCap[0]) + ", " + str(mBikeCap[0])) )

                    # Recalculate cost table entries for pBikeCap and mBikeCap
                    pBikeCapCost[chosenInd[4]][1] = calculateStationObj(arrowDict, s1, TrySolnLvl, TrySolnCaps, nMove, nMove) - currentCost
                    pBikeCapCost.sort(key=operator.itemgetter(1))
                    mBikeCapCost[chosenInd[5]][1] = calculateStationObj(arrowDict, s2, TrySolnLvl, TrySolnCaps, -nMove, -nMove) - currentCost
                    mBikeCapCost.sort(key=operator.itemgetter(1))
                    # Also recalculate cost table entries for pBike, pCap and mBike, mCap
                    i3 = returnIndexSid(pBike, s1)
                    pBikeCost[i3][1] = calculateStationObj(arrowDict, s1, TrySolnLvl, TrySolnCaps, nMove, 0) - currentCost
                    pBikeCost.sort(key=operator.itemgetter(1))
                    i4 = returnIndexSid(pCap, s1)
                    pCapCost[i4][1] = calculateStationObj(arrowDict, s1, TrySolnLvl, TrySolnCaps, 0, nMove) - currentCost
                    pCapCost.sort(key=operator.itemgetter(1))
                    i5 = returnIndexSid(mBike, s2)
                    mBikeCost[i5][1] = calculateStationObj(arrowDict, s2, TrySolnLvl, TrySolnCaps, -nMove, 0) - currentCost
                    mBikeCost.sort(key=operator.itemgetter(1))
                    i6 = returnIndexSid(mCap, s2)
                    mCapCost[i6][1] = calculateStationObj(arrowDict, s2, TrySolnLvl, TrySolnCaps, 0, -nMove) - currentCost
                    mCapCost.sort(key=operator.itemgetter(1))

                elif bestMove == 3:
                    s1 = mBikeCap[0]
                    s2 = pBike[0]
                    s3 = pCap[0]
                    TrySolnCaps[s1] -= nMove
                    TrySolnLvl[s1] -= nMove
                    TrySolnLvl[s2] += nMove
                    TrySolnCaps[s3] += nMove
                    logger1.debug( ("Trying mBikeCap, pBike, pCap = " + str(mBikeCap[0]) + ", " + str(pBike[0]) + ", " + str(pCap[0])) )

                    # Recalculate cost table entries for mBikeCap, pBike, and pCap
                    mBikeCapCost[chosenInd[5]][1] = calculateStationObj(arrowDict, s1, TrySolnLvl, TrySolnCaps, -nMove, -nMove) - currentCost
                    mBikeCapCost.sort(key=operator.itemgetter(1))
                    pBikeCost[chosenInd[0]][1] = calculateStationObj(arrowDict, s2, TrySolnLvl, TrySolnCaps, nMove, 0) - currentCost
                    pBikeCost.sort(key=operator.itemgetter(1))
                    pCapCost[chosenInd[2]][1] = calculateStationObj(arrowDict, s3, TrySolnLvl, TrySolnCaps, 0, nMove) - currentCost
                    pCapCost.sort(key=operator.itemgetter(1))
                    # Also recalculate cost table entries for pBikeCap and mBike, mCap
                    i3 = returnIndexSid(pBikeCapCost, s1)
                    pBikeCapCost[i3][1] = calculateStationObj(arrowDict, s1, TrySolnLvl, TrySolnCaps, nMove, nMove) - currentCost
                    pBikeCapCost.sort(key=operator.itemgetter(1))
                    i4 = returnIndexSid(mBike, s1)
                    mBikeCost[i4][1] = calculateStationObj(arrowDict, s1, TrySolnLvl, TrySolnCaps, -nMove, 0) - currentCost
                    mBikeCost.sort(key=operator.itemgetter(1))
                    i5 = returnIndexSid(mBikeCapCost, s2)
                    if i5:
                        mBikeCapCost[i5][1] = calculateStationObj(arrowDict, s2, TrySolnLvl, TrySolnCaps, -nMove, -nMove) - currentCost
                        mBikeCapCost.sort(key=operator.itemgetter(1))
                    i6 = returnIndexSid(mBikeCapCost, s3)
                    if i6:
                        mBikeCapCost[i6][1] = calculateStationObj(arrowDict, s3, TrySolnLvl, TrySolnCaps, -nMove, -nMove) - currentCost
                        mBikeCapCost.sort(key=operator.itemgetter(1))

                elif bestMove == 4:
                    s1 = pBikeCap[0]
                    s2 = mBike[0]
                    s3 = mCap[0]
                    TrySolnCaps[s1] += nMove
                    TrySolnLvl[s1] += nMove
                    TrySolnLvl[s2] -= nMove
                    TrySolnCaps[s3] -= nMove
                    logger1.debug( ("Trying pBikeCap, mBike, mCap = " + str(pBikeCap[0]) + ", " + str(mBike[0]) + ", " + str(mCap[0])) )

                    # Recalculate cost table entries for pBikeCap, mBike, mCap
                    pBikeCapCost[chosenInd[4]][1] = calculateStationObj(arrowDict, s1, TrySolnLvl, TrySolnCaps, nMove, nMove) - currentCost
                    pBikeCapCost.sort(key=operator.itemgetter(1))
                    mBikeCost[chosenInd[1]][1] = calculateStationObj(arrowDict, s2, TrySolnLvl, TrySolnCaps, -nMove, 0) - currentCost
                    mBikeCost.sort(key=operator.itemgetter(1))
                    mCapCost[chosenInd[3]][1] = calculateStationObj(arrowDict, s3, TrySolnLvl, TrySolnCaps, 0, -nMove) - currentCost
                    mCapCost.sort(key=operator.itemgetter(1))
                    # Also recalculate cost table entries for pBike, pCap, and mBikeCap
                    i3 = returnIndexSid(pBike, s1)
                    pBikeCost[i3][1] = calculateStationObj(arrowDict, s1, TrySolnLvl, TrySolnCaps, nMove, 0) - currentCost
                    pBikeCost.sort(key=operator.itemgetter(1))
                    i4 = returnIndexSid(pCap, s1)
                    pCapCost[i4][1] = calculateStationObj(arrowDict, s1, TrySolnLvl, TrySolnCaps, 0, nMove) - currentCost
                    pCapCost.sort(key=operator.itemgetter(1))
                    i5 = returnIndexSid(mBikeCap, s2)
                    if i5:
                        mBikeCapCost[i5][1] = calculateStationObj(arrowDict, s2, TrySolnLvl, TrySolnCaps, -nMove, -nMove) - currentCost
                        mBikeCapCost.sort(key=operator.itemgetter(1))
                    i6 = returnIndexSid(mBikeCap, s3)
                    if i6:
                        mBikeCapCost[i6][1] = calculateStationObj(arrowDict, s3, TrySolnLvl, TrySolnCaps, -nMove, -nMove) - currentCost
                        mBikeCapCost.sort(key=operator.itemgetter(1))

            # Simulate the trial solution.
            simCount += rep
            solutionList1, obj1, ciwidth1, arrowDict1 = simulate(TrySolnLvl, TrySolnCaps, sM, rep, daySeed, mbm, durations, simMethod, startTime, numIntervals)
            diff = obj0 - obj1

            # Make the move if improving.
            # if improved, do the swap, else, restore solution.
            if diff > 0.0:
                improve = diff
                level = TrySolnLvl # points to the trial soln
                capacity = TrySolnCaps
                obj0 = obj1
                results[simCount] = obj1
                logger1.warning( ("Improve: Obj1 = " + str(obj1) + " with ciwidth " + str(ciwidth1) +
                    " by " + str(diff)) )
                failedswap = 0 # suceed, reset number of attempts for this starting soln
                failedSinceLastChange = 0
            else:
                failedswap += 1
                failedSinceLastChange += 1
                if nMatch > 1 and failedSinceLastChange > 30:
                    nMatch = nMatch / 2
                    failedSinceLastChange = 0
                logger1.info( ("Failed trying the trial solution. Failed number: " + str(failedswap)) )

            logger1.warning( "nMatch " + str(nMatch) + ", last improvement " + str(improve) + ", last obj" + str(obj0) + ", simCount" + str(simCount) +
                                       ", iteration time " + str(time.time() - time_startIter))

            if simCount % (rep*10) == 0: # store every 10 iterations
                storePickle(results, level, capacity, fileName)

        except KeyboardInterrupt:
            print '\nPausing...  (Hit ENTER to continue, type quit to stop optimization and record solutions, type break to exit immediately.)'
            try:
                response = raw_input()
                if response == 'quit':
                    break
                elif response == 'break':
                    return
                print 'Resuming...'
            except KeyboardInterrupt:
                print 'Resuming...'
                continue

    solutionListFinal, objFinal, ciwidthFinal, _ = simulate(level, capacity, sM, 100, daySeed+1, mbm, durations, simMethod, startTime, numIntervals)
    end = time.time()
    logger1.warning( ("Starting objective value: " + str(obj00) + ",  ciwidth: " + str(ciwidth00)) )
    logger1.warning( ("Final objective value: " + str(objFinal) + ", Final ciwidth: " + str(ciwidthFinal)) )
    logger1.warning( ("Total solutions evaluated by simulation = " + str(simCount/rep)) )
    logger1.warning( ("Last failed number of swaps = " + str(failedswap)) )
    logger1.warning( ("Elapsed time: " + str(end-start)) )
    storePickle(results, level, capacity, fileName)

    return

def storePickle(results, level, capacity, fileName):
    fileName1 = ("./outputsDO/%s.p" % (fileName + 'CapsResults'))
    fileName2 = ("./outputsDO/%s.p" % (fileName + 'CapsLevel'))
    fileName3 = ("./outputsDO/%s.p" % (fileName + 'CapsCapacity'))
    # fileName4 = ("./outputsDO/%s.p" % (fileName + 'CapsFailedSwaps'))
    cPickle.dump(results, open(fileName1, 'wb'))
    cPickle.dump(level, open(fileName2, 'wb'))
    cPickle.dump(capacity, open(fileName3, 'wb'))
    # cPickle.dump(failedSwapPairs, open(fileName4, 'wb'))


if __name__ == '__main__':
    ''' Configurations '''
    seed = 9
    start = 6
    end = 10
    rep = 30 # replications to evaluate each trial solution
    nMove = 1 # number of bikes/racks to move at each station
    nMatch = 32 # max allowed matches of station pairs to move bike/dock
    maxInd = 30 # randomize between top 1 and top maxInd sids in the cost table

    startTime = int(start*60) # simulation start time (minutes, from 0 to 1439)
    numIntervals = int(2*(end-start)) # number of 30-minute intervals to simulate
    #solutionFile = 'CTMCVaryRate' + str(start) + "-" + str(end) + '_15x'
    #solutionName = 'CTMCVaryRate' + str(start) + "to" + str(end) + '_15x'
    #solutionName = 'AverageAllocation'
    #solutionFile = 'AverageAllocationFromNamesConstrained'
    solutionFile = 'fluidModelUB_Dec15x'
    solutionName = 'FluidModel'
    fileInd = numpy.random.randint(1,99)
    fileName = (solutionName + "id" + str(fileInd) + "CapsTable")

    ''' Logging to File '''
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename='./outputsDO/%sid%iCapsTable.log' % (solutionName, fileInd),
                        filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    logging.info('gradSearchCapsTable.py')
    logging.info('Purpose of the run: testing table method starting from fluidModel 6-10')
    logging.info(('random seed = ' + str(seed)))
    logging.info(('solution name = ' + fileName))

    # get state map info (caps, ords)
    # sM = eval(open(('./data/'+solutionFile+'.txt')).read())
    sM = cPickle.load(open('./data/%s.p' % solutionFile, 'r'))
    sM[-1000] = {'bikes':-1000, 'capacity':-1000, 'ords':(0,0), 'name':"null"}
    logging.info('Finished loading station map.')

    # get durations
    durationMult = eval(open('./data/durationsLNMultiplier2.txt').read())
    logging.info('Finished loading durations multiplier.')

    # get min-by-min data
    mbm = cPickle.load(open("./data/mbm30minDec_15x.p", 'r'))
    logging.info('Finished loading flow rates.')

    ''' Simulate and Optimize! '''
    config = [seed, rep, nMatch, nMove, maxInd]
    # time, objFinal, ciwidthFinal, obj00, ciwidth00 = randomSearch(sM,mbm,durationMult,fileName,
                                                            # startTime,numIntervals,config)
    randomSearch(sM,mbm,durationMult,fileName,startTime,numIntervals,config)
    # logging.warning( ("Random search id: " + str(fileInd) + ", solution: " + str(objFinal) +
    #                 ", ciwidth: " + str(ciwidthFinal) + ", elapsed time:" + str(time)) )


    ''' Just Simulate! '''
    # level = {} # level of bikes at each station at the beginning of the day
    # capacity = {} # capacity of each station
    # for sid in sM:
    #     level[sid] = sM[sid]['bikes']
    #     capacity[sid] = sM[sid]['capacity']
    # simulate(level, capacity, sM, 1, seed, mbm, durationMult, "AltCond", 360, 8)
