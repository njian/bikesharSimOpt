'''

eomahony



'''

# import MyLevelParsers
import BikeSimCapsTable as BikeSim
# import BikeSimDBBackend
# import Config
import numpy

def runDay(mbm, statMapGen, durations, simMethod, startTime, numIntervals,
            sctPlt = None, nsamples=1, tgenMult=1, sctPltTimes = None, vehicles=[]):
    sM = statMapGen
    gc = BikeSim.GlobalClock(startTime, sM, BikeSim.TripGenerator(sM, mbm, durations, tgenMult),
                             verbosity=2, vehicles=vehicles)

    for i in range(30*numIntervals):#60*18
        if simMethod == "Original":
            minTrips = gc.tripGen.generateTrips(gc.time)
            gc.tick_original(minTrips)

        if simMethod == "Alt2":
        # Note: assumes that interval starts at the beginning of a 30 minute period
            if i%30 == 0:
                allTrips = gc.tripGen.getAllTripsCombined(gc.time)
                    # dictionary with keys = minutes in interval
                for i in range(30):
                    minTrips=allTrips[gc.time]
                    gc.tick_original(minTrips)

        if simMethod == "AltCond":
            if i%30 == 0:
                allTrips = gc.tripGen.getAllTripsCombinedCond(gc.time)
                    # dictionary with keys = minutes in interval
                for i in range(30):
                    minTrips=allTrips[gc.time]
                    gc.tick_original(minTrips)

    # if sctPlt is not None:
    #     gc.getScatterPlotData(sctPlt, nsamples)
    # if sctPltTimes is not None:
    #     gc.getScatterPlotDataTimes(sctPltTimes, nsamples)

    # if vehicles is not []:
    #     for v in vehicles:
    #         print v.totalPicked, v.totalDropped

    arrowDict = {}
    for sid in sM.keys():
        arrowDict[sid] = sM[sid].getArrowList()

    return (gc.getFailedEnds(),
            gc.getFailedStarts(),
            gc.getAlterEnd(),
            arrowDict)
            # gc.getFailedStartsStationCount())


def runDays(mbm, statMapGen, iters=10, tMult=1, vehicles=lambda: []):
    tOk = []
    fEnd = []
    aEnd = []
    oMins = []
    tTrips = []
    eMins = []
    fMins = []
    cTrips = []
    fStarts = []

    for i in range(iters):
        t,f,a,o, tt, em, fm, ct, fs, fss, fes = runDay(mbm, statMapGen, tgenMult=tMult,
                                             vehicles=vehicles())
        tOk.append(t)
        fEnd.append(f)
        aEnd.append(a)
        oMins.append(o)
        tTrips.append(tt)
        eMins.append(em)
        fMins.append(fm)
        cTrips.append(ct)
        fStarts.append(fs)

    return [sum(tOk)/float(iters), sum(fEnd)/float(iters),
            sum(aEnd)/float(iters), sum(oMins)/float(iters),
            sum(tTrips)/float(iters), sum(eMins)/float(iters),
            sum(fMins)/float(iters), sum(cTrips)/float(iters),
            sum(fStarts)/float(iters)]

def statMap50Gen():
    sM = BikeSim.getStatMap()
    # Put in an allocation
    total = 0

    for sid, stat in sM.items():
        stat.level = int(round(stat.cap*0.5))
        total += stat.level
    print "Total bikes", total
    return sM

def statMap50GenDepots():
    sM = BikeSim.getStatMap()
    # Put in an allocation
    total = 0

    for sid, stat in sM.items():
        stat.level = int(round(stat.cap*0.5))
        total += stat.level

    # Add depots
    sM[0] = BikeSim.Station(0, "depot 0", 400, 200, 0, (0,0))
    sM[1] = BikeSim.Station(1, "depot 1", 400, 200, 0, (0,0))

    print "Total bikes", total
    return sM

