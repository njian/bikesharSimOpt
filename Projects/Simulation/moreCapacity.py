'''
Optimizing both bike and capacity allocations using the "table" method.
Instead of moving between one pair of stations, move between multiple pairs based on the cost table.
This is the version with random index when choosing each pair of station.

Nanjing Jian, last updated 2016/09
'''

import SimulationRunnerCapsTable as SimulationRunnerCaps
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

    for i in range(rep):
        data = SimulationRunnerCaps.testVehicles2(level, capacity, sM, mbm, durations,
            simMethod, startTime, numIntervals)
        solutionList[i] = data[0:3]
        solutionList2.append(float(sum(data[0:3])))
        arrowDict[i] = data[3]

    # cPickle.dump(arrowDict, open('arrowDict.p','wb'))

    obj = round(numpy.mean(solutionList2, axis=0), 2)
    ciwidth = round(numpy.std(solutionList2)*1.96/numpy.sqrt(rep), 2)

    return (solutionList, obj, ciwidth, arrowDict)


def calculateStationObj(arrowDict, sid, level, capacity):
    ''' Goes through the arrowList and 'simulate' the avg. objective if the
        starting level and capacity is as inputted.

    Args:
    rep: The replication number where the objective is returned.
    arrowDict: {rep: {sid: ordered list of [+1 for inflow, -1 for outflow]}}
    sid: The prompted station id.
    level: The hypothetical starting bike level of sid.
    capacity: The hypothetical starting capacity of sid.

    Returns: The average contributon of station sid to the objective over
             replications.
    '''
    # First put huge cost on infeasible solutions
    if level > capacity or level < 0 or capacity < 0: # or capacity > maxCap
        return 9999

    obj = [0]*len(arrowDict.keys()) # length = #replications
    for rep in arrowDict.keys(): # replication
        l = level
        for x in arrowDict[rep][sid]:
            if l + x > capacity or l + x < 0:
                obj[rep] += 1
            else: l += x
    return round(numpy.mean(obj, axis=0), 2)


def calculateTotalObj(arrowDict, level, capacity):
    ''' Returns the total objective value over all stations. '''
    obj = 0
    for sid in arrowDict[0].keys():
        obj += calculateStationObj(arrowDict, sid, level[sid], capacity[sid])
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


