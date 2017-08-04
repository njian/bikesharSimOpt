import SimulationRunnerCapsDecomp as SimulationRunnerCaps
import math, random
import numpy
import time
import cPickle
from collections import Counter
from operator import itemgetter
import logging

def findIntersect(stat1List, stat2List):
    # names = eval(open('./data/CoordsAndNames.txt').read())
    sharedSid = list(set(stat1List).intersection(stat2List))
    # print "sharedSid", sharedSid
    # for sid in sharedSid:
    #     print sid, names[sid]['name'], dict(stat1)[sid], dict(stat2)[sid]
    return  sharedSid # shared components

def findExclusion(statList1, statList2):
    # find the stations in stat1 but not in stat2
    return list(set(statList1)-set(statList2))

def returnTopList(stat, listLength):
    return [stat[i][0] for i in range(len(stat))][0:listLength]

def returnTopStatCList(statC, capacity, listLength, nswap, minCap):
    com = 0
    nC = 0
    statCList = []
    while nC<listLength and com<=len(statC)-1:
        sidC = statC[com][0] # the com-th least outage station
        if capacity[sidC] - nswap >= minCap and sidC != 3230 and sidC != 3236: # not depots
            statCList.append(sidC)
            nC+=1
        com+=1
    return statCList

def takeAwayBikes(sidList, nswap, level):
    logger1 = logging.getLogger('gradSearchCapsDecomp')
    totalBikesTaken = 0
    failedSid = []
    for sid in sidList:
        if sid != -1:
            if level[sid] - nswap >= 0:
                level[sid] -= nswap
                totalBikesTaken += nswap
                logger1.debug( (str(nswap) + " bikes taken from " + str(sid)) )
            else: failedSid.append(sid)
    return level, totalBikesTaken, failedSid

def addBikes(sidList, nswap, level, capacity):
    logger1 = logging.getLogger('gradSearchCapsDecomp')
    totalBikesGiven = 0
    failedSid = []
    for sid in sidList:
        if sid != -1:
            if level[sid] + nswap <= capacity[sid]:
                level[sid] += nswap
                totalBikesGiven += nswap
                logger1.debug( (str(nswap) + " bikes given to " + str(sid)) )
            else: failedSid.append(sid)
    return level, totalBikesGiven, failedSid

def simulate(level, capacity, sM, rep, seed, mbm, durations, simMethod="AltCond", startTime=420, numIntervals=4):
    ''' Optimize bikes and docks, need statC '''
    numpy.random.seed(seed) # starting seed for round of reps
    soln = 0
    statE = []
    statEAM = []
    statEPM = []
    statF = []
    statFAM = []
    statFPM = []
    solutionList = {}
    solutionList2 = []

    for i in range(rep):
        data = SimulationRunnerCaps.testVehicles2(level, capacity, sM, mbm, durations, simMethod, startTime, numIntervals)
        solutionList[i] = data[0:5]
        solutionList2.append(float(sum(data[0:5])))
        statEAM.extend(data[5])
        statEPM.extend(data[6])
        statFAM.extend(data[7])
        statFPM.extend(data[8])

    obj = round(numpy.mean(solutionList2, axis=0), 2)
    ciwidth = round(numpy.std(solutionList2)*1.96/numpy.sqrt(rep), 2)
    statE_AM = Counter(statEAM).most_common() # produces a list with [0]=sid and [1]=failedStarts
    # print statE_AM
    statE_PM = Counter(statEPM).most_common()
    # print statE_PM
    statF_AM = Counter(statFAM).most_common() # produces a list with [0]=sid and [1]=failedEnds
    # print statF_AM
    statF_PM = Counter(statFPM).most_common()
    # print statF_PM
    counterC = Counter(statEAM+statFAM+statEPM+statFPM) # produces a list with [0]=sid and [1]=failedStarts+failedEnds
    statC = sorted(counterC.items(), key=itemgetter(1), reverse=False)
    return (solutionList, obj, ciwidth, statE_AM, statE_PM, statF_AM, statF_PM, statC)