def statMapCTMCDepots():
    sM = statMapMorningGenCTMC()
    # Add depots
    sM[0] = BikeSim.Station(0, "depot 0", 400, 200, 0, (0,0))
    sM[1] = BikeSim.Station(1, "depot 1", 400, 200, 0, (0,0))

    return sM

def statMapEqual4kGen():
    sM = BikeSim.getStatMap()
    # Put in an allocation
    total = 0

    for sid, stat in sM.items():
        stat.level = int(round(stat.cap*0.365))
        total += stat.level
    print "Total bikes", total
    return sM

def statMapMinMaxCost():
    sM = BikeSim.getStatMap()
    # Put in an allocation
    import Config
    total = 0
    for sid, stat in sM.items():
        if Config.MinMaxMorning.has_key(sid):
            stat.level = int(round(Config.MinMaxMorning[sid]))
        else:
            stat.level = stat.cap/2
        total += stat.level
    print "Total bikes cluster:", total
    return sM

def statMapMinCostSum():
    sM = BikeSim.getStatMap()
    # Put in an allocation
    import Config
    total = 0
    for sid, stat in sM.items():
        if Config.minCostSumMorning.has_key(sid):
            stat.level = int(round(Config.minCostSumMorning[sid]))
        else:
            stat.level = stat.cap/2
        total += stat.level
    print "Total bikes cluster:", total
    return sM

def statMapMinCostSquared():
    sM = BikeSim.getStatMap()
    # Put in an allocation
    import Config
    total = 0
    for sid, stat in sM.items():
        if Config.minCostSquaredMorning.has_key(sid):
            stat.level = int(round(Config.minCostSquaredMorning[sid]))
        else:
            stat.level = stat.cap/2
        total += stat.level
    print "Total bikes cluster:", total
    return sM

def statMapMorningGen():
    sM = BikeSim.getStatMap()
    # Put in an allocation
    import Config
    total = 0
    for sid, stat in sM.items():
        if Config.morning.has_key(sid):
            stat.level = int(stat.cap*Config.morning[sid])
        else:
            stat.level = stat.cap/2
        total += stat.level
    print "Total bikes cluster:", total
    return sM

def statMapMorningGenCTMC():
    sM = BikeSim.getStatMap()
    # Put in an allocation
    import Config
    total = 0
    for sid, stat in sM.items():
        if Config.CTMCMorning4K.has_key(sid):
            stat.level = int(round(Config.CTMCMorning4K[sid]))
        else:
            del sM[sid]
            # print "deleted station", sid
            # stat.level = stat.cap/2
        total += stat.level
    # print "Total bikes CTMC:", total
    return sM

def statMapTestSol(level, capacity, sM):
    # Put in a starting allocation
    stations = {}
    for sid in level.keys():
        stations[sid] = BikeSim.Station(sid, sM[sid]['name'], capacity[sid], level[sid],
            0, sM[sid]['ords'])
    return stations

def makeScatterPlots(actualRes, simRes, month):
    import matplotlib.pyplot as plt

    x = []
    y = []
    for oID in actualRes.keys():
        for dID in actualRes[oID].keys():
            x.append(actualRes[oID][dID])
            if simRes.has_key(oID) and simRes[oID].has_key(dID):
                y.append(simRes[oID][dID] )
            else: y.append(0)

    #print x, y

    plt.clf()
    plt.scatter(x,y)
    plt.xlim(0,60)
    plt.ylim(0,60)
    plt.plot(range(60), range(60), color='g')
    plt.title("Scatter plot of average data from %s versus Simulation" % month)
    plt.xlabel("Real (ij) trip numbers")
    plt.ylabel("Simulated (ij) trip numbers")
    plt.savefig("./scatterPlots/%sVersusSimulation.png" % month)

