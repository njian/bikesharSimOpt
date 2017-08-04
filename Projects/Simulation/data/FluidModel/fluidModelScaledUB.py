import cPickle

def initFluidModel(sM, mbm, timeLB, timeUB):
	sidList = []
	stationFlows = {}

	# For each station, calculate flows throughout day
	for sid in sM:
		# Set up stationFlows dictionary, which will hold fluid model results
		sidList.append(sid)
		stationFlows[sid] = {}

		initLevel = sM[sid]["bikes"]
		sM[sid]["initBikes"] = initLevel
		sM[sid]["initCapacity"] = sM[sid]["capacity"]
		sM[sid]["levelList"] = [initLevel]

		# RESET bikes, capacity (filled through scaling)
		sM[sid]["bikes"] = "temp"
		sM[sid]["capacity"] = "temp"

		sM[sid]["netFlows"] = []

		level = initLevel

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

			sM[sid]["netFlows"].append(netflow)
			level = level + netflow
			sM[sid]["levelList"].append(level)

		levelList = sM[sid]["levelList"]

		# Calculate the minimum bikes and racks needed to meet the fluid model net flows with no failed starts/ends
		h = min(levelList)  # If positive, will reduce min bike level; if negative, will increase
		sM[sid]["minBikes"] = initLevel - h
		sM[sid]["minRacks"] = max(levelList) - h

	return sM

def scaleByBikesAndRacks(fm, totalBikes, totalRacks, bRatio, cRatio):

	'''Bike Scale bikes by bike ratio, racks by rack ratio. Adjust rounding to match total system bikes and racks'''

	# initialize available bikes and racks at system totals
	availBikes = totalBikes
	availRacks = totalRacks

	for i in fm.keys():
		# Calculate scaled bikes/racks with bounds: (0,60) bikes, (16,60) racks
		fm[i]['bikes'] = min(round(bRatio*fm[i]['minBikes']),60)
		fm[i]['capacity'] = min(max(round(cRatio*fm[i]['minRacks']),16),60)

		#Calculate the difference between the scaled bikes and ideal fluid model bikes 
		fm[i]['diffBikes'] = round(fm[i]['minBikes']) - fm[i]['bikes']
		availBikes -= fm[i]['bikes']
		availRacks -= fm[i]['capacity'] 

	# Adjust racks if necessary after scaling: assign to highest capacity stations, take from lowest capacity stations
	if availRacks < 0:
		print "Initial scaling exceeds available racks by %d. Taken from lowest capacity stations" % (-1*availRacks)
		toTake = sorted(fm, key = lambda i: fm[i].get('capacity'), reverse = False)
		index = 0
		while availRacks < 0:
			sid = toTake[index]
			if fm[sid]['capacity'] > 16:
				fm[sid]['capacity'] -= 1
				availRacks += 1
			# Increment, or circle back if necessary
			if index < len(fm) - 1: 
				index += 1
			else:
				print "Rack index reset to 0"
				index = 0
	if availRacks > 0:
		print "Initial scaling results in excess of %d racks. Assigned to highest capacity stations" % availRacks
		toAdd = sorted(fm, key = lambda i: fm[i].get('capacity'), reverse = True)
		index = 0
		while availRacks > 0:
			sid = toAdd[index]
			if fm[sid]['capacity'] < 60:
				fm[sid]['capacity'] += 1
				availRacks -= 1
			# Increment, or circle back if necessary
			if index < len(fm) - 1: 
				index += 1
			else:
				print "Rack index reset to 0"
				index = 0

	# Adjust bikes if necessary after scaling: assign to stations with most bikes, take from stations with fewest bikes 
	if availBikes < 0:
		print "Initial scaling exceeds available bikes by %d. Taken from stations with fewest bikes" % (-1*availBikes)
		toTake = sorted(fm, key = lambda i: fm[i].get('bikes'), reverse = False)
		index = 0
		while availBikes < 0:
			sid = toTake[index]
			if fm[sid]['bikes'] > 0:
				fm[sid]['bikes'] -= 1
				availBikes += 1
			# Increment, or circle back if necessary
			if index < len(fm) - 1: 
				index += 1
			else:
				print "Bike index reset to 0"
				index = 0
	if availBikes > 0:
		print "Initial scaling results in excess of %d bikes. Assigned to stations with most bikes" % availBikes
		toAdd = sorted(fm, key = lambda i: fm[i].get('bikes'), reverse = True)
		index = 0
		while availBikes > 0:
			sid = toAdd[index]
			if fm[sid]['bikes'] < fm[sid]['capacity']:
				fm[sid]['bikes'] += 1
				availBikes -= 1
			# Increment, or circle back if necessary
			if index < len(fm) - 1: 
				index += 1
			else:
				print "Index reset to 0"
				index = 0

	return fm

