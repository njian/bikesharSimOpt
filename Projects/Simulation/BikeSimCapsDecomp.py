'''

Module to perform a basic simulation of a bike sharing system

@eoinomahony

    editted by Nanjing Jian & Holly Wiberg for simulation optimization purpose

'''

from heapq import *

# import BikeSimDBBackend

# import MapMaker

import math
import numpy
# import time

##
# Utility functions
##

GLOBAL_TRIP_ID = 0
def getTripID():
    global GLOBAL_TRIP_ID
    res = GLOBAL_TRIP_ID
    GLOBAL_TRIP_ID += 1
    return res

GLOBAL_VEHICLE_ID = 0
def getVehicleID():
    global GLOBAL_VEHICLE_ID
    res = GLOBAL_VEHICLE_ID
    GLOBAL_VEHICLE_ID += 1
    return res

def getStatMap():
    return None
    # return BikeSimDBBackend.loadStationPickle()

def addDepots(statMap):
    return statMap

''' NJ: ALIAS for sampling multinomial '''
''' https://hips.seas.harvard.edu/blog/2013/03/03/
the-alias-method-efficient-sampling-with-many-discrete-outcomes/'''
def alias_setup(probs):
    K = len(probs)
    q = numpy.zeros(K)
    J = numpy.zeros(K, dtype=numpy.int)

    # Sort the data into the outcomes with probabilities
    # that are larger and smaller than 1/K.
    smaller = []
    larger  = []
    for kk, prob in enumerate(probs):
        q[kk] = K*prob
        if q[kk] < 1.0:
            smaller.append(kk)
        else:
            larger.append(kk)

    # Loop though and create little binary mixtures that
    # appropriately allocate the larger outcomes over the
    # overall uniform mixture.
    while len(smaller) > 0 and len(larger) > 0:
        small = smaller.pop()
        large = larger.pop()

        J[small] = large
        q[large] = q[large] - 1.0 + q[small]

        if q[large] < 1.0:
            smaller.append(large)
        else:
            larger.append(large)

    return J, q

def alias_draw_n(J, q, nsamples):
    K  = len(J)
    sample = []

    for i in range(nsamples):
        # Draw from the overall uniform mixture.
        kk = int(numpy.floor(numpy.random.rand()*K))
        # Draw from the binary mixture, either keeping the
        # small one, or choosing the associated larger one.
        if numpy.random.rand() < q[kk]:
            sample.append(kk)
        else:
            sample.append(J[kk])

    return sample
##
#
##
class Trip(object):

    # Constants to maintain trip state
    TRIPOK = 0
    STARTFAILED = 1
    ENDFAILED = 2
    TRIPENDOK = 3
    TRIPENDBAD = 4

    def __init__(self, startTime, startLoc, endTime, endLoc, duration,
                 clock, tid=getTripID(), statMap={}, tgen=None, failedEndSid=None):
        self.tid = tid
        self.startTime = startTime
        self.startLoc = startLoc
        self.endTime = endTime
        self.endLoc = endLoc
        self.clock = clock
        self.state = self.TRIPOK

        self.statMap = statMap
        self.tgen = tgen
        self.failedEndSid = failedEndSid

        # Maintain a list of stations we tried to end the trip at
        self.visitedEnds = []

    ##
    # End the trip, if all was ok we have a TRIPOK state
    # otherwise we have a bad end trip
    ##
    def endTrip(self, ):
        if self.state is self.TRIPOK:
            self.state = self.TRIPENDOK
        elif self.state is self.ENDFAILED:
            self.state = self.ENDFAILED
        else: self.state = self.TRIPENDBAD

    ##
    # If we attempt to end the trip but it does not work
    # we need to find somewhere else to end the trip
    ##
    def failEnd(self, ):
        self.state = self.ENDFAILED
        self.visitedEnds.append(self.endLoc)

        if len(self.visitedEnds) == 1:
            self.failedEndSid = self.endLoc

        if len(self.visitedEnds) < 3:
            newEndLoc = self.findAltEnding()
            newEndTime = self.tgen.getDuration(self.endLoc,
                                        newEndLoc, self.endTime, len(self.visitedEnds))
            self.endLoc = newEndLoc
            self.endTime += newEndTime
            return self
        else:
            self.state = self.TRIPENDBAD
            return None


    def findAltEnding(self, ):
        # We need to look at another place to end the trip
        others = [(stat.sid, stat.distanceTo(self.statMap[self.endLoc]) )
                for stat in self.statMap.values() if stat.sid not in self.visitedEnds]
        others = sorted(others, key=lambda x: x[1])
        return others[0][0]

    def failStart(self, ):
        self.state = self.STARTFAILED

    ##
    # We are compared on our endTimes which is the next time
    # the simulation must process something
    ##
    def __cmp__(self, other):
        return cmp(self.endTime, other)

