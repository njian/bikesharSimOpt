import SimulationRunnerCaps
import math, random
import numpy
import time
import cPickle
from collections import Counter
import logging

def simulate(level, capacity, sM, rep, seed, mbm, durations, simMethod="AltCond",
    startTime=420, numIntervals=4):
    ''' Optimize bikes and docks, need statC '''
    # t0 = time.time()
    numpy.random.seed(seed) # starting seed for round of reps
    soln = 0
    s1 = []
    s2 = []
    solutionList = {}
    solutionList2 = []

    for i in range(rep):
        data = SimulationRunnerCaps.testVehicles2(level, capacity, sM, mbm, durations,
            simMethod, startTime, numIntervals)
        solutionList[i] = data[0:3]
        solutionList2.append(float(sum(data[0:3])))
        if data[3] != -1:
            s1.extend(data[3]) # all failed start sids in this rep
        if data[4] != -1:
            s2.extend(data[4]) # all failed end sids in this rep

    obj = round(numpy.mean(solutionList2, axis=0), 2)
    ciwidth = round(numpy.std(solutionList2)*1.96/numpy.sqrt(rep), 2)
    statE = Counter(s1).most_common() # produces a list with [0]=sid and [1]=failedStarts
    statF = Counter(s2).most_common() # produces a list with [0]=sid and [1]=failedEnds
    statC = Counter(s1+s2).most_common() # produces a list with [0]=sid and [1]=failedStarts+failedEnds
    # statC = sorted(totalOutage, key=totalOutage.get, reverse=False)
    # print "time in simulate(): ", time.time() - t0, ", rep: ", rep
    return (solutionList, obj, ciwidth, statE, statF, statC)