def scaleByRacks(fm, totalBikes, totalRacks, cRatio):
	''' Helper function for chooseThreshold(): scales all racks and bikes by the rack ratio.
	Adjusts the racks to match the total racks in system (subject to 16-60 bounds)
	Bikes are adjusted through other functions wrapped in chooseThreshold()'''

	availBikes = totalBikes
	availRacks = totalRacks

	for i in fm.keys():

		# Calculate scaled bikes/racks
		fm[i]['bikes'] = min(round(cRatio*fm[i]['minBikes']),60)
		fm[i]['capacity'] = min(max(round(cRatio*fm[i]['minRacks']),16),60)

		#Calculate the difference between the scaled bikes and ideal fluid model bikes 
		fm[i]['diffBikes'] = min(60,round(fm[i]['minBikes'])) - fm[i]['bikes']
		availBikes -= fm[i]['bikes']
		availRacks -= fm[i]['capacity'] 

	# Adjust racks if necessary after scaling: assign to highest capacity stations, take from lowest capacity stations
	if availRacks < 0:
		print "Initial scaling exceeds available racks by %d. Taken from lowest capacity stations" % (-1*availRacks)
		toTake = sorted(fm, key = lambda i: fm[i].get('capacity'), reverse = False)
		index = 0
		while availRacks < 0:
			sid = toTake[index]
			if fm[sid]['capacity'] > 16:
				fm[sid]['capacity'] -= 1
				availRacks += 1
			# Increment, or circle back if necessary
			if index < len(fm) - 1: 
				index += 1
			else:
				print "Rack index reset to 0"
				index = 0
	if availRacks > 0:
		print "Initial scaling results in excess of %d racks. Assigned to highest capacity stations" % availRacks
		toAdd = sorted(fm, key = lambda i: fm[i].get('capacity'), reverse = True)
		index = 0
		while availRacks > 0:
			sid = toAdd[index]
			if fm[sid]['capacity'] < 60:
				fm[sid]['capacity'] += 1
				availRacks -= 1
			# Increment, or circle back if necessary
			if index < len(fm) - 1: 
				index += 1
			else:
				print "Rack index reset to 0"
				index = 0

	return fm

def assignBikes(current, threshold):
	''' Helper function for chooseThreshold(). Add bikes to stations based on a given threshold.
	For any stations that have 'diffBikes' > threshold, try to add the difference between them to that station.
	If the difference exceeds the number of empty racks, cap it at the station capacity to avoid overfilling the station.'''
	totalAdded = 0
	totalSystem = 0

	for i in current.keys():
		if current[i]['diffBikes'] < threshold: 
			numAdd = 0
		else: 
			numAdd = min(current[i]['diffBikes']-threshold, current[i]['capacity']-current[i]['bikes'])
		current[i]['numAdd'] = numAdd
		current[i]['bikes'] = current[i]['bikes'] + numAdd
		totalAdded += numAdd
		totalSystem += current[i]['bikes']

	return totalSystem, current