def randomSearch(sM,mbm,durations,fileName,startTime,numIntervals,config):
    ''' Configurations '''
    nswap = 3 # initial number to swap in each iteration
    logger1 = logging.getLogger('gradSearchCapsDecomp')
    daySeed = config[0]
    listLength = config[1]
    simulationMethod = config[2]
    rep = config[3] # to evaluate each objective
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
    TrySolnLvl = level.copy()
    TrySolnCaps = capacity.copy()

    ''' Get initial solution '''
    objAll, obj0, ciwidth, statE_AM, statE_PM, statF_AM, statF_PM, statC = simulate(level, capacity, sM, 30, daySeed, mbm, durations, simMethod, startTime, numIntervals)
    logger1.warning( ("Obj0: " + str(obj0) + " ciwidth " + str(ciwidth)) )
    obj00 = obj0
    ciwidth00 = ciwidth
    results = {}
    results[0] = obj0 #objAll
    cumulativeCapsChange = 0
    cumulativeBikesChange = 0

    ''' Swapping Heuristics '''
    seed = daySeed
    failedswap = 0
    failedSinceLastChange = 0
    while True: # Stopping criteria
        try:
            time_startIter = time.time()

            ''' Decrease the number of swaps adaptively '''
            if failedSinceLastChange >= 50 and nswap - 1 >= 1:
                nswap -= 1
                failedSinceLastChange = 0

            # Select which stations to swap
            seed += 1
            random.seed(seed) # only used for selecting the sids

            ''' Debugging purpose '''
            statEAMDict = dict(statE_AM)
            statEAMDict[-1] = -1
            statEPMDict = dict(statE_PM)
            statEPMDict[-1] = -1
            statFAMDict = dict(statF_AM)
            statFAMDict[-1] = -1
            statFPMDict = dict(statF_PM)
            statFPMDict[-1] = -1
            statCDict = dict(statC)
            statCDict[-1] = -1

            ''' Find the top stations in each list '''
            statEAMList = returnTopList(statE_AM, listLength)
            statEPMList = returnTopList(statE_PM, listLength)
            statFAMList = returnTopList(statF_AM, listLength)
            statFPMList = returnTopList(statF_PM, listLength)
            statCList = returnTopStatCList(statC, capacity, 50, nswap, minCap)

            ''' 6 types of stations '''
            sidEA_list = findExclusion(statEAMList, statFPMList) # empty in AM but not full in PM
            sidEP_list = findExclusion(statEPMList, statFAMList) # empty in PM but not full in AM
            sidFA_list = findExclusion(statFAMList, statEPMList) # full in AM but not empty in PM
            sidFP_list = findExclusion(statFPMList, statEAMList) # full in PM but not empty in AM
            sidBI_list = findIntersect(statEAMList, statFPMList) # busy stations that are empty in AM and full in PM
            sidBD_list = findIntersect(statFAMList, statEPMList) # busy stations that are full in AM and empty in PM


            ''' Choose randomly from statE, statF, statC '''
            ''' Skips: in case the solution is very close to optimal so that statE, statF might be empty '''
            sidEA = random.choice(sidEA_list) if sidEA_list else -1
            sidEP = random.choice(sidEP_list) if sidEP_list else -1
            sidFA = random.choice(sidFA_list) if sidFA_list else -1
            sidFP = random.choice(sidFP_list) if sidFP_list else -1
            sidBI = random.choice(sidBI_list) if sidBI_list else -1
            sidBD = random.choice(sidBD_list) if sidBD_list else -1

            logger1.debug( ("sidEA %i: %i, sidEP %i: %i, sidFA %i: %i, sidFP %i: %i" % (sidEA, statEAMDict[sidEA], sidEP, statEPMDict[sidEP], sidFA, statFAMDict[sidFA], sidFP, statFPMDict[sidFP])) )
            logger1.debug( ("sidBI %i: %i, %i, sidBD %i: %i, %i" %  (sidBI, statEAMDict[sidBI], statFPMDict[sidBI], sidBD, statFAMDict[sidBD], statEPMDict[sidBD])) )

            ''' Generate the trial solution '''
            TrySolnLvl = level.copy()
            TrySolnCaps = capacity.copy()
            totalBikesTaken = 0
            totalBikesGiven = 0
            totalCapsChange = 0
            totalBikesChange = 0

            # Add dock to sidBI and sidBD
            sidC1 = random.choice(statCList)
            if sidBI != -1:
                if TrySolnCaps[sidBI] + nswap <= maxCap:
                    TrySolnCaps[sidBI] += nswap
                    TrySolnCaps[sidC1] -= nswap
                    statCList.remove(sidC1)
                    if TrySolnLvl[sidC1] > TrySolnCaps[sidC1]:
                        TrySolnLvl[sidC1] -= nswap
                        totalBikesTaken += nswap
                        logger1.debug( (str(nswap) + "bikes taken from sidC due to overflowing " + str(sidC1) + ',' + str(statCDict[sidC1])) )
                    totalCapsChange += nswap
                    logger1.debug( ("%i docks added to sidBI %i" % (nswap, sidBI)) )
                    logger1.debug( ("Docks taken from sidC " + str(sidC1) + ',' + str(statCDict[sidC1])) )
            sidC2 = random.choice(statCList)
            if sidBD != -1:
                if TrySolnCaps[sidBD] + nswap <= maxCap:
                    TrySolnCaps[sidBD] += nswap
                    TrySolnCaps[sidC2] -= nswap
                    statCList.remove(sidC2)
                    if TrySolnLvl[sidC2] > TrySolnCaps[sidC2]:
                        TrySolnLvl[sidC2] -= nswap
                        totalBikesTaken += nswap
                        logger1.debug( (str(nswap) + " bikes taken from sidC due to overflowing " + str(sidC2) + ',' + str(statCDict[sidC2])) )
                    totalCapsChange += nswap
                    logger1.debug( ("%i docks added to sidBD %i" % (nswap, sidBD)) )
                    logger1.debug( ("Docks taken from sidC " + str(sidC2) + ',' + str(statCDict[sidC2])) )


            # Try to take away a bike from each of sidFA, sidFP, sidBD
            TrySolnLvl, takenFrom3, failedTakeSid = takeAwayBikes([sidFA, sidFP, sidBD], nswap, TrySolnLvl)
            logger1 = logging.getLogger('gradSearchCapsDecomp')
            totalBikesTaken += takenFrom3
            listC3 = []
            while 3*nswap-totalBikesTaken > 0: # if taken < 3*nswap
                sidC3 = random.choice(statCList)
                ct = 0
                while TrySolnLvl[sidC3] - nswap < 0:
                    ct += 1
                    if ct >= 50:
                        statCList = returnTopStatCList(statC, capacity, 100, nswap, minCap)
                        print "in while 1! Running out of statCList. Tried %i loops" % ct
                    sidC3 = random.choice(statCList)
                TrySolnLvl[sidC3] -= nswap
                statCList.remove(sidC3)
                listC3.append(sidC3) # record the extra statC taken bikes
                totalBikesTaken += nswap
                logger1.debug( (str(nswap) + " bikes taken from sidC " + str(sidC3) + ',' + str(statCDict[sidC3])) )
            totalBikesChange += totalBikesTaken

            # Try to add a bike to each of sidEA, sidEP, sidBI
            TrySolnLvl, givenTo3, failedAddSid = addBikes([sidEA, sidEP, sidBI], nswap, TrySolnLvl, TrySolnCaps)
            totalBikesGiven += givenTo3

            logger1 = logging.getLogger('gradSearchCapsDecomp')
            # Add dock to stations that needs bike but are too full
            for sid in failedAddSid:
                if TrySolnCaps[sid] + nswap <= maxCap:
                    TrySolnCaps[sid] += nswap

                sidC4 = random.choice(statCList)
                ct = 0
                while TrySolnLvl[sidC4] - nswap < 0:
                    ct += 1
                    if ct >= 150:
                        statCList = returnTopStatCList(statC, capacity, len(statC), nswap, minCap)
                        print "in while 2! Running out of statCList. Tried %i loops" % ct
                    elif ct >= 50:
                        statCList = returnTopStatCList(statC, capacity, 100, nswap, minCap)
                        print "in while 2! Running out of statCList. Tried %i loops" % ct
                TrySolnCaps[sidC4] -= nswap
                statCList.remove(sidC4)
                totalCapsChange += nswap
            TrySolnLvl, givenToFailed, failedAddSid = addBikes(failedAddSid, nswap, TrySolnLvl, TrySolnCaps)
            totalBikesGiven += givenToFailed

            logger1 = logging.getLogger('gradSearchCapsDecomp')
            for sidC3 in listC3: # put excess bikes back to the previous sidC in listC3 first. If empty then will skip this
                if totalBikesTaken > totalBikesGiven + nswap: # taken more than given
                    TrySolnLvl[sidC3] += nswap
                    totalBikesGiven += nswap
                    logger1.debug( (str(nswap) + "bikes given to sidC " + str(sidC3) + ',' + str(statCDict[sidC3])) )
            while totalBikesTaken - totalBikesGiven > 0: # still has more bikes to allocate, then find more sidC to give bikes if necessary
                sidC3 = random.choice(statCList)
                ct = 0
                while TrySolnLvl[sidC3] + nswap > TrySolnCaps[sidC3]:
                    ct += 1
                    if ct >= 50:
                        statCList = returnTopStatCList(statC, capacity, 100, nswap, minCap)
                        print "in while 3! Running out of statCList. Tried %i loops" % ct
                    sidC3 = random.choice(statCList)
                TrySolnLvl[sidC3] += nswap
                totalBikesGiven += nswap
                logger1.debug( (str(nswap) + " bikes given to sidC " + str(sidC3) + ',' + str(statCDict[sidC3])) )

            # Check if equal
            logger1.debug( ("totalBikesGiven " + str(totalBikesGiven) + ", totalBikesTaken " + str(totalBikesTaken)) )

            ''' Simulate the trial solution '''
            simCount += rep
            objAll1, obj1, ciwidth1, statE_AM_Trial, statE_PM_Trial, statF_AM_Trial, statF_PM_Trial, statC_Trial = simulate(TrySolnLvl, TrySolnCaps, sM, rep, daySeed, mbm, durations, simMethod, startTime, numIntervals)
            diff = obj0 - obj1

            ''' Make the move if improving '''
            # if improved, do the swap, else, restore solution
            if diff>0.0:
                improve = diff
                level = TrySolnLvl.copy() # points to the trial soln
                capacity = TrySolnCaps.copy()
                obj0 = obj1
                results[simCount] = obj1 #objAll1
                logger1.warning( ("Improve: Obj1 = " + str(obj1) + " with ciwidth " + str(ciwidth1) +
                    " by " + str(diff)) )
                failedswap = 0 # suceed, reset number of attempts for this starting soln
                failedSinceLastChange = 0
                # del failedSwapPairs[-1]
                cumulativeCapsChange += totalCapsChange
                cumulativeBikesChange += totalBikesChange
                statE_AM = statE_AM_Trial
                statE_PM = statE_PM_Trial
                statF_AM = statF_AM_Trial
                statF_PM = statF_PM_Trial
                statC = statC_Trial
                logger1.warning( ("total capacity changes: " + str(cumulativeCapsChange)) )
                logger1.warning( ("total bikes changes: " + str(cumulativeBikesChange)) )
            else:
                failedswap += 1
                failedSinceLastChange += 1
                logger1.info( ("Failed trying the trial solution. Failed number: " + str(failedswap)) )

            logger1.warning("last improvement " + str(improve) + ", last obj" + str(obj0) + ", simCount" + str(simCount) +
                                      ", iteration time " + str(time.time() - time_startIter))

            if simCount % (rep*10) == 0: # store every 10 iterations
                storePickle(results, level, capacity, fileName)

        except KeyboardInterrupt:
            print '\nPausing...  (Hit ENTER to continue, type quit to stop optimization and record solutions, type break to exit immediately.)'
            try:
                response = raw_input()
                if response == 'quit':
                    break
                    objAllFinal, objFinal, ciwidthFinal, statE_AM1, statE_PM1, statF_AM1, statF_PM1, statC1 = simulate(level, capacity, sM, 100, daySeed+1, mbm, durations, simMethod, startTime, numIntervals)
                    end = time.time()
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

    objAllFinal, objFinal, ciwidthFinal, statE_AM1, statE_PM1, statF_AM1, statF_PM1, statC1 = simulate(level, capacity, sM, 100, daySeed+1, mbm, durations, simMethod, startTime, numIntervals)
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
    fileName1 = ("./outputsDO/%s.p" % (fileName + 'Results'))
    fileName2 = ("./outputsDO/%s.p" % (fileName + 'Level'))
    fileName3 = ("./outputsDO/%s.p" % (fileName + 'Capacity'))
    # fileName4 = ("./outputsDO/%s.p" % (fileName + 'FailedSwaps'))
    cPickle.dump(results, open(fileName1, 'wb'))
    cPickle.dump(level, open(fileName2, 'wb'))
    cPickle.dump(capacity, open(fileName3, 'wb'))
    # cPickle.dump(failedSwapPairs, open(fileName4, 'wb'))