def makeScatterPlotsTime(actualRes, simRes, month):
    import matplotlib.pyplot as plt

    x = []
    y = []

    xprime = []
    yprime = []

    for t1 in actualRes.keys():
        x.append(actualRes[t1][0])
        if simRes.has_key(t1):
            y.append(simRes[t1][0] )
        else: y.append(0)

        xprime.append(actualRes[t1][1])
        if simRes.has_key(t1):
            yprime.append(simRes[t1][1] )
        else: yprime.append(0)

    plt.clf()
    plt.scatter(x,y)
    plt.scatter(xprime, yprime, color='r')
    plt.plot(range(1000), range(1000), color='g')

    plt.xlim(0,1000)
    plt.ylim(0,1000)
    plt.title("Scatter plot of average data from %s versus Simulation" % month)
    plt.xlabel("Real trip numbers per 10 min time window")
    plt.ylabel("Simulated trip numbers per 10 min time window")
    plt.savefig("./scatterPlots/%sVersusSimulationTime.png" % month)


def makeStatToStatScatterPlots():
    mbm = BikeSimDBBackend.getMinByMin()

    iters = 10
    simPlt = {}
    for i in range(iters):
        runDay(mbm, statMap50Gen, simPlt, iters)

    actPltJul = BikeSimDBBackend.loadScatterPlotPickle("Jul")
    makeScatterPlots(actPltJul, simPlt, "July")

    actPltAug = BikeSimDBBackend.loadScatterPlotPickle("Aug")
    makeScatterPlots(actPltAug, simPlt, "August")

    actPltSept = BikeSimDBBackend.loadScatterPlotPickle("Sept")
    makeScatterPlots(actPltSept, simPlt, "September")

    actPltOct = BikeSimDBBackend.loadScatterPlotPickle("Oct")
    makeScatterPlots(actPltOct, simPlt, "October")

def makeTripsPerHourScatterPlots():
    mbm = BikeSimDBBackend.getMinByMin()
    iters = 10
    simPlt = {}
    for i in range(iters):
        runDay(mbm, statMap50Gen, nsamples= iters, sctPltTimes = simPlt)

    actPltJul = BikeSimDBBackend.loadScatterPlotPickleTime("Jul")
    makeScatterPlotsTime(actPltJul, simPlt, "July")

    actPltAug = BikeSimDBBackend.loadScatterPlotPickleTime("Aug")
    makeScatterPlotsTime(actPltAug, simPlt, "August")

    actPltSept = BikeSimDBBackend.loadScatterPlotPickleTime("Sept")
    makeScatterPlotsTime(actPltSept, simPlt, "September")

    actPltOct = BikeSimDBBackend.loadScatterPlotPickleTime("Oct")
    makeScatterPlotsTime(actPltOct, simPlt, "October")

def makeRadarPlotCluster50Comp(mbm, mult):
    resA = runDays(mbm, statMap50Gen, tMult=mult)
    resB = runDays(mbm, statMapMorningGen, tMult=mult)
    data = [ resA, resB ]
    columns = ["Successful Trips", "Failed Ends", "Different Ends",
               "Outage Minutes", "Total Trips", "Empty Mins", "Full Mins",
               "Completed Trips", "Failed Starts"]
    labels = ["50 Fill Leve", "Clustered Morning",]
    title = "Clustered Fill Levels Vs. 50pct levels (demand at x%f)" % mult

    import RadarSimPlot
    RadarSimPlot.radarPlotSimulationVeresions(data, columns,
                title, labels, "./radarPlots/clustVs50_%fdem.png"%mult)
    z
def makeRadarPlotCluster50CTMCComp(mbm, mult):
    resA = runDays(mbm, statMap50Gen, tMult=mult)
    resB = runDays(mbm, statMapMorningGenCTMC, tMult=mult)
    data = [ resA, resB ]
    columns = ["Successful Trips", "Failed Ends", "Different Ends",
               "Outage Minutes", "Total Trips", "Empty Mins", "Full Mins",
               "Completed Trips", "Failed Starts"]
    labels = ["50 Fill Level", "CTMC Morning",]
    title = "CTMC Fill Levels Vs. 50pct levels (demand at x%f)" % mult

    import RadarSimPlot
    RadarSimPlot.radarPlotSimulationVeresions(data, columns,
                title, labels, "./radarPlots/ctmcVs50_%fdem.png"%mult)