##
# Class to handle a vehicle
##
class Vehicle(object):
    #code

    TRAILER = 0
    TRUCK = 1

    INITIAL = 2
    TRAVELING = 3
    LOADING = 4
    WAITING = 5
    UNLOADING = 6

    def __init__(self, vtype, capacity, bikes, router):
        self.vid = getVehicleID()
        self.vtype = vtype

        self.capacity = capacity
        self.bikes = bikes

        self.router = router
        self.state = Vehicle.INITIAL

        self.totalPicked = 0
        self.totalDropped = 0
        self.statSoft = 5

    ##
    # Try to drop as much as possible, if we can't we wait
    # at the station to keep dropping them off
    ##
    def drop(self, stat):
        self.state = Vehicle.UNLOADING

        if stat.cap - (stat.level + self.statSoft) >= self.bikes:
            stat.level += self.bikes
            self.totalDropped += self.bikes
            self.bikes = 0
            self.state = Vehicle.TRAVELING
            return True
        else:
            # There is a gap
            gap = stat.cap - (stat.level+self.statSoft)
            if gap > 0:
                stat.level += gap
                self.totalDropped += gap
                self.bikes -= gap
            return False

    ##
    # Try to pick up as many bikes as possible
    # wait until you can fill up
    ##
    def pick(self, stat):
        self.state = Vehicle.LOADING
        gap = self.capacity - self.bikes
        if (stat.level - self.statSoft) >= gap:
            self.bikes += self.capacity
            self.totalPicked += self.capacity
            stat.level -= gap
            self.state = Vehicle.TRAVELING
            return True
        elif stat.level > self.statSoft:
            self.bikes += stat.level - self.statSoft
            self.totalPicked += stat.level - self.statSoft
            stat.level = self.statSoft
            return False
        else: return False

    def tick(self, time, statMap):
        self.router.tick(time, statMap)

##
#
##
class Trailer(Vehicle):
    def __init__(self, router):
        Vehicle.__init__(self, Vehicle.TRAILER, 4, 0, router)
        self.router.bike = self

##
#
##
class BikeTrailerRouter(object):

    def __init__(self, pair, ttime, starttime, endtime):
        self.bike = None
        self.pair = pair
        self.ttime = ttime
        self.at = pair[0]

        self.nextTime = 0
        self.starttime = starttime
        self.endtime = endtime

    ##
    # What should we do this timestep
    ##
    def tick(self, time, statMap):

        # While I am in my operation window and not waiting for something to happen
        if time >= self.starttime and time <= self.endtime and time >= self.nextTime:

            # We find where we need to go next
            going = [stat for stat in self.pair if stat is not self.at][0]

            # We try to load/unload
            action = self.getAction(statMap)

            # If its a success we move
            if action is True:
                self.at = going
                self.nextTime = time + self.ttime
            # Otherwise we wait here
            else:
                self.nextTime = time + self.ttime


    def getAction(self, statMap):
        sid = self.at
        if sid == self.pair[0]:
            return self.bike.pick(statMap[self.at])
        else: return self.bike.drop(statMap[self.at])

