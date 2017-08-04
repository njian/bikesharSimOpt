import SimulationRunnerDecomp as SimulationRunner
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

def takeAwayBikes(sidList, nswap, level):
    logger1 = logging.getLogger('gradSearchDecomp')
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
    logger1 = logging.getLogger('gradSearchDecomp')
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

def simulate(level, sM, rep, seed, mbm, durations, simMethod="AltCond", startTime=420, numIntervals=4):
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
        data = SimulationRunner.testVehicles2(level, sM, mbm, durations, simMethod, startTime, numIntervals)
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
    logger1 = logging.getLogger('gradSearchDecomp')
    daySeed = config[0]
    listLength = config[1]
    simulationMethod = config[2]
    rep = config[3] # to evaluate each objective
    # failedSwapPairs = []

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

    ''' Get initial solution '''
    objAll, obj0, ciwidth, statE_AM, statE_PM, statF_AM, statF_PM, statC = simulate(level, sM, 50, daySeed, mbm, durations, simMethod, startTime, numIntervals)
    logger1.warning( ("Obj0: " + str(obj0) + " ciwidth " + str(ciwidth)) )
    obj00 = obj0
    ciwidth00 = ciwidth
    results = {}
    results[0] = objAll
    cumulativeBikesChange = 0

    ''' Swapping Heuristics '''
    seed = daySeed
    failedswap = 0
    failedSinceLastChange = 0
    while True: # Stopping criteria
        try:
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
            statCList = returnTopList(statC, 50)

            ''' 6 types of stations '''
            notInLength = 200
            sidEA_list = findExclusion(statEAMList, returnTopList(statF_PM, notInLength)) # empty in AM but not full in PM
            sidEP_list = findExclusion(statEPMList, returnTopList(statF_AM, notInLength)) # empty in PM but not full in AM
            sidFA_list = findExclusion(statFAMList, returnTopList(statE_PM, notInLength)) # full in AM but not empty in PM
            sidFP_list = findExclusion(statFPMList, returnTopList(statE_AM, notInLength)) # full in PM but not empty in AM
            sidBI_list = findIntersect(returnTopList(statE_AM, 50), returnTopList(statF_PM, 50)) # busy stations that are empty in AM and full in PM
            sidBD_list = findIntersect(returnTopList(statF_AM, 50), returnTopList(statE_PM, 50)) # busy stations that are full in AM and empty in PM


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
            totalBikesTaken = 0
            totalBikesGiven = 0
            totalBikesChange = 0

            # Try to take away a bike from each of sidFA, sidFP, sidBD
            TrySolnLvl, takenFrom3, failedTakeSid = takeAwayBikes([sidFA, sidFP, sidBD], nswap, TrySolnLvl)
            logger1 = logging.getLogger('gradSearchDecomp')
            totalBikesTaken += takenFrom3
            listC3 = []
            while 3*nswap-totalBikesTaken > 0: # if taken < 3*nswap
                sidC3 = random.choice(statCList)
                while TrySolnLvl[sidC3] - nswap < 0:
                    sidC3 = random.choice(statCList)
                TrySolnLvl[sidC3] -= nswap
                statCList.remove(sidC3)
                listC3.append(sidC3) # record the extra statC taken bikes
                totalBikesTaken += nswap
                logger1.debug( (str(nswap) + " bikes taken from sidC " + str(sidC3) + ',' + str(statCDict[sidC3])) )
            totalBikesChange += totalBikesTaken

            # Try to add a bike to each of sidEA, sidEP, sidBI
            TrySolnLvl, givenTo3, failedAddSid = addBikes([sidEA, sidEP, sidBI], nswap, TrySolnLvl, capacity)
            totalBikesGiven += givenTo3

            logger1 = logging.getLogger('gradSearchDecomp')
            for sidC3 in listC3: # put excess bikes back to the previous sidC in listC3 first. If empty then will skip this
                if totalBikesTaken > totalBikesGiven + nswap: # taken more than given
                    TrySolnLvl[sidC3] += nswap
                    totalBikesGiven += nswap
                    logger1.debug( (str(nswap) + "bikes given to sidC " + str(sidC3) + ',' + str(statCDict[sidC3])) )
            while totalBikesTaken - totalBikesGiven > 0: # still has more bikes to allocate, then find more sidC to give bikes if necessary
                sidC3 = random.choice(statCList)
                while TrySolnLvl[sidC3] + nswap > capacity[sidC3]:
                    sidC3 = random.choice(statCList)
                TrySolnLvl[sidC3] += nswap
                totalBikesGiven += nswap
                logger1.debug( (str(nswap) + " bikes given to sidC " + str(sidC3) + ',' + str(statCDict[sidC3])) )

            # Check if equal
            logger1.debug( ("totalBikesGiven " + str(totalBikesGiven) + ", totalBikesTaken " + str(totalBikesTaken)) )

            ''' Simulate the trial solution '''
            simCount += rep
            objAll1, obj1, ciwidth1, statE_AM_Trial, statE_PM_Trial, statF_AM_Trial, statF_PM_Trial, statC_Trial = simulate(TrySolnLvl, sM, rep, daySeed, mbm, durations, simMethod, startTime, numIntervals)
            diff = obj0 - obj1

            ''' Make the move if improving '''
            # if improved, do the swap, else, restore solution
            if diff>0.0:
                improve = diff
                level = TrySolnLvl.copy() # points to the trial soln
                obj0 = obj1
                results[simCount] = objAll1
                logger1.warning( ("Improve: Obj1 = " + str(obj1) + " with ciwidth " + str(ciwidth1) +
                    " by " + str(diff)) )
                failedswap = 0 # suceed, reset number of attempts for this starting soln
                failedSinceLastChange = 0
                # del failedSwapPairs[-1]
                cumulativeBikesChange += totalBikesChange
                statE_AM = statE_AM_Trial
                statE_PM = statE_PM_Trial
                statF_AM = statF_AM_Trial
                statF_PM = statF_PM_Trial
                statC = statC_Trial
                logger1.warning( ("total bikes changes: " + str(cumulativeBikesChange)) )
            else:
                failedswap += 1
                failedSinceLastChange += 1
                logger1.info( ("Failed trying the trial solution. Failed number: " + str(failedswap)) )
            logger1.warning( ("last improvement " + str(improve) + ", last obj" + str(obj0) + ", simCount" + str(simCount)) )

            if simCount % (rep*10) == 0: # store every 10 iterations
                storePickle(results, level, fileName)

        except KeyboardInterrupt:
            print '\nPausing...  (Hit ENTER to continue, type quit to stop optimization and record solutions, type break to exit immediately.)'
            try:
                response = raw_input()
                if response == 'quit':
                    break
                    objAllFinal, objFinal, ciwidthFinal, statE_AM1, statE_PM1, statF_AM1, statF_PM1, statC1 = simulate(level, sM, 100, daySeed+1, mbm, durations, simMethod, startTime, numIntervals)
                    end = time.time()
                    logger1.warning( ("Starting objective value: " + str(obj00) + ",  ciwidth: " + str(ciwidth00)) )
                    logger1.warning( ("Final objective value: " + str(objFinal) + ", Final ciwidth: " + str(ciwidthFinal)) )
                    logger1.warning( ("total bikes changes: " + str(totalBikesChange)) )
                    logger1.warning( ("Total solutions evaluated by simulation = " + str(simCount/rep)) )
                    logger1.warning( ("Last failed number of swaps = " + str(failedswap)) )
                    logger1.warning( ("Elapsed time: " + str(end-start)) )
                    storePickle(results, level, fileName)
                    return (soln, objFinal, objAllFinal, ciwidthFinal)
                elif response == 'break':
                    break
                print 'Resuming...'
            except KeyboardInterrupt:
                print 'Resuming...'
                continue

    objAllFinal, objFinal, ciwidthFinal, statE_AM1, statE_PM1, statF_AM1, statF_PM1, statC1 = simulate(level, sM, 100, daySeed+1, mbm, durations, simMethod, startTime, numIntervals)
    end = time.time()
    logger1.warning( ("Starting objective value: " + str(obj00) + ",  ciwidth: " + str(ciwidth00)) )
    logger1.warning( ("Final objective value: " + str(objFinal) + ", Final ciwidth: " + str(ciwidthFinal)) )
    logger1.warning( ("total bikes changes: " + str(totalBikesChange)) )
    logger1.warning( ("Total solutions evaluated by simulation = " + str(simCount/rep)) )
    logger1.warning( ("Last failed number of swaps = " + str(failedswap)) )
    logger1.warning( ("Elapsed time: " + str(end-start)) )
    storePickle(results, level, fileName)
    return end-start, objFinal, ciwidthFinal, obj00, ciwidth00