# def getKeyOfMax(d):
#     ''' Returns the key of the max item in dictionary d '''
#     return max(d.iteritems(), key=operator.itemgetter(1))[0]


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
    maxCap = 99
    # maxCap = {}
    # for sid in sM.keys():
    #     maxCap[sid] = 80 if sid == 477 or sid == 519 or sid == 432 else 60
    minCap = 0 # min capacity of a station when optimizing
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
                currentCost = calculateStationObj(arrowDict, sid, TrySolnLvl[sid], TrySolnCaps[sid])
                pBikeCost.append([sid, calculateStationObj(arrowDict, sid, TrySolnLvl[sid] + nMove, TrySolnCaps[sid]) - currentCost])
                mBikeCost.append([sid, calculateStationObj(arrowDict, sid, TrySolnLvl[sid] - nMove, TrySolnCaps[sid]) - currentCost])
                pCapCost.append([sid, calculateStationObj(arrowDict, sid, TrySolnLvl[sid] , TrySolnCaps[sid] + nMove) - currentCost])
                mCapCost.append([sid, calculateStationObj(arrowDict, sid, TrySolnLvl[sid] , TrySolnCaps[sid] - nMove) - currentCost])
                pBikeCapCost.append([sid, calculateStationObj(arrowDict, sid, TrySolnLvl[sid] + nMove , TrySolnCaps[sid] + nMove) - currentCost])
                mBikeCapCost.append([sid, calculateStationObj(arrowDict, sid, TrySolnLvl[sid] - nMove , TrySolnCaps[sid] - nMove) - currentCost])

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
                    pBike = pBikeCost[chosenInd[0]]
                while TrySolnLvl[mBike[0]] - nMove < 0:
                    mBikeCost.pop(chosenInd[1])
                    mBike = mBikeCost[chosenInd[1]]
                while TrySolnCaps[pCap[0]] + nMove > maxCap:
                    pCapCost.pop(chosenInd[2])
                    pCap = pCapCost[chosenInd[2]]
                while TrySolnCaps[mCap[0]] - nMove < minCap:
                    mCapCost.pop(chosenInd[3])
                    mCap = mCapCost[chosenInd[3]]
                while TrySolnLvl[pBikeCap[0]] + nMove > TrySolnCaps[pBikeCap[0]] or TrySolnCaps[pBikeCap[0]] + nMove > maxCap:
                    pBikeCapCost.pop(chosenInd[4])
                    pBikeCap = pBikeCapCost[chosenInd[4]]
                while TrySolnCaps[mBikeCap[0]] - nMove < minCap or TrySolnLvl[mBikeCap[0]] - nMove < 0:
                    mBikeCapCost.pop(chosenInd[5])
                    mBikeCap = mBikeCapCost[chosenInd[5]]

                # Consider the following 5 movements and choose the best one.
                # TODO: fix index m to not skip the ones visited.
                # 0 - move bike from i to j
                # 1 - move empty dock from i to j
                # 2 - move bike and dock from i to j
                # 3 - remove bike and dock from i, allocate them separately to j and k
                # 4 - collect bike and dock separately from j and k. add together to i
                possibeDeltaCost = [pBike[1] + mBike[1], pCap[1] + mCap[1], pBikeCap[1] + mBikeCap[1], mBikeCap[1] + pBike[1] + pCap[1], mBike[1] + mCap[1] + pBikeCap[1]] # see above for index
                bestMove = min(enumerate(possibeDeltaCost), key=operator.itemgetter(1))[0]
                if bestMove == 0:
                    TrySolnLvl[pBike[0]] += nMove
                    TrySolnLvl[mBike[0]] -= nMove
                    logger1.debug( ("Trying pBike, mBike = " + str(pBike[0]) + ", " + str(mBike[0])) )
                elif bestMove == 1:
                    TrySolnCaps[pCap[0]] += nMove
                    TrySolnCaps[mCap[0]] -= nMove
                    logger1.debug( ("Trying pCap, mCap = " + str(pCap[0]) + ", " + str(mCap[0])) )
                elif bestMove == 2:
                    TrySolnCaps[pBikeCap[0]] += nMove
                    TrySolnCaps[mBikeCap[0]] -= nMove
                    TrySolnLvl[pBikeCap[0]] += nMove
                    TrySolnLvl[mBikeCap[0]] -= nMove
                    logger1.debug( ("Trying pBikeCap, mBikeCap = " + str(pBikeCap[0]) + ", " + str(mBikeCap[0])) )
                elif bestMove == 3:
                    TrySolnCaps[mBikeCap[0]] -= nMove
                    TrySolnLvl[mBikeCap[0]] -= nMove
                    TrySolnCaps[pCap[0]] += nMove
                    TrySolnLvl[pBike[0]] += nMove
                    logger1.debug( ("Trying mBikeCap, pBike, pCap = " + str(mBikeCap[0]) + ", " + str(pBike[0]) + ", " + str(pCap[0])) )
                elif bestMove == 4:
                    TrySolnCaps[pBikeCap[0]] += nMove
                    TrySolnLvl[pBikeCap[0]] += nMove
                    TrySolnCaps[mCap[0]] -= nMove
                    TrySolnLvl[mBike[0]] -= nMove
                    logger1.debug( ("Trying pBikeCap, mBike, mCap = " + str(pBikeCap[0]) + ", " + str(mBike[0]) + ", " + str(mCap[0])) )

            # Simulate the trial solution.
            simCount += rep
            solutionList1, obj1, ciwidth1, arrowDict1 = simulate(TrySolnLvl, TrySolnCaps, sM, rep, daySeed, mbm, durations, simMethod, startTime, numIntervals)
            diff = obj0 - obj1

            # Make the move if improving.
            # if improved, do the swap, else, restore solution.
            if diff >= 0.0:
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
                storePickle(results, level, capacity, pBikeCost, mBikeCost, pCapCost, mCapCost, pBikeCapCost, mBikeCapCost, fileName)

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
    storePickle(results, level, capacity, pBikeCost, mBikeCost, pCapCost, mCapCost, pBikeCapCost, mBikeCapCost, fileName)

    return