##
#
##
class Station(object):

    def __init__(self, sid, name, cap, level, clock, ords=None):
        self.sid = sid
        self.name = name
        self.cap = cap
        self.level = level
        self.clock = clock
        self.ords = ords

        # Record state over time
        self.levelTime = []

        self.tripsOut = []
        self.tripsIn = []
        self.tripsFailedOut = []
        self.tripsFailedIn = []

    def tripIn(self, trip):
        if self.cap > self.level:
            trip.endTrip()
            self.level += 1
            return None
        else:
            return trip.failEnd()

    def tripOut(self, trip):
        if self.level == 0:
            trip.failStart()
            return False
        else:
            self.level -= 1
            return True

    def recordTime(self, time):
        self.levelTime.append(self.level)

    def tick(self, time): self.recordTime(time)

    def distanceTo(self, stat):
        return ((stat.ords[0] - self.ords[0])*(stat.ords[0] - self.ords[0]) +
                (stat.ords[1] - self.ords[1])*(stat.ords[1] - self.ords[1]) )

    def getOutageMins(self, ):
        res = [  ]
        for l in self.levelTime:
            if l == 0 or l == self.cap:
                res.append(1)
            else: res.append(0)
        return res

    def getEmptyMins(self, ):
        res = [  ]
        for l in self.levelTime:
            if l == 0:
                res.append(1)
            else: res.append(0)
        return res

    def getFullMins(self, ):
        res = [  ]
        for l in self.levelTime:
            if l == self.cap:
                res.append(1)
            else: res.append(0)
        return res

    def getSla(self):
        res = [  ]
        for l in self.levelTime:
            if l == 0 or l == self.cap:
                res.append(1)
            else: res.append(0)
        return sum(res[6*60:22*60])

