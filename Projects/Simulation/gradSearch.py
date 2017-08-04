import SimulationRunner_v2 as SimulationRunner
import math, random
import numpy
import time
import cPickle
from collections import Counter
import logging

def simulate(level, sM, durations, rep, seed, mbm, simMethod, startTime, numIntervals):
    t0 = time.time()
    numpy.random.seed(seed) # starting seed for round of reps
    soln = 0
    s1 = []
    s2 = []
    solutionList = []
    solutionList2 = []
    for i in range(rep):
        data = SimulationRunner.testVehicles2(level, sM, mbm, durations, simMethod, startTime, numIntervals)
        solutionList.append(data)
        solutionList2.append(float(sum(data[0:3])))
        if data[3] != -1:
            s1.extend(data[3]) # all failed start sids in this rep
        if data[4] != -1:
            s2.extend(data[4]) # all failed end sids in this rep
    obj = round(numpy.mean(solutionList2, axis=0), 2)
    ciwidth = round(numpy.std(solutionList2)*1.96/numpy.sqrt(rep), 2)
    statE = Counter(s1).most_common() # produces a list with [0]=sid and [1]=failedStarts
    statF = Counter(s2).most_common() # produces a list with [0]=sid and [1]=failedEnds
    # print "Most common failed starts: ", statE
    # print "Most common failed ends: ", statF
    print "time in simulate() ", time.time() - t0, " with rep ", rep
    return (solutionList, obj, ciwidth, statE, statF)
    # return (obj, ciwidth)


def storePickle(results, level, fileName):
    ''' Store pickle '''
    fileName1 = ("./outputsDO/%s.p" % (fileName + 'Results'))
    fileName2 = ("./outputsDO/%s.p" % (fileName + 'Level'))
    cPickle.dump(results, open(fileName1, 'wb'))
    cPickle.dump(level, open(fileName2, 'wb'))

# Basic Solution: randomSearch start of code
def basicSoln(sM, mbm, daySeed, reps, simMethod = "AltCond", startTime = 420, numIntervals = 4):
    logger1 = logging.getLogger('gradSearch')

    sidList = []
    level = {}
    # Read solution
    for sid in sM:
        sidList.append(sid)
        level[sid] = sM[sid]['bikes']

    start = time.time()
    objAll, obj0, ciwidth, statE, statF = simulate(level, sM, reps, daySeed, mbm, simMethod, startTime, numIntervals)
    end = time.time()

    runTime = round(end - start,3)

    return runTime, obj0, ciwidth