def chooseThreshold(fluidModel, totalBikes, totalRacks, cRatio):
	''' Scale everthing by the capacity ratio using scaleByRacks(). Adjust rounding to match total system racks. 
	Assign surplus bikes to stations using assignBikes(), where bikes are assigned based on the greatest difference between desired and scaled bikes. 
	This is done by iterating through thresholds (starting at the max 'diffBikes'), until there are no more extra bikes. Adjust if necessary to match system total'''

	current = scaleByRacks(fluidModel, totalBikes, totalRacks, cRatio)

	t = max(current[i]["diffBikes"] for i in current.keys()) # Initialize Threshold
	while True:
		totalSystem, assignment = assignBikes(current, t)

		if totalSystem < totalBikes and t > 0: # Reduce threshold to assign more bikes
			t -= 1

		elif t > 0: # Threshold assigned too many bikes -> adjust by taking from stations with 'diffBikes'=t (i.e. the last stations to get extra bikes)
			extra = totalSystem - totalBikes
			for i in assignment.keys():
				# add to stations with diffBik
				if extra > 0 and assignment[i]['diffBikes']==t and assignment[i]['bikes']>0:
					assignment[i]['bikes'] -= 1
					totalSystem -= 1
					extra -= 1
				else: 
					print "Assignment Complete: %d bikes assigned. Exceed available bikes by %d" % (totalSystem, totalBikes - totalSystem)
					print "Final Threshold: %d bikes" % t
					return assignment

		else: # Threshold has reached zero, but still not enough bikes assigned
			print "%d bikes remain after threshold reaches 0. Assign extra to stations with most bikes" %  (totalSystem - totalBikes)
			toAdd = sorted(assignment, key = lambda i: assignment[i].get('bikes'), reverse = True)
			index = 0
			while availBikes > 0:
				sid = toAdd[index]
				if assignment[sid]['bikes'] < assignment[sid]['capacity']:
					assignment[sid]['bikes'] += 1
					availBikes -= 1
				# Increment, or circle back if necessary
				if index < len(assignment) - 1: 
					index += 1
				else:
					print "Index reset to 0"
					index = 0
			return assignment

def fullFluidModel(sM, mbm, timeLB, timeUB):
	# Calculate initial fluid model min bikes and min racks
	fm = initFluidModel(sM,mbm, timeLB, timeUB)

	C = sum(fm[i]['initCapacity'] for i in fm.keys()) #actual total racks
	B = sum(fm[i]['initBikes'] for i in fm.keys()) # actual total bikes
	fmC = sum(fm[i]['minRacks'] for i in fm.keys()) # racks assigned over all stations in fluidModel
	fmB = sum(fm[i]['minBikes'] for i in fm.keys()) # bikes assigned over all stations in fluidModel

	# Calculate rack and bike ratios
	cRatio = C/float(fmC)
	bRatio = B/float(fmB)

	print "Bike Ratio = %.3f, Rack Ratio = %.3f" % (round(bRatio,3), round(cRatio,3))

	if bRatio < cRatio:
		print "Bike Ratio < Rack Ratio: can scale directly."
		fmScaled = scaleByBikesAndRacks(fm, B, C, bRatio, cRatio)

	else: 
		print "Bike Ratio > Rack Ratio: scale bikes and racks by rack ratio, then assign extra bikes."
		fmScaled = chooseThreshold(fm, B, C, cRatio)

	return fmScaled

if __name__ == '__main__':

	lb = 6
	ub = 10 # either 10 or 24
	mbm2x = eval(open('./Data/multipliedflowdictDec2.txt').read())
	sM15x = eval(open('./Data/CTMCVaryRate'+str(lb)+'-'+str(ub)+'_15x.txt').read())
	result = fullFluidModel(sM15x, mbm2x, lb, ub)

	cPickle.dump(result, open('./Results/fluidModelUB_'+str(lb)+'-'+str(ub)+'.p', 'wb'))

	resultCSV = {}
	for i in result.keys():
		resultCSV[i] = {}
		resultCSV[i]['name'] = result[i]['name']
		resultCSV[i]['ords'] = result[i]['ords']
		resultCSV[i]['initBikes'] = result[i]['initBikes']
		resultCSV[i]['initCapacity'] = result[i]['initCapacity']
		resultCSV[i]['bikes'] = result[i]['bikes']
		resultCSV[i]['capacity'] = result[i]['capacity']
		resultCSV[i]['minBikes'] = result[i]['minBikes']
		resultCSV[i]['minRacks'] = result[i]['minRacks']


	from csv import DictWriter
	with open('./Results/fluidModelUB_'+str(lb)+'-'+str(ub)+'.csv', 'wb') as f:
	    writer = DictWriter(f, ['key', 'name', 'ords', 'initBikes', 'initCapacity', 'bikes', 'capacity', 'minBikes', 'minRacks'])
	    writer.writerow(dict(zip(writer.fieldnames, writer.fieldnames))) # no automatic header :-(
	    for key,values in resultCSV.items():
	        writer.writerow(dict(key=key, **values)) # first make a new dict merging the key and the values