def randomSearch(sM,mbm,durations,fileName,startTime,numIntervals,config):
    ''' Configurations '''
    rep = 30 # to evaluate each objective
    nswap = 3 # initial number to swap in each iteration
    logger1 = logging.getLogger('gradSearchCaps')
    daySeed = config[0]
    listLength = config[1]
    simulationMethod = config[2]
    # failedSwapPairs = []
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
    objAll, obj0, ciwidth, statE, statF, statC = simulate(level, capacity, sM, 30,
        daySeed, mbm, durations, simMethod, startTime, numIntervals)
    logger1.warning( ("Obj0: " + str(obj0) + " ciwidth " + str(ciwidth)) )
    obj00 = obj0
    ciwidth00 = ciwidth
    results = {}
    results[0] = objAll
    totalCapsChange = 0
    totalBikesChange = 0

    ''' Swapping Heuristics '''
    seed = daySeed
    failedswap = 0
    failedSinceLastChange = 0
    while True: # Stopping criteria
        try:
            if failedSinceLastChange > 150 and nswap - 1 >= 1:
                nswap -= 1
                failedSinceLastChange = 0

            # Select which stations to swap
            seed += 1
            random.seed(seed) # only used for selecting the sids
            ''' The top listLength empty stations '''
            nE = 0
            sidEList = []
            com = 0 # select the most common empty/full station at first
            logger1.debug( ("statE(listLength)", str(statE[:listLength])) )
            while nE<listLength and com<=len(statE)-1:
                sidE = statE[com][0]
                if sidE != -1: #and level[sidE] + nswap <= float(sM[sidE]['capacity']):
                    sidEList.append(sidE)
                    nE+=1
                com+=1
            ''' The top listLength full stations'''
            nF = 0
            sidFList = []
            com = 0
            logger1.debug( ("statF(listLength)", str(statF[:listLength])) )
            while nF<listLength and com<=len(statF)-1:
                sidF = statF[com][0]
                if sidF != -1: #and level[sidF] - nswap >= 0.0:
                    sidFList.append(sidF)
                    nF+=1
                com+=1
            ''' The top listLength 'stable' stations that can afford nswap capacity'''
            nC = 0
            sidCList = []
            com = 0
            logger1.debug( ("statC(listLength)", str(statC[:-listLength-1:-1])) )
            # listLength least outage station
            # Make sure can move nswap caps away from sidC
            while nC<listLength and com<=len(statC)-1:
                sidC = statC[-com][0] # the com-th least outage station
                if capacity[sidC] - nswap >= minCap and sidC != 3230 and sidC != 3236: # not depots
                    sidCList.append(sidC)
                    nC+=1
                com+=1
            logger1.debug( ("Feasible statC", str(sidCList)) )

            ''' Choose randomly from statE, statF, statC '''
            ''' Skips: in case the solution is very close to optimal so that statE, statF might be empty '''
            skip1 = False
            skip2 = False
            skip3 = False
            if nE == 0:
                sidE = -1000
                skip1 = True
                skip2 = True
            else:
                sidE = random.choice(sidEList)
            if nF == 0:
                sidF = -1000
                skip1 = True
                skip3 = True
            else:
                sidF = random.choice(sidFList)
            if nC == 0:
                sidC = -1000
                skip2 = True
                skip3 = True
            else:
                sidC = random.choice(sidCList)

            logger1.debug( ("list lengths: " + str(nE) + " , " + str(nF)  + " , " + str(nC)))

            logger1.warning( ("sidE (statE) " + str(sidE) + ", cap" + str(sM[sidE]['capacity']) + ", lvl " + str(level[sidE]) +
                "; sidF (statF) " + str(sidF) + ", cap" + str(sM[sidF]['capacity']) + ", lvl " + str(level[sidF])) )
            logger1.warning( ("sidC (statC) " + str(sidC) + ", lvl " + str(level[sidC]) +
                ", cap " + str(sM[sidC]['capacity'])) )

            ''' Generate the trial solution '''
            TrySolnLvl = level.copy()
            TrySolnCaps = capacity.copy()
            if (not skip1) and level[sidE] + nswap <= capacity[sidE] and level[sidF] - nswap >= 0:
                # Can move bikes between most empty (sidE) and most full stations (sidF)
                TrySolnLvl[sidE] += nswap
                TrySolnLvl[sidF] -= nswap
                logger1.info( ("Trying to move " + str(nswap) + " bikes from " + str(sidF) + " to " + str(sidE)) )
                # failedSwapPairs.append([sidF, sidE])
            else:
                logger1.debug("failed case 1")
                if (not skip2) and level[sidE] + nswap > capacity[sidE]:
                    #  Cannot move bikes because sidE is already full and gets empty quickly
                    if TrySolnCaps[sidE] + nswap <= maxCap:
                        while level[sidC] - nswap < 0:
                            sidC = random.choice(sidCList)
                        TrySolnLvl[sidE] += nswap
                        TrySolnLvl[sidC] -= nswap
                        TrySolnCaps[sidE] += nswap
                        TrySolnCaps[sidC] -= nswap
                    logger1.info( ("Trying to move " + str(nswap) + " bikes and caps from " + str(sidC) + " to " + str(sidE)) )
                    # failedSwapPairs.append([sidC, sidE])
                else:
                    logger1.debug("failed case 2")
                    if (not skip3) and TrySolnCaps[sidF] + nswap <= maxCap:
                        # Cannot move bikes because sidF doesn't have any initial bikes and still gets full quickly
                        TrySolnCaps[sidF] += nswap
                        TrySolnCaps[sidC] -= nswap
                        excessBikes = TrySolnLvl[sidC] - TrySolnCaps[sidC]
                        # If moving docks away from sidC makes its level overflow, move the excess to sidE
                        if excessBikes > 0: #(not skip2) and
                            TrySolnLvl[sidC] -= excessBikes
                            TrySolnLvl[sidE] += excessBikes
                        logger1.info( ("Trying to move " + str(nswap) + " caps from " + str(sidC) + " to " + str(sidF)) )
                        # failedSwapPairs.append([sidC, sidF])
                    else:
                        logger1.debug("failed case 3")

            ''' Simulate the trial solution '''
            simCount += rep
            objAll1, obj1, ciwidth1, statE, statF, statC = simulate(TrySolnLvl, TrySolnCaps, sM, rep, daySeed, mbm, durations, simMethod, startTime, numIntervals)
            diff = obj0 - obj1

            ''' Make the move if improving '''
            # if improved, do the swap, else, restore solution
            if diff>0.0:
                ''' Record total bikes and racks changes '''
                totalBikesChange += float(TrySolnLvl[sidE]) - float(level[sidE])
                totalCapsChange += float(capacity[sidC]) - float(TrySolnCaps[sidC])

                improve = diff
                level = TrySolnLvl # points to the trial soln
                capacity = TrySolnCaps
                obj0 = obj1
                results[simCount] = objAll1
                logger1.warning( ("Improve: Obj1 = " + str(obj1) + " with ciwidth " + str(ciwidth1) +
                    " by " + str(diff)) )
                failedswap = 0 # suceed, reset number of attempts for this starting soln
                failedSinceLastChange = 0
                # del failedSwapPairs[-1]

                logger1.warning( ("total capacity changes: " + str(totalCapsChange)) )
                logger1.warning( ("total bikes changes: " + str(totalBikesChange)) )
            else:
                failedswap += 1
                failedSinceLastChange += 1
                logger1.info( ("Failed trying the trial solution. Failed number: " + str(failedswap)) )

            logger1.warning( ("last improvement " + str(improve) + ", last obj" + str(obj0) + ", simCount" + str(simCount)) )

            if simCount % (rep*10) == 0: # store every 10 iterations
                storePickle(results, level, capacity, fileName)

        except KeyboardInterrupt:
            print '\nPausing...  (Hit ENTER to continue, type quit to stop optimization and record solutions, type break to exit immediately.)'
            try:
                response = raw_input()
                if response == 'quit':
                    break
                    objAllFinal, objFinal, ciwidthFinal, statE1, statF1, statC1 = simulate(level, capacity, sM, 100, daySeed+1, mbm, durations, simMethod, startTime, numIntervals)
                    end = time.time()
                    logging.info('Purpose of the run: CTMC soln for 6-10AM, caps')
                    logger1.warning( ("Starting objective value: " + str(obj00) + ",  ciwidth: " + str(ciwidth00)) )
                    logger1.warning( ("Final objective value: " + str(objFinal) + ", Final ciwidth: " + str(ciwidthFinal)) )
                    logger1.warning( ("total capacity changes: " + str(totalCapsChange)) )
                    logger1.warning( ("total bikes changes: " + str(totalBikesChange)) )
                    logger1.warning( ("Total solutions evaluated by simulation = " + str(simCount/rep)) )
                    logger1.warning( ("Last failed number of swaps = " + str(failedswap)) )
                    logger1.warning( ("Elapsed time: " + str(end-start)) )
                    storePickle(results, level, capacity, fileName)
                    return (soln, objFinal, objAllFinal, ciwidthFinal)
                elif response == 'break':
                    break
                print 'Resuming...'
            except KeyboardInterrupt:
                print 'Resuming...'
                continue

    objAllFinal, objFinal, ciwidthFinal, statE1, statF1, statC1 = simulate(level, capacity, sM, 100, daySeed+1, mbm, durations, simMethod, startTime, numIntervals)
    end = time.time()
    logger1.warning( ("Starting objective value: " + str(obj00) + ",  ciwidth: " + str(ciwidth00)) )
    logger1.warning( ("Final objective value: " + str(objFinal) + ", Final ciwidth: " + str(ciwidthFinal)) )
    logger1.warning( ("total capacity changes: " + str(totalCapsChange)) )
    logger1.warning( ("total bikes changes: " + str(totalBikesChange)) )
    logger1.warning( ("Total solutions evaluated by simulation = " + str(simCount/rep)) )
    logger1.warning( ("Last failed number of swaps = " + str(failedswap)) )
    logger1.warning( ("Elapsed time: " + str(end-start)) )
    storePickle(results, level, capacity, fileName)
    return end-start, objFinal, ciwidthFinal, obj00, ciwidth00

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
    randListSize = 30 # length of the list for randomized search. 1 is greedy.
    start = 6
    end = 10
    startTime = int(start*60) # simulation start time (minutes, from 0 to 1439)
    numIntervals = int(2*(end-start)) # number of 30-minute intervals to simulate
    # solutionFile = 'CTMCVaryRate' + str(start) + "-" + str(end) + '_15x'
    # solutionName = 'CTMCVaryRate' + str(start) + "to" + str(end) + '_15x'
    solutionFile = 'fluidModelUB_Dec15x'
    solutionName = 'FluidModel'
    simMethod = 'AltCond'
    fileInd = numpy.random.randint(1,99)
    fileName = (solutionName + "id" + str(fileInd))

    ''' Logging to File '''
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename='./outputsDO/%sid%iCaps.log' % (solutionName, fileInd),
                        filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    logging.info('gradSearchCaps.py')
    logging.info('Purpose of the run: fluid for 6-10AM, caps')
    logging.info(('random seed = ' + str(seed)))
    logging.info(('solution name = ' + fileName))

    # get state map info (caps, ords)
    sM = eval(open(('./data/'+solutionFile+'.txt')).read())
    # sM = cPickle.load(open('./data/%s.p' % solutionFile, 'r'))
    sM[-1000] = {'bikes':-1000, 'capacity':-1000, 'ords':(0,0), 'name':"null"}
    logging.info('Finished loading station map.')

    # get durations
    durationMult = eval(open('./data/durationsLNMultiplier2.txt').read())
    logging.info('Finished loading durations multiplier.')

    # get min-by-min data
    mbm = cPickle.load(open("./data/mbm30minDec_15x.p", 'r'))
    logging.info('Finished loading flow rates.')

    ''' Simulate and Optimize! '''
    config = [seed, randListSize, simMethod]
    time, objFinal, ciwidthFinal, obj00, ciwidth00 = randomSearch(sM,mbm,durationMult,fileName,
                                                            startTime,numIntervals,config)
    logging.warning( ("Random search id: " + str(fileInd) + ", solution: " + str(objFinal) +
                    ", ciwidth: " + str(ciwidthFinal) + ", elapsed time:" + str(time)) )