if __name__ == '__main__':
    ''' Configurations '''
    seed = 9
    randListSize = 30 # length of the list for randomized search. 1 is greedy.
    reps = 30
    start = 6 # start hour
    end = 24 # end hour
    startTime = int(start*60) # simulation start time (minutes, from 0 to 1439)
    numIntervals = int(2*(end-start)) # number of 30-minute intervals to simulate
    solutionFile = 'CTMCVaryRate' + str(start) + "-" + str(end) + '_15x'
    solutionName = 'CTMCVaryRate' + str(start) + "to" + str(end) + '_15x'
    # solutionName = 'AverageAllocation'
    # solutionFile = 'AverageAllocationFromNamesConstrained'
    # solutionFile = 'fluidModelUB_Dec15x'
    # solutionName = 'FluidModel'
    simMethod = 'AltCond'
    fileInd = numpy.random.randint(1,99)
    fileName = (solutionName + "id" + str(fileInd) + "CapsDecomp")

    ''' Logging to File '''
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename='./outputsDO/%sid%iCapsDecomp.log' % (solutionName, fileInd),
                        filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    logging.info('gradSearchCapsDecomp.py')
    logging.info('Purpose of the run: decomposed gradSearchCaps starting from CTMC 6-24')
    logging.info(('random seed = ' + str(seed)))
    logging.info(('reps = ' + str(reps)))
    logging.info(('list size = ' + str(randListSize)))
    logging.info(('solution name = ' + fileName))

    ''' Get data '''
    # get state map info (caps, ords)
    sM = eval(open(('./data/'+solutionFile+'.txt')).read())
    # sM = cPickle.load(open('./data/%s.p' % solutionFile, 'r'))
    sM[-1000] = {'bikes':-1000, 'capacity':-1000, 'ords':(0,0), 'name':"null"}
    logging.info('Finished loading station map.')

    # get min-by-min data
    mbm = cPickle.load(open("./data/mbm30minDec_15x.p", 'r'))
    logging.info('Finished loading flow rates.')

    # get durations
    durations = eval(open('./data/durationsLNMultiplier2.txt').read())
    # durations = eval(open('./data/PairwiseCyclingDurations.txt').read())
    logging.info('Finished loading durations.')

    ''' Simulate and Optimize! '''
    config = [seed, randListSize, simMethod, reps]
    time, objFinal, ciwidthFinal, obj00, ciwidth00 = randomSearch(sM,mbm,durations,fileName,startTime,numIntervals,config)
    logging.warning( ("Random search id: " + str(fileInd) + ", solution: " + str(objFinal) + ", ciwidth: " + str(ciwidthFinal) + ", elapsed time:" + str(time)) )

    ''' Just simulate, not optimize '''
    # rep = 10
    # level = {} # level of bikes at each station at the beginning of the day
    # capacity = {} # capacity of each station
    # for sid in sM:
    #     level[sid] = sM[sid]['bikes']
    #     capacity[sid] = sM[sid]['capacity']
    # solutionList, obj, ciwidth, statE_AM, statE_PM, statF_AM, statF_PM, statC = simulate(level, capacity, sM, rep, seed, mbm, durations, simMethod="AltCond", startTime=360, numIntervals=36)


