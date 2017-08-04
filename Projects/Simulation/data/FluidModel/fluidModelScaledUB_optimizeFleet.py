import cPickle

def fluidModelFleet(sM, mbm, timeLB, timeUB):
	sidList = []
	stationFlows = {}

	# For each station, calculate full day flow
	for sid in sM.keys():
		# Set up stationFlows dictionary, which will hold fluid model results
		sidList.append(sid)
		stationFlows[sid] = {}

		initLevel = sM[sid]["bikes"]
		sM[sid]["initBikes"] = initLevel
		sM[sid]["initCapacity"] = sM[sid]["capacity"]
		if sM[sid]["initCapacity"] == 0:
			sM[sid]["bikes"] = 0

		else: 
			# RESET bikes (filled through scaling)
			sM[sid]["bikes"] = "temp"

			# Set up dictionary to store objective values for each possible bike level
			sM[sid]["obj"] = {}

			for b in range(sM[sid]["capacity"]+1):
				level = b
				objValue = 0

				# At each 30 minute interval of specified time range, update the bike level based on the net flow
				for time in range(timeLB*60,timeUB*60,30):
					i = time/30 #convert to 0-47
					outflow = 0
					inflow = 0
					if mbm[sid].has_key(i): 
						outflow = mbm[sid][i][1]
					if mbm[sid].has_key(i): 
						inflow = mbm[sid][i][0]
					netflow = (inflow - outflow)*.75*30

					levelTest = level + netflow
					if levelTest > sM[sid]["capacity"]: # If levelTest exceeds capacity, increase obj value and set level to capacity
						objValue += abs(levelTest - sM[sid]["capacity"])
						level = sM[sid]["capacity"]
					elif levelTest < 0: # If levelTest falls below 0, increase obj value and set level to 0
						objValue += abs(levelTest)
						level = 0
					else: # If levelTest within range, update level
						level = levelTest

				sM[sid]["obj"][b] = objValue

			sM[sid]["bikes"] = min(sM[sid]["obj"].iterkeys(), key=(lambda key: sM[sid]["obj"][key]))

	print sum(sM[i]["bikes"] for i in sM.keys())
	print sum(sM[i]["capacity"] for i in sM.keys())

	return sM


if __name__ == '__main__':
	# mbm15x = cPickle.load(open("./April19_gradSearchCaps/data/mbm30minDec_15x.p", 'r'))
	mbm2x = eval(open('./Data/multipliedflowdictDec2.txt').read())
	sM15x = eval(open('./Data/AverageAllocationFromNames.txt').read())

	result = fluidModelFleet(sM15x, mbm2x, 6, 24) 


	cPickle.dump(result, open("./Results/fluidModelUBFleet.p", 'wb'))

	resultCSV = {}
	for i in result.keys():
		resultCSV[i] = {}
		resultCSV[i]['name'] = result[i]['name']
		resultCSV[i]['ords'] = result[i]['ords']
		resultCSV[i]['initBikes'] = result[i]['initBikes']
		resultCSV[i]['initCapacity'] = result[i]['initCapacity']
		resultCSV[i]['bikes'] = result[i]['bikes']
		resultCSV[i]['capacity'] = result[i]['capacity']

	from csv import DictWriter
	with open('./Results/fluidModelScaledWithUBFleet.csv', 'wb') as f:
	    writer = DictWriter(f, ['key', 'name', 'ords', 'initBikes', 'initCapacity', 'bikes', 'capacity'])
	    writer.writerow(dict(zip(writer.fieldnames, writer.fieldnames))) # no automatic header :-(
	    for key,values in resultCSV.items():
	        writer.writerow(dict(key=key, **values)) # first make a new dict merging the key and the values