def randomSearch(sM, mbm, durations, startTime, numIntervals, config):
    ''' Configurations '''
    nswap = 3 # initial number to swap in each iteration
    logger1 = logging.getLogger('gradSearch_v2')
    daySeed = config[0]
    listLength = config[1]
    simulationMethod = config[2]
    randomSwap = config[3]
    rep = config[4]
    logger1 = logging.getLogger('gradSearch_v2')
    start = time.time()

    simCount = 0 # count of total simulation days
    diff = -1

    sidList = []
    level = {}
    # Read solution
    for sid in sM:
        sidList.append(sid)
        level[sid] = sM[sid]['bikes']
    obj1 = 0.0

    objAll, obj0, ciwidth, statE, statF = simulate(level, sM, durations, 50, daySeed, mbm, simMethod, startTime, numIntervals)
    logger1.warning( ("Obj0: " + str(obj0) + " ciwidth " + str(ciwidth)) )
    obj00 = obj0
    ciwidth00 = ciwidth
    results = {}
    results[0] = objAll


    # proceed = 1
    seed = daySeed # random seed
    failedswap = 0
    failedSinceLastChange = 0
    improve = -999
    while True: # Stopping criteria
        try:
            ''' Decrease the number of swaps adaptively '''
            if failedSinceLastChange > 150 and nswap - 1 >= 1:
                nswap -= 1
                failedSinceLastChange = 0

            ''' Generate the sid lists to choose from '''
            # if randSwap == True:
            #     sidE = random.choice(sidList)
            #     sidF = random.choice(sidList)
            # else:
            sidEList = []
            sidFList = []
            showsidEList = []
            showsidFList = []
            n1 = 0
            n2 = 0
            com = 0 # select the most common empty/full station at first
            while n1<listLength and com<=len(statE)-1:
                sidE = statE[com][0]
                if sidE != -1 and level[sidE] + nswap <= float(sM[sidE]['capacity']):
                    sidEList.append(sidE)
                    showsidEList.append([sidE, statE[com][1]])
                    n1+=1
                com+=1

            com = 0
            while n2<listLength and com<=len(statF)-1:
                sidF = statF[com][0]
                if sidF != -1 and level[sidF] - nswap >= 0.0:
                    sidFList.append(sidF)
                    showsidFList.append([sidF, statF[com][1]])
                    n2+=1
                com+=1

            ''' Randomly choose two stations from the lists '''
            logger1.debug( ("sidEList: " + ', '.join(str(sid) for sid in showsidEList)) )
            logger1.debug( ("sidFList: " + ', '.join(str(sid) for sid in showsidFList)) )
            sidE = random.choice(sidEList)
            sidF = random.choice(sidFList)

            # sidEup = False
            # sidFup = False
            # sidEdn = False
            # sidFdn = False
            # while sidEup*sidFdn!=1 and sidEdn*sidFup!=1:
            #     sidEup = False
            #     sidFup = False
            #     sidEdn = False
            #     sidFdn = False
            #     # Determine which of the sidE, sidF can be increased or decreased
            #     if level[sidE] + nswap <= float(sM[sidE]['capacity']):
            #         sidEup = True
            #     if level[sidF] + nswap <= float(sM[sidF]['capacity']) and randomSwap==True: # if determined by data, has to decrease sid 2
            #         sidFup = True
            #     if level[sidE] - nswap >= 0.0 and randomSwap==True: # if determined by data, has to increase sid 1
            #         sidEdn = True
            #     if level[sidF] - nswap >= 0.0:
            #         sidFdn = True

            #     logger1.debug( ("sid" + str(sidE) + ", cap" + str(sM[sidE]['capacity']) + ", lvl " + str(level[sidE]) +
            #         "; sid" + str(sidF) + ", cap" + str(sM[sidF]['capacity']) + ", lvl " + str(level[sidF])) )
            #     logger1.debug( ("up,dn: sid" + str(sidE) + ", " + str(sidEup) + ", " + str(sidEdn) +
            #         "; sid" + str(sidF) +  ", " + str(sidFup) + ", " + str(sidFdn)) )

            #     # if randomSwap == False:
            #     if sidFdn==False or sidE==sidF: # the 0 is bounding
            #         com+=1
            #         logger1.debug( ("com " + str(com)) )
            #         logger1.debug( ("list F" + str(statF[com])) )
            #         if com <= len(statF[com])-1:
            #             sidF = statF[com][0]
            #             if sidF == -1:
            #                 sidF = random.choice(sidList)
            #         else: break
            #         logger1.debug( ("new sidF" + str(sidF)) )
            #     elif sidEup==False: # the capacity is bounding
            #         com+=1
            #         logger1.debug( ("com " + str(com)) )
            #         logger1.debug( ("list E" + str(statE[com])) )
            #         if com <= len(statE[com])-1:
            #             sidE = statE[com][0]
            #             if sidE == -1:
            #                 sidE = random.choice(sidList)
            #         else: break
            #         logger1.debug( ("new sidE" + str(sidE)) )
                # else:
                #     if (sidEup==True and sidFdn==False) or (sidEdn==True and sidFup==False):
                #         while sidE == sidF:
                #             sidF = random.choice(sidList)
                #         logger1.info( ("randomly selected sidF:" + str(sidF)) )
                #     elif (sidEup==False and sidFdn==True) or (sidEdn==False and sidFup==True):
                #         while sidE == sidF:
                #             sidE = random.choice(sidList)
                #         logger1.info( ("randomly selected sidE:" + str(sidE)) )


            logger1.info( ("Found up, dn: sid" + str(sidE) + ", lvl " + str(level[sidE]) +
                "; sid" + str(sidF) + ", lvl " + str(level[sidF])) )

            TrySoln = level.copy()
            # if sidEup*sidFdn==1: # or sidEdn*sidFup==1
            simCount += rep

            # try swapping
            TrySoln[sidE] += nswap
            TrySoln[sidF] -= nswap
            objAll1, obj1,ciwidth1,statE,statF = simulate(TrySoln, sM, durations, rep, daySeed, mbm, simMethod, startTime, numIntervals)
            diff = obj0 - obj1

            # if improved, do the swap, else, restore solution
            if diff>0.0:
                improve = diff
                level = TrySoln
                obj0 = obj1
                results[simCount] = objAll1
                logger1.warning( ("Improve: Obj1 = " + str(obj1) + " with ciwidth " + str(ciwidth1) +
                    " by " + str(diff) + " move " + str(nswap) +  " from " + str(sidF) + " to " + str(sidE)) )
                failedswap = 0 # suceed, reset number of attempts for this starting sol
                failedSinceLastChange = 0
            else:
                failedswap += 1
                failedSinceLastChange += 1
                logger1.info( ("Failed to move " + str(nswap) + " from " + str(sidF) + " to " + str(sidE) +
                    " failed number: " + str(failedswap)) )
            # elif sidEdn*sidFup==1:
            #     simCount += rep

            #     # try swapping
            #     TrySoln[sidF] += nswap
            #     TrySoln[sidE] -= nswap
            #     objAll1, obj1, ciwidth1, statE, statF = simulate(TrySoln, sM, durations, rep, daySeed, mbm, simMethod, startTime, numIntervals)

            #     # if improved, do the swap
            #     if diff>0.0:
            #         failedswap = 0
            #         improve = diff
            #         level = TrySoln
            #         obj0 = obj1
            #         results[simCount] = objAll1
            #         logger1.warning( ("Improve: Obj1 = " + str(obj1) + " with ciwidth " + str(ciwidth1) +
            #             " by " + str(diff) + " move " + str(nswap) +  " from " + str(sidF) + " to " + str(sidE)) )
            #         failedswap = 0 # succeed, reset number of attempts for this starting sol
            #     else:
            #         failedswap += 1
            #         logger1.info( ("Failed to move " + str(nswap) + " from " + str(sidF) + " to " + str(sidE) +
            #             " failed number: " + str(failedswap)) )

            logger1.warning( ("last improvement " + str(improve) + ", last obj" + str(obj0) + ", simCount" + str(simCount)) )
            
            if (simCount-50) % (rep*10) == 0: # store every 10 iterations
                storePickle(results, level, fileName)

        except KeyboardInterrupt:
            print '\nPausing...  (Hit ENTER to continue, type quit to stop optimization and record solutions, type break to exit immediately.)'
            try:
                response = raw_input()
                if response == 'quit':
                    break
                    objAllFinal, objFinal, ciwidthFinal, statE1, statF1 = simulate(level, sM, durations, 100, daySeed+1, mbm, simMethod, startTime, numIntervals)
                    end = time.time()
                    logger1.warning( ("Starting objective value: " + str(obj00) + ",  ciwidth: " + str(ciwidth00)) )
                    logger1.warning( ("Starting objective value: " + str(obj00) + ",  ciwidth: " + str(ciwidth00)) )
                    logger1.warning( ("Final objective value: " + str(objFinal) + ", Final ciwidth: " + str(ciwidthFinal)) )
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

    objAllFinal, objFinal, ciwidthFinal, statE1, statF1 = simulate(level, sM, durations, 100, daySeed+1, mbm, simMethod, startTime, numIntervals)
    end = time.time()
    logger1.warning( ("Starting objective value: " + str(obj00) + ",  ciwidth: " + str(ciwidth00)) )
    logger1.warning( ("Final objective value: " + str(objFinal) + ", Final ciwidth: " + str(ciwidthFinal)) )
    logger1.warning( ("Total solutions evaluated by simulation = " + str(simCount/rep)) )
    logger1.warning( ("Last failed number of swaps = " + str(failedswap)) )
    logger1.warning( ("Elapsed time: " + str(end-start)) )
    storePickle(results, level, fileName)
    return end-start, objFinal, ciwidthFinal, obj00, ciwidth00