def makeRadarPlotEqual40CTMCComp(mbm, mult):
    resA = runDays(mbm, statMapEqual4kGen, tMult=mult)
    resB = runDays(mbm, statMapMorningGenCTMC, tMult=mult)
    data = [ resA, resB ]
    columns = ["Successful Trips", "Failed Ends", "Different Ends",
               "Outage Minutes", "Total Trips", "Empty Mins", "Full Mins",
               "Completed Trips", "Failed Starts"]
    labels = ["4K Equal Fill Level", "CTMC Morning",]
    title = "CTMC Fill Levels Vs. Equal levels (4k bikes) (demand at x%f)" % mult

    import RadarSimPlot
    RadarSimPlot.radarPlotSimulationVeresions(data, columns,
                title, labels, "./radarPlots/ctmcVs4k_%fdem.png"%mult)

def makeRadarPlot50VsMCSq(mbm, mult):
    resA = runDays(mbm, statMap50Gen, tMult=mult)
    resB = runDays(mbm, statMapMinCostSquared, tMult=mult)
    data = [ resA, resB ]
    columns = ["Successful Trips", "Failed Ends", "Different Ends",
               "Outage Minutes", "Total Trips", "Empty Mins", "Full Mins",
               "Completed Trips", "Failed Starts"]
    labels = ["50 Fill Level", "Min Cost Squared",]
    title = "50 Fill Level Vs. Min Cost Squared  (demand at x%f)" % mult

    import RadarSimPlot
    RadarSimPlot.radarPlotSimulationVeresions(data, columns,
                title, labels, "./radarPlots/50fillVsMCSq_%fdem.png"%mult)

def makeRadarPlot50VsMCSum(mbm, mult):
    resA = runDays(mbm, statMap50Gen, tMult=mult)
    resB = runDays(mbm, statMapMinCostSum, tMult=mult)
    data = [ resA, resB ]
    columns = ["Successful Trips", "Failed Ends", "Different Ends",
               "Outage Minutes", "Total Trips", "Empty Mins", "Full Mins",
               "Completed Trips", "Failed Starts"]
    labels = ["50 Fill Level", "Min Cost Sum",]
    title = "50 Fill Level Vs. Min Cost Sum  (demand at x%f)" % mult

    import RadarSimPlot
    RadarSimPlot.radarPlotSimulationVeresions(data, columns,
                title, labels, "./radarPlots/50fillVsMCSum_%fdem.png"%mult)

def makeRadarPlot50VsMinMaxC(mbm, mult):
    resA = runDays(mbm, statMap50Gen, tMult=mult)
    resB = runDays(mbm, statMapMinMaxCost, tMult=mult)
    data = [ resA, resB ]
    columns = ["Successful Trips", "Failed Ends", "Different Ends",
               "Outage Minutes", "Total Trips", "Empty Mins", "Full Mins",
               "Completed Trips", "Failed Starts"]
    labels = ["50 Fill Level", "Min Max Cost",]
    title = "50 Fill Level Vs. Min Max Cost (demand at x%f)" % mult

    import RadarSimPlot
    RadarSimPlot.radarPlotSimulationVeresions(data, columns,
                title, labels, "./radarPlots/50fillVsMMaxC_%fdem.png"%mult)

def getMorningTrailerRoutes():
    res = []
    for s,e in Config.morningPairs:
        res.append( BikeSim.BikeTrailerRouter( (s, e), 12, 6*60, 11*60 ) )
    return res


