import cPickle
import operator

def allLevelsInDay(sM, mbm, startTime, endTime):
	''' 
	Returns {sid: list of level in day of that sid}.
	Inputs: see levelInDay().
	'''
	stationFlows = {}
	# For each station, calculate flows throughout day
	for sid in sM:
		# Set up stationFlows dictionary, which will hold fluid model results
		stationFlows[sid] = levelInDay(sid, sM[sid]['bikes'], sM[sid]['capacity'], mbm, startTime, endTime)
	return stationFlows


def levelInDay(sid, bikes, capacity, mbm, startTime, endTime):
	''' 
	Returns a a list that's level in the day at the beginning of each 30min intervals between startTime and endTime.
	Inputs:
		sid, bikes, capacity: inquired sid and its level of bikes at startTime and capacity
		sM: station map at startTime
		mbm: min-by-min (actually every 30 min) flow rates
		startTime, endTime: in minutes	
	'''
	levelList = [bikes]
	level = bikes

	# At each 30 minute interval of specified time range, update the bike level based on the net flow
	for time in range(startTime, endTime, 30):
		outflow = 0
		inflow = 0
		# outflow = total flow out of sid at that time
		if mbm[time].has_key(sid):
			outflow = mbm[time][sid]['total']
		# inflow = total flow out of the origin stations that have trips to sid at that time
		# this is assuming trips have duration 0
		for origin in mbm[time].keys():
			if mbm[time][origin]['dests'].has_key(sid):
				inflow += mbm[time][origin]['dests'][sid]

		netflow = (inflow - outflow)*30

		# sM[sid]["netFlows"].append(netflow)
		level = level + netflow
		levelList.append(level)

	return levelList


# def getObjective(sid, bikes, capacity, mbm):
def getCorralStations(stationFlows, sM, startTime, endTime):
	'''	For each 30 minute interval, get a ranked list of station in the order of maximum failedEnds 
		returns {minute in day: [sid (that corresponds to), most failedEnd]} '''
	corralSid = {}
	start = (startTime * 60) / 30 # the index of 30-min interval in the day
	end = (endTime * 60) / 30
	for t1 in range(start, end, 1): # begin index
		t2 = t1 + 1 # end index
		sidFailedEnd = []
		for sid in sM:
			failedEnd1 = max(stationFlows[sid][t1 - start] - sM[sid]['capacity'], 0)
			failedEnd2 = max(stationFlows[sid][t2 - start] - sM[sid]['capacity'], 0)
			failedEnd = abs(failedEnd1 - failedEnd2)
			sidFailedEnd.append([sid, failedEnd])
		sidFailedEnd.sort(key=operator.itemgetter(1), reverse=True)
		corralSid[t1*30] = sidFailedEnd #[sidFailedEnd[0][0], sidFailedEnd[0][1]]
		# sidFailedEnd[i] = [sid, the number of failedEnds of that sid which ranked i-th]
		print sidFailedEnd[0][0], sidFailedEnd[0][1], sidFailedEnd[1][0], sidFailedEnd[1][1]
	return corralSid


if __name__ == '__main__':

	timeLB = 7
	timeUB = 19 # either 10 or 24
	
	# read data
	mbm = cPickle.load(open("./data/mbm30minDec_15x.p", 'r'))
	solutionFile = 'fluidModelUB_Dec15x'
	sM = cPickle.load(open('./data/%s.p' % solutionFile, 'r'))
	with open('./data/realBikes7_20161115.txt', 'r') as f:
		data = eval(f.read())
	for item in data['stationBeanList']:
		sid = item['id']
		if sM.has_key(sid):
			sM[sid]['bikes'] = item['availableBikes']
			sM[sid]['capacity'] = item['totalDocks']

	# get the level list of each station
	stationFlows = allLevelsInDay(sM, mbm, timeLB*60, timeUB*60)
	cPickle.dump(stationFlows, open('./fluidModel/levelList_'+str(timeLB)+'-'+str(timeUB)+'.p', 'wb'))

	# get the ranked locations of corrals at each time interval
	corralTime = getCorralStations(stationFlows, sM, timeLB, timeUB)
	cPickle.dump(corralTime, open('./fluidModel/corrals_'+str(timeLB)+'-'+str(timeUB)+'.p', 'wb'))

	resultCSV = {}
	for t in range(timeLB * 60, timeUB * 60, 30):
		resultCSV[t] = {}
		resultCSV[t]['startTime'] = t
		sid = corralTime[t][0][0]
		resultCSV[t]['sid'] = sid
		resultCSV[t]['name'] = sM[sid]['name']
		resultCSV[t]['ords'] = sM[sid]['ords']
		resultCSV[t]['bikes'] = sM[sid]['bikes']
		resultCSV[t]['capacity'] = sM[sid]['capacity']
		resultCSV[t]['failedEnds'] = corralTime[t][0][1]


	numCorrals = 3
	import csv
	fieldnames = ["startTime", "sid", "name", "longitude", "latitude", "level", "capacity", "failedEnds"]
	with open('./fluidModel/corralPlacement3_realBikes_'+str(timeLB)+'-'+str(timeUB)+'.csv', 'wb') as csvfile:
		writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
		writer.writeheader()
		filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
		for t in resultCSV.keys():
			for k in range(numCorrals):
				sid = corralTime[t][k][0]
				filewriter.writerow((resultCSV[t]['startTime'], sid, sM[sid]['name'], sM[sid]['ords'][1], sM[sid]['ords'][0], sM[sid]['bikes'], sM[sid]['capacity'], corralTime[t][k][1]))