if __name__ == '__main__':
    ''' Configurations '''
    seed = 8
    randListSize = 10 # length of the list for randomized search. 1 is greedy.
    reps = 30 # number of replications to evaluate each trial solution
    start = 6 # start hour
    end = 10 # end hour
    startTime = int(start*60) # simulation start time (minutes, from 0 to 1439)
    numIntervals = int(2*(end-start)) # number of 30-minute intervals to simulate
    # solutionName = 'CTMCVaryRateBikesOnly' + str(start) + "-" + str(end) + '_15x'
    solutionName = 'AverageAllocationFromNames'
    simMethod = 'AltCond'
    fileInd = numpy.random.randint(1,99)
    fileName = (solutionName + "id" + str(fileInd))

    ''' Logging to File '''
    # set up logging to file - see previous section for more details
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename='./outputsDO/'+solutionName+'id'+str(fileInd)+'.log',
                        filemode='w')
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

    logging.info('gradSearch_v2.py')
    logging.info('extension to average allocation id 73')
    logging.info(('random seed = ' + str(seed)))
    logging.info(('reps = ' + str(reps)))
    logging.info(('list size = ' + str(randListSize)))
    logging.info(('solution name = ' + fileName))

    # get state map info (caps, ords)
    sM = eval(open(('./data/'+solutionName+'.txt')).read())
    level = cPickle.load(open('./outputsDO/AverageAllocationFromNamesid73Level.p', 'r'))
    for s in sM.keys():
        sM[s]['bikes'] = level[s]
    logging.info('Finished loading station map.')

    # get min-by-min data
    start = time.time()
    mbm = cPickle.load(open("./data/mbm30minDec_15x.p", 'r'))
    end = time.time()
    load_time = end - start
    logging.info('Finished loading flow rates. Time elapsed: %d' % load_time)
    logging.debug( ('Check length of mbm = ' + str(len(mbm))) )

    # get durations
    durations = eval(open('./data/durationsLNMultiplier2.txt').read())
    logging.info('Finished loading durations.')

    randSwap = False


    # # Simulate (no optimization)

    # startTime = 420
    # numIntervals = 4
    # reps = 30

    # runtime, obj0, ciwidth = basicSoln(sM, mbm, seed, reps, "Original", startTime, numIntervals)
    # logging.warning( ("Simulation (Original): " + str(obj0) + ", ciwidth: " + str(ciwidth) + ", elapsed time:" + str(runtime)) )

    # runtime, obj0, ciwidth = basicSoln(sM, mbm, seed, reps, "Alt2", startTime, numIntervals)
    # logging.warning( ("Simulation (Alt2): " + str(obj0) + ", ciwidth: " + str(ciwidth) + ", elapsed time:" + str(runtime)) )

    # runtime, obj0, ciwidth = basicSoln(sM, mbm, seed, 30, "AltCond")
    # logging.warning( ("Simulation (AltCond): " + str(obj0) + ", ciwidth: " + str(ciwidth) + ", elapsed time:" + str(runtime)) )

    # runtime, obj0, ciwidth = basicSoln(sM, mbm, seed, 30, "AltAliasCond")
    # logging.warning( ("Simulation (AltAliasCond): " + str(obj0) + ", ciwidth: " + str(ciwidth) + ", elapsed time:" + str(runtime)) )

    # Simulate and Optimize!
    config = [seed, randListSize, simMethod, randSwap, reps]
    runtime, objFinal, ciwidthFinal, obj00, ciwidth00 =randomSearch(sM, mbm, durations, startTime, numIntervals, config)
    logging.warning( ("Random search id: " + str(fileInd) + ", solution: " + str(objFinal) + ", ciwidth: " + str(ciwidthFinal) + ", elapsed time:" + str(runtime)) )