def getEveningTrailerRoutes():
    res = []
    for s,e in Config.eveningPairs:
        res.append( BikeSim.BikeTrailerRouter( (s, e), 12, 13*60, 20*60 ) )
    return res

def getVehicles():
    # Generate the vehicles
    vehicles = []
    for btr in getMorningTrailerRoutes():
        vehicles.append( BikeSim.Trailer(btr) )
    for btr in getEveningTrailerRoutes():
        vehicles.append( BikeSim.Trailer(btr) )
    return vehicles


def testVehicles(mbm, mult):
    resA = runDays(mbm, statMapMorningGenCTMC, tMult=mult, iters=10)
    resB = runDays(mbm, statMapCTMCDepots, tMult=mult, iters=10, vehicles = getVehicles)
    data = [ resA, resB ]
    columns = ["Successful Trips", "Failed Ends", "Different Ends",
               "Outage Minutes", "Total Trips", "Empty Mins", "Full Mins",
               "Completed Trips", "Failed Starts"]
    labels = ["Normal", "Trailers",]
    title = "Normal Vs Trailers (demand at x%f)" % mult
    import RadarSimPlot
    RadarSimPlot.radarPlotSimulationVeresions(data, columns,
                title, labels, "./radarPlots/50fillVsTrailers_%fdem.png"%mult)

# Modified testVehicles, only run 1 day morning rush hour
def testVehicles2(level, capacity, sM, mbm, durations, simMethod, startTime, numIntervals):
    data = runDay(mbm, statMapTestSol(level, capacity, sM), durations, simMethod,
        startTime, numIntervals, sctPlt = None, nsamples=1,  tgenMult=1, sctPltTimes = None,
        vehicles=[])
    return data

if __name__ == '__main__':

    #makeTripsPerHourScatterPlots()
    #makeStatToStatScatterPlots()

    # mbm = BikeSimDBBackend.getMinByMin()
    # testVehicles(mbm, 1)
    # testVehicles(mbm, 1.25)
    # testVehicles(mbm, 1.5)
    # testVehicles(mbm, 1.75)
    # testVehicles(mbm, 2)

    '''
    mbm = BikeSimDBBackend.getMinByMin()
    makeRadarPlotCluster50CTMCComp(mbm, 1)
    makeRadarPlotCluster50CTMCComp(mbm, 1.25)
    makeRadarPlotCluster50CTMCComp(mbm, 1.5)
    makeRadarPlotCluster50CTMCComp(mbm, 1.75)
    makeRadarPlotCluster50CTMCComp(mbm, 2)

    makeRadarPlot50VsMCSq(mbm, 1)
    makeRadarPlot50VsMCSq(mbm, 1.25)
    makeRadarPlot50VsMCSq(mbm, 1.5)
    makeRadarPlot50VsMCSq(mbm, 1.75)
    makeRadarPlot50VsMCSq(mbm, 2)

    makeRadarPlot50VsMCSum(mbm, 1)
    makeRadarPlot50VsMCSum(mbm, 1.25)
    makeRadarPlot50VsMCSum(mbm, 1.5)
    makeRadarPlot50VsMCSum(mbm, 1.75)
    makeRadarPlot50VsMCSum(mbm, 2)

    makeRadarPlot50VsMinMaxC(mbm, 1)
    makeRadarPlot50VsMinMaxC(mbm, 1.25)
    makeRadarPlot50VsMinMaxC(mbm, 1.5)
    makeRadarPlot50VsMinMaxC(mbm, 1.75)
    makeRadarPlot50VsMinMaxC(mbm, 2)
    '''


    '''
    makeRadarPlotCluster50Comp(mbm, 1)
    makeRadarPlotCluster50Comp(mbm, 1.25)
    makeRadarPlotCluster50Comp(mbm, 1.5)
    makeRadarPlotCluster50Comp(mbm, 1.75)
    makeRadarPlotCluster50Comp(mbm, 2)
    '''