def storePickle(results, level, capacity, pBikeCost, mBikeCost, pCapCost, mCapCost, pBikeCapCost, mBikeCapCost, fileName):
    fileName1 = ("./outputsDO/%s.p" % (fileName + 'CapsResults'))
    fileName2 = ("./outputsDO/%s.p" % (fileName + 'CapsLevel'))
    fileName3 = ("./outputsDO/%s.p" % (fileName + 'CapsCapacity'))
    # fileName4 = ("./outputsDO/%s.p" % (fileName + 'CapsFailedSwaps'))
    cPickle.dump(results, open(fileName1, 'wb'))
    cPickle.dump(level, open(fileName2, 'wb'))
    cPickle.dump(capacity, open(fileName3, 'wb'))

    cPickle.dump(pBikeCost, open(("./outputsDO/%spBikeCost.p" % fileName), 'wb'))
    cPickle.dump(mBikeCost, open(("./outputsDO/%smBikeCost.p" % fileName), 'wb'))
    cPickle.dump(pCapCost, open(("./outputsDO/%spCapCost.p" % fileName), 'wb'))
    cPickle.dump(mCapCost, open(("./outputsDO/%smCapCost.p" % fileName), 'wb'))
    cPickle.dump(pBikeCapCost, open(("./outputsDO/%spBikeCapCost.p" % fileName), 'wb'))
    cPickle.dump(mBikeCapCost, open(("./outputsDO/%smBikeCapCost.p" % fileName), 'wb'))

    # cPickle.dump(failedSwapPairs, open(fileName4, 'wb'))


if __name__ == '__main__':
    ''' Configurations '''
    seed = 9
    start = 6
    end = 24
    rep = 30 # replications to evaluate each trial solution
    nMove = 1 # number of bikes/racks to move at each station
    nMatch = 32 # max allowed matches of station pairs to move bike/dock
    maxInd = 30 # randomize between top 1 and top maxInd sids in the cost table

    startTime = int(start*60) # simulation start time (minutes, from 0 to 1439)
    numIntervals = int(2*(end-start)) # number of 30-minute intervals to simulate
    # solutionFile = 'CTMCVaryRate' + str(start) + "-" + str(end) + '_15x'
    # solutionName = 'CTMCVaryRate' + str(start) + "to" + str(end) + '_15x'
    #solutionFile = 'AverageAllocationFromNamesConstrained'
    #solutionName = 'AverageAllocation' + str(start) + "-" + str(end)
    solutionFile = 'fluidModelUB_Dec15x'
    # solutionName = 'FluidModel' + str(start) + "-" + str(end)
    solutionName = 'CTMCVaryRate6to24_15xid12'
    fileInd = numpy.random.randint(1,99)
    fileName = (solutionName + "id" + str(fileInd) + "CapsTableRn")

    ''' Logging to File '''
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename='./outputsDO/%sid%iCapsTableRn.log' % (solutionName, fileInd),
                        filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    logging.info('gradSearchCapsTableRn.py')
    logging.info('Purpose of the run: restart from CTMCVaryRate6to24_15xid12CapsTableRnCaps without constraints of maxCaps and minCaps')
    logging.info(('random seed = ' + str(seed)))
    logging.info(('solution name = ' + fileName))

    # get state map info (caps, ords)
    # sM = eval(open(('./data/'+solutionFile+'.txt')).read())
    sM = cPickle.load(open('./data/%s.p' % solutionFile, 'r'))
    capacity = cPickle.load(open('./outputsDO/CTMCVaryRate6to24_15xid12CapsTableRnCapsCapacity.p', 'r'))
    level = cPickle.load(open('./outputsDO/CTMCVaryRate6to24_15xid12CapsTableRnCapsLevel.p', 'r'))
    for sid in sM:
        sM[sid]['bikes'] = level[sid]
        sM[sid]['capacity'] = capacity[sid]
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
    time, objFinal, ciwidthFinal, obj00, ciwidth00 = randomSearch(sM,mbm,durationMult,fileName,
                                                            startTime,numIntervals,config)
    randomSearch(sM,mbm,durationMult,fileName,startTime,numIntervals,config)
    logging.warning( ("Random search id: " + str(fileInd) + ", solution: " + str(objFinal) +
                    ", ciwidth: " + str(ciwidthFinal) + ", elapsed time:" + str(time)) )


    ''' Just Simulate! '''
    # level = {} # level of bikes at each station at the beginning of the day
    # capacity = {} # capacity of each station
    # for sid in sM:
    #     level[sid] = sM[sid]['bikes']
    #     capacity[sid] = sM[sid]['capacity']
    # simulate(level, capacity, sM, rep, seed, mbm, durationMult, "AltCond", 360, 8)