def storePickle(results, level, fileName):
    fileName1 = ("./outputsDO/%s.p" % (fileName + 'Results'))
    fileName2 = ("./outputsDO/%s.p" % (fileName + 'Level'))
    # fileName4 = ("./outputsDO/%s.p" % (fileName + 'FailedSwaps'))
    cPickle.dump(results, open(fileName1, 'wb'))
    cPickle.dump(level, open(fileName2, 'wb'))
    # cPickle.dump(failedSwapPairs, open(fileName4, 'wb'))

if __name__ == '__main__':
    ''' Configurations '''
    seed = 2
    randListSize = 30 # length of the list for randomized search. 1 is greedy.
    reps = 30
    start = 6 # start hour
    end = 24 # end hour
    startTime = int(start*60) # simulation start time (minutes, from 0 to 1439)
    numIntervals = int(2*(end-start)) # number of 30-minute intervals to simulate
    solutionName = 'CTMCVaryRateBikesOnly' + str(start) + "-" + str(end) + '_15x' #AverageAllocationFromNames
    # solutionName = "AverageAllocationFromNames"
    # CTMCVaryRate6-24_15x
    simMethod = 'AltCond'
    fileInd = numpy.random.randint(1,99)
    fileName = (solutionName + "id" + str(fileInd) + "Decomp")

    ''' Logging to File '''
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename='./outputsDO/%sid%iDecomp.log' % (solutionName, fileInd),
                        filemode='w')
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    logging.info('gradSearchDecomp.py')
    logging.info('Purpose of the run: extension of AverageAllocationFromNamesid9Decomp')
    # logging.info('Extension to AverageAllocationFromNamesid19Decomp') # comments
    # logging.info('extension to CTMCVaryRateBikesOnly6-24_15xid70Decomp') # comments
    logging.info(('random seed = ' + str(seed)))
    logging.info(('reps = ' + str(reps)))
    logging.info(('list size = ' + str(randListSize)))
    logging.info(('solution name = ' + fileName))

    ''' Get data '''
    # get state map info (caps, ords)
    sM = eval(open(('./data/'+solutionName+'.txt')).read())
    sM[-1000] = {'bikes':-1000, 'capacity':-1000, 'ords':(0,0), 'name':"null"}
    # level = cPickle.load(open('./outputsDO/AverageAllocationFromNamesid9DecompLevel.p', 'r'))
    # for s in sM.keys():
    #     sM[s]['bikes'] = level[s]
    logging.info('Finished loading station map.')

    # get min-by-min data
    mbm = cPickle.load(open("./data/mbm30minDec_15x.p", 'r'))
    logging.info('Finished loading flow rates.')

    # get durations
    durations = eval(open('./data/durationsLNMultiplier2.txt').read())
    logging.info('Finished loading durations.')

    ''' Simulate and Optimize! '''
    config = [seed, randListSize, simMethod, reps]
    time, objFinal, ciwidthFinal, obj00, ciwidth00 = randomSearch(sM,mbm,durations,fileName,startTime,numIntervals,config)
    logging.warning( ("Random search id: " + str(fileInd) + ", solution: " + str(objFinal) + ", ciwidth: " + str(ciwidthFinal) + ", elapsed time:" + str(time)) )

    # rep = 10
    # level = {} # level of bikes at each station at the beginning of the day
    # capacity = {} # capacity of each station
    # for sid in sM:
    #     level[sid] = sM[sid]['bikes']
    #     capacity[sid] = sM[sid]['capacity']
    # solutionList, obj, ciwidth, statE_AM, statE_PM, statF_AM, statF_PM, statC = \
    #     simulate(level, sM, rep, seed, mbm, durations, "AltCond", 360, 36)
    # ''' Find the top stations in each list '''
    # listLength = 10
    # statEAMList = returnTopList(statE_AM, listLength)
    # statEPMList = returnTopList(statE_PM, listLength)
    # statFAMList = returnTopList(statF_AM, listLength)
    # statFPMList = returnTopList(statF_PM, listLength)
    # statCList = returnTopList(statC, 50)

    # ''' 6 types of stations '''
    # sidEA_list = findExclusion(statEAMList, statFPMList) # empty in AM but not full in PM
    # sidEP_list = findExclusion(statEPMList, statFAMList) # empty in PM but not full in AM
    # sidFA_list = findExclusion(statFAMList, statEPMList) # full in AM but not empty in PM
    # sidFP_list = findExclusion(statFPMList, statEAMList) # full in PM but not empty in AM
    # sidBI_list = findIntersect(statEAMList, statFPMList) # busy stations that are empty in AM and full in PM
    # sidBD_list = findIntersect(statFAMList, statEPMList) # busy stations that are full in AM and empty in PM
    # for i in range(5):
    #     print sidEA_list[i], sidEP_list[i], sidFA_list[i], sidFP_list[i], sidBI_list[i], sidBD_list[i], statC[i]