##
# Class that will process the events
##
class GlobalClock(object):

    ##
    #
    ##
    def __init__(self, startTime, stationMap, tripGenerator,
                 imageDir=None, imageFreq=20, vehicles=[],
                 verbosity=1, durList={}):
        ''' IMPORTANT: initialized to start from 7am'''
        self.time = startTime
        self.heap = []

        self.statMap = stationMap
        self.tripGen = tripGenerator

        self.trips = []

        self.vehicles = vehicles

        self.imageDir = imageDir
        self.imageFreq = imageFreq
        self.imageCount = 0

        self.verbosity = verbosity

        self.durList = durList

    def printTripStatus(self, ):
        print self.time,
        print len(filter(lambda x: x.state is Trip.TRIPOK, self.trips)),
        print len(filter(lambda x: x.state is Trip.TRIPENDOK, self.trips)),
        print len(filter(lambda x: x.state is Trip.STARTFAILED, self.trips)),
        print len(filter(lambda x: x.state is Trip.ENDFAILED, self.trips)),
        print len(filter(lambda x: x.state is Trip.TRIPENDBAD, self.trips)),
        print len(self.trips)

    def getTripOk(self, ):
        return  len(filter(lambda x: x.state is Trip.TRIPENDOK, self.trips))

    def getFailedStarts(self, ):
        return  len(filter(lambda x: x.state is Trip.STARTFAILED, self.trips))

    def getFailedStartsAM(self, ):
        return  len(filter(lambda x: x.state is Trip.STARTFAILED and x.startTime < 600, self.trips))

    def getFailedStartsPM(self, ):
        return  len(filter(lambda x: x.state is Trip.STARTFAILED and x.startTime >= 600, self.trips))

    def getCompletedTrips(self, ):
        return len(filter(lambda x:x.state in [Trip.TRIPENDOK,Trip.ENDFAILED], self.trips))

    def getFailedEnds(self, ):
        return len(filter(lambda x: x.state is Trip.TRIPENDBAD, self.trips))

    def getAlterEnd(self, ):
        return len(filter(lambda x: x.state is Trip.ENDFAILED, self.trips))

    def getAlterEndAM(self, ):
        return len(filter(lambda x: x.state is Trip.ENDFAILED and x.startTime < 600, self.trips))

    def getAlterEndPM(self, ):
        return len(filter(lambda x: x.state is Trip.ENDFAILED and x.startTime >= 600, self.trips))

    def getOutageMins(self,):
        return sum( map(lambda x: sum(x.getOutageMins()), self.statMap.values()))

    def getTotalTrips(self, ):
        return len(self.trips)

    def getEmptyMins(self, ):
        return sum( map(lambda x: sum(x.getEmptyMins()), self.statMap.values()))

    def getFullMins(self, ):
        return sum( map(lambda x: sum(x.getFullMins()), self.statMap.values()))

    ''' Editted to return station with max failed starts and max failed ends'''
    def getFailedStartsStation(self, ):
        slist = map(lambda x: x.startLoc, filter(lambda x: x.state is Trip.STARTFAILED, self.trips))
        # if len(slist) == 0:
        #     return -1
        # else:
        return slist

    def getFailedStartsStationAM(self, ):
        slist = map(lambda x: x.startLoc, filter(lambda x: x.state is Trip.STARTFAILED and x.startTime < 600, self.trips))
        # if len(slist) == 0:
        #     return -1
        # else:
        return slist

    def getFailedStartsStationPM(self, ):
        slist = map(lambda x: x.startLoc, filter(lambda x: x.state is Trip.STARTFAILED and x.startTime >= 600, self.trips))
        # if len(slist) == 0:
        #     return -1
        # else:
        return slist

    def getAlterEndsStation(self, ):
        slist = map(lambda x: x.failedEndSid, filter(lambda x: x.failedEndSid is not None, self.trips))
        # if len(slist) == 0:
        #     return -1
        # else:
        return slist

    def getAlterEndsStationAM(self, ):
        slist = map(lambda x: x.failedEndSid, filter(lambda x: x.failedEndSid is not None and x.startTime < 600, self.trips))
        # if len(slist) == 0:
        #     return -1
        # else:
        return slist

    def getAlterEndsStationPM(self, ):
        slist = map(lambda x: x.failedEndSid, filter(lambda x: x.failedEndSid is not None and x.startTime >= 600, self.trips))
        # if len(slist) == 0:
        #     return -1
        # else:
        return slist

    # ''' Editted to return station with max empty mins and max full mins '''
    # def getMaxEmptyMinsStat(self, ):
    #     listE = map(lambda x: sum(x.getEmptyMins()), self.statMap.values())
    #     maxE = listE.index(max(listE))
    #     return Array(self.statMap)[maxE].0

    # def getMaxFullMinsStat(self, ):
    #     listF = map(lambda x: sum(x.getFullMins()), self.statMap.values())
    #     maxF = listE.index(max(listF))
    #     return Array(self.statMap)[maxF].0


    def getScatterPlotData(self, result = {}, numsamples=1):

        for trip in filter(lambda x: x.state is Trip.TRIPENDOK, self.trips):
            oID = trip.startLoc
            dID = trip.endLoc
            if not result.has_key(oID):
                result[oID] = {}
            if not result[oID].has_key(dID):
                result[oID][dID] = 1/float(numsamples)
            else: result[oID][dID] += 1/float(numsamples)
        return result

    def getScatterPlotDataTimes(self, result = {}, numsamples=1):

        for trip in filter(lambda x: x.state in
                           [Trip.TRIPENDOK,Trip.ENDFAILED], self.trips):
            startTime = trip.startTime
            endTime = trip.endTime

            if not result.has_key(startTime/10):
                result[startTime/10] = [ 1/float(numsamples),0 ]
            else: result[startTime/10][0] += 1/float(numsamples)

            if not result.has_key(endTime/10):
                result[endTime/10] = [0,1/float(numsamples)]
            else: result[endTime/10][1] += 1/float(numsamples)

        return result

    def tick_original(self, minTrips):
        if self.verbosity is 1: self.printTripStatus()

        # Get new trips to start
        badEndTrips = []

        # First we process what can happen at the current time
        toProc = []
        while len(self.heap) > 0 and self.heap[0] < self.time:
            # Now process these, assume they are all trips for now
            trip = heappop(self.heap)
            if trip.endLoc is not None and self.statMap.has_key(trip.endLoc): # mismatch statMap: may not have endLoc
                tin = self.statMap[trip.endLoc].tripIn(trip)
                if tin is not None: badEndTrips.append(tin)

        # Then we make new end point trips happen
        for trip in badEndTrips:
            heappush(self.heap, trip)

        # Then we make new trips happen
        # numpy.random.seed(Config.seeds[0])
        tripList = minTrips
        for trip in tripList:
            tok = self.statMap[trip.startLoc].tripOut(trip)
            self.trips.append(trip)
            if tok: heappush(self.heap, trip)

        for stat in self.statMap.values():
            stat.tick(self.time)

        # Now we deal with rebalancing
        # for v in self.vehicles: v.tick(self.time, self.statMap)

        # Should we dump out an image
        if self.imageDir is not None:
            if self.time % self.imageFreq is 0:
                self.dumpImage()

        # for sid in [423,382]:
        #     fileName = ("./outputsDO/lvlInDay/sid"+str(sid)+"lvlInDay"+str(1)+".p")
        #     levels = cPickle.load(open(fileName, 'r'))
        #     levels[self.time] = self.statMap[sid].level
        #     cPickle.dump(levels, open(fileName, 'wb'))

        # At the end of tick we increment the time
        self.time += 1

    def dumpImage(self):
        gmap = MapMaker.Map()
        for stat in self.statMap.values():
            if stat.cap > 0:
                pct = stat.level/float(stat.cap)
                gmap.addCircle(MapMaker.Circle( stat.ords, pct = pct))
        gmap.produceImage(self.imageDir+"/%d_state.png" % self.imageCount,
                          "%02d:%02d" % (self.time/60, self.time%60))
        self.imageCount += 1

    def addTripToProcess(self, trip):
        heapq.heappush(self.heap, trip)

##
#
##
class TripGenerator(object):
    #code

    def __init__(self, statMap, minbymin, durations, mult = 1):
        self.statMap = statMap
        self.tid = 0
        self.minbymin = minbymin
        self.mult = mult
        self.durations = durations

    # runDay_alt2 method for generating trips

    def getAllTripsCombined(self, timeStart):
        # Initialize dictionary with keys = minutes in interval. Entry = list of trips for that minute
        trips = {}
        for i in range(30):
            trips[timeStart+i] = []

        for sid in self.statMap.keys():
            # First, check corner cases
            if not self.minbymin[timeStart].has_key(sid): continue
            if self.minbymin[timeStart][sid]["total"] == 0: continue
            if not self.statMap.has_key(sid): continue

            # Get trip counts for full 30 minute interval
            n = numpy.random.poisson(self.minbymin[timeStart][sid]["total"], size = 30)
            totalTrips = sum(n)

            # Get list of all destinations
            total = self.minbymin[timeStart][sid]["total"]
            dests = self.minbymin[timeStart][sid]["dests"].keys()
            distr = map(lambda x: x/float(total),
                   self.minbymin[timeStart][sid]["dests"].values())
            ''' NJ: tolist() converts numpy array to list, so can use .index later'''
            res = numpy.random.multinomial(1, distr, size = totalTrips).tolist()

            ''' NJ: the creation of allDests and its two for loops can be avoided. See below '''
            # allDests = []
            # for r in range(totalTrips):
            #     for i in range(len(res[r])):
            #         if res[r][i] == 1: allDests.append(dests[i])

            # Assign trips to the dictionary entry for their respective minute
            count = 0
            for i in range(30):
                # Get trips for ith minute (time = timeStart + i)
                time = timeStart + i
                # j in number of trips at time
                for j in range(n[i]):
                    ''' NJ: .index(1) returns the index corresponding to the value 1. It is faster than a
                    for loop and can be used since there is only one 1'''
                    dest = dests[res[count].index(1)]
                    duration = self.getDuration(sid, dest, time)
                    newTrip = Trip(startTime = time, startLoc = sid,
                        endTime = time + duration, endLoc = dest,
                        duration = duration, clock = time, statMap=self.statMap,
                               tgen = self)
                    # Add new trips to full trip dictionary under minute "time"
                    trips[time].append(newTrip)
                    count += 1

            # DEBUGGING
            if count != totalTrips:
                print "Error creating trip list"
        return trips

    # def getAllTripsCombinedAlias(self, timeStart):
    #     # Initialize dictionary with keys = minutes in interval. Entry = list of trips for that minute
    #     trips = {}
    #     for i in range(30):
    #         trips[timeStart+i] = []

    #     for sid in self.statMap.keys():
    #         # First, check corner cases
    #         if not self.minbymin[timeStart].has_key(sid): continue
    #         if self.minbymin[timeStart][sid]["total"] == 0: continue
    #         if not self.statMap.has_key(sid): continue

    #         # Get trip counts for full 30 minute interval
    #         n = numpy.random.poisson(self.minbymin[timeStart][sid]["total"], size = 30)
    #         totalTrips = sum(n)

    #         # Get list of all destinations
    #         total = self.minbymin[timeStart][sid]["total"]
    #         dests = self.minbymin[timeStart][sid]["dests"].keys()
    #         distr = map(lambda x: x/float(total),
    #                self.minbymin[timeStart][sid]["dests"].values())
    #         t0 = time.time()
    #         J, q = alias_setup(distr) # do the setup for alias once every 30 minutes
    #         setupTime = time.time() - t0
    #         destIndex = alias_draw_n(J, q, totalTrips) # draw all the destinations

    #         # Assign trips to the dictionary entry for their respective minute
    #         count = 0
    #         for i in range(30):
    #             t = timeStart + i
    #             # j in number of trips at time
    #             for j in range(1, n[i]+1):
    #                 dest = dests[destIndex[count]]
    #                 duration = self.getDuration(sid, dest, time)
    #                 newTrip = Trip(startTime = t, startLoc = sid,
    #                     endTime = t + duration, endLoc = dest,
    #                     duration = duration, clock = t, statMap=self.statMap,
    #                            tgen = self)
    #                 # Add new trips to full trip dictionary under minute "time"
    #                 trips[t].append(newTrip)
    #                 count += 1

    #         # DEBUGGING
    #         if count != totalTrips:
    #             print "Error creating trip list"
    #     return trips

    def getAllTripsCombinedCond(self, timeStart):
        # Initialize dictionary with keys = minutes in interval. Entry = list of trips for that minute
        trips = {}
        for i in range(30):
            trips[timeStart+i] = []

        for sid in self.statMap.keys():
            # First, check corner cases
            if not self.minbymin[timeStart].has_key(sid): continue
            if self.minbymin[timeStart][sid]["total"] == 0: continue
            if not self.statMap.has_key(sid): continue

            # Get trip counts for full 30 minute interval
            totalTrips = numpy.random.poisson(self.minbymin[timeStart][sid]["total"]*30, size = 1)

            # Get list of all destinations
            total = self.minbymin[timeStart][sid]["total"]
            dests = self.minbymin[timeStart][sid]["dests"].keys()
            distr = map(lambda x: x/float(total),
                   self.minbymin[timeStart][sid]["dests"].values())
            res = numpy.random.multinomial(1, distr, size = totalTrips).tolist()

            ts = timeStart + numpy.random.randint(30, size=totalTrips)
            # Assign trips to the dictionary entry for their respective minute
            for i in range(totalTrips):
                ''' Poisson Process property: conditioning on number of arrivals in [0,T],
                the time of arrivals is uniform in [0,T]. Here we use the discrete uniform.'''
                time = int(ts[i])
                dest = dests[res[i].index(1)]
                duration = self.getDuration(sid, dest, time)
                newTrip = Trip(startTime = time, startLoc = sid,
                    endTime = time + duration, endLoc = dest,
                    duration = duration, clock = time, statMap=self.statMap,
                           tgen = self)
                trips[time].append(newTrip)
        return trips

    ''' runDay_original methods for generating trips '''
    def generateTrips(self, timeValue):
        trips = []
        for s1 in self.statMap.keys():
            trips.extend(self.getTrips(s1, timeValue))
        return trips

    def getTrips(self, sid, time):
        if not self.minbymin[time-time%30].has_key(sid): return []
        if self.minbymin[time-time%30][sid]["total"] == 0: return []
        if not self.statMap.has_key(sid): return []

        numberTrips = numpy.random.poisson(self.minbymin[time-time%30][sid]["total"]*
                                           self.mult)

        trips = []
        for t in range(numberTrips):
            dest = self.getWhereTripGoing(sid, time)
            duration = self.getDuration(sid, dest, time)
            newTrip = Trip(time, sid, time+duration, dest,
                           duration, time, statMap=self.statMap,
                           tgen = self)
            trips.append(newTrip)
        return trips

    def getWhereTripGoing(self, s1, time):
        total = self.minbymin[time-time%30][s1]["total"]
        dests = self.minbymin[time-time%30][s1]["dests"].keys()
        distr = map(lambda x: x/float(total),
                self.minbymin[time-time%30][s1]["dests"].values())
        for i in range(len(res)):
            if res[i] == 1: return dests[i]


    def getDuration(self, s1, s2, t, ind=None):
        # if not self.minbymin.has_key(t-t%30):
        #     # print "Warning: Time %d has no key" %t
        #     return 10
        # if not self.minbymin[t-t%30].has_key(s1):
        #     # print "Warning: sid=%d has no key at time %d" %(s1,t)
        #     return 10
        # if not self.minbymin[t-t%30][s1]["durations"].has_key(s2):
        #     # print "Warning: s1=%d has no duration key to s2=%d at time %d" %(s1,s2,t)
        #     return 10

        # if ind is None:
        #     duration = int(round(numpy.random.poisson(self.durations[s1][s2])/60.0))
        # else:
        #     state = numpy.random.get_state()
        #     duration = int(round(numpy.random.poisson(self.durations[s1][s2])/60.0))
        #     numpy.random.set_state(state) # Restore state
        # return duration

        # intercept = 0.5769 
        # slope = 0.9116
        # sigma = 0.2389 # sqrt of 0.0570636366697
        # est = self.durations[s1][s2]

        # ''' If ind=None, this is called when generating the trip list, so return one duration. If ind = 1 or 2,
        # meaning ind number of failedEnds has been triggered, return duration without affecting the
        # random number cycle'''
        # if ind is None:
        #     duration = numpy.exp(slope*numpy.log(est) + numpy.random.normal(0,sigma) + intercept)/60.0
        #     # duration = numpy.random.poisson(self.minbymin[t-t%30][s1]["durations"][s2]/60.0)
        # else:
        #     state = numpy.random.get_state()
        #     # numpy.random.RandomState() # Start a new stream
        #     duration = numpy.exp(slope*numpy.log(est) + numpy.random.normal(0,sigma) + intercept)/60.0
        #     numpy.random.set_state(state) # Restore state
        # return duration

        # sigma = numpy.sqrt(0.0657409799597)
        # intercept= 0.229073863936
        # slope= 0.929447637457
        # est = self.durations[s1][s2]/60.0
        # if ind is None:
        #     duration = numpy.exp(slope*numpy.log(est) + numpy.random.normal(0,sigma) + intercept)
        # else:
        #     state = numpy.random.get_state()
        #     duration = numpy.exp(slope*numpy.log(est) + numpy.random.normal(0,sigma) + intercept)
        #     numpy.random.set_state(state) # Restore state
        # return duration

        
        sigma = 0.2571 # sqrt of 0.0661117309208
        mult = self.durations[s1][s2]
        ''' If ind=None, this is called when generating the trip list, so return one duration. If ind = 1 or 2,
        meaning ind number of failedEnds has been triggered, return duration without affecting the
        random number cycle'''
        if ind is None:
            duration = int(round(mult*numpy.random.lognormal(0,sigma)))
        else:
            state = numpy.random.get_state()
            # numpy.random.RandomState() # Start a new stream
            duration = int(round(mult*numpy.random.lognormal(0,sigma)))
            numpy.random.set_state(state) # Restore state
        return duration

if __name__ == "__main__":
    pass