import cPickle

import cPickle

def getInflows(mbm):
	# Given an mbm outflow file, calculate inflows by aggregating destination flow rates
	inflow = {}

	for t in mbm.keys():
		inflow[t] = {}
		# In each interval, make a list of all stations that have inflow
		for startStation in mbm[t].keys():
			totalInflow = 0
			for destStation in mbm[t][startStation]["dests"].keys():
				destInflow = mbm[t][startStation]["dests"][destStation]
				if not inflow[t].has_key(destStation):
					# Create dictionary for this destination station
					inflow[t][destStation] = {}
					#Create sources dictionary, with a key for this start station
					inflow[t][destStation]["sources"] = {}
					inflow[t][destStation]["sources"][startStation] = destInflow
					# Create total inflow key that sums all inflows
					inflow[t][destStation]["totalInflow"] = destInflow

				else:
					inflow[t][destStation]["sources"][startStation] = destInflow
					inflow[t][destStation]["totalInflow"] += destInflow
	return inflow


def initFluidModel(sM, mbm):
	outflowRates = mbm
	inflowRates = getInflows(mbm)
	sidList = []
	stationFlows = {}

	# For each station, calculate full day flow
	for sid in sM:

		# Set up stationFlows dictionary, which will hold fluid model results
		sidList.append(sid)
		stationFlows[sid] = {}

		initLevel = sM[sid]["level"]
		stationFlows[sid]["initLevel"] = initLevel
		stationFlows[sid]["initCapacity"] = sM[sid]["capacity"]
		stationFlows[sid]["levelList"] = [initLevel]

		stationFlows[sid]["netFlows"] = []

		level = initLevel

		# Divide day into two intervals: 6am to midnight, followed by midnight to 6am
		# At each 30 minute interval, update the bike level based on the net flow
		for i in range(360,1440,30):
			outflow = 0
			inflow = 0
			if outflowRates[i].has_key(sid): 
				outflow = outflowRates[i][sid]["total"]
			if inflowRates[i].has_key(sid): 
				inflow = inflowRates[i][sid]["totalInflow"]
			netflow = inflow - outflow
			stationFlows[sid]["netFlows"].append(netflow)

			level = level + 30*netflow
			stationFlows[sid]["levelList"].append(level)

		for i in range(0,360,30):
			outflow = 0
			inflow = 0
			if outflowRates[i].has_key(sid): 
				outflow = outflowRates[i][sid]["total"]
			if inflowRates[i].has_key(sid): 
				inflow = inflowRates[i][sid]["totalInflow"]
			netflow = inflow - outflow
			stationFlows[sid]["netFlows"].append(netflow)

			level = level + 30*netflow
			stationFlows[sid]["levelList"].append(level)

		levelList = stationFlows[sid]["levelList"]

		# Calculate the minimum bikes and racks needed to meet the fluid model net flows with no failed starts/ends

		h = min(levelList)  # If positive, will reduce min bike level; if negative, will increase
		stationFlows[sid]["minBikes"] = initLevel - h
		stationFlows[sid]["minRacks"] = max(levelList) - h

	return stationFlows


def scaleByRacks(fm):
	''' GIVEN THE FLUID MODEL DICTIONARY, DO INITIAL SCALING. RETURN DICTIONARY THAT CONTAINS:
		minBikes, minRacks (calculated with fluid model)
		sBikes, sRacks (scaled by rack factor)
		availSpace = racks available in scaled solution
		diffBikes = difference between scaled bikes and fluid model desired bikes

		NOTE: use this when bike scale factor > rack scale factor '''

	C = sum(fm[i]['initCapacity'] for i in fm.keys()) #actual total racks
	B = sum(fm[i]['initLevel'] for i in fm.keys()) # actual total bikes
	fmC = sum(fm[i]['minRacks'] for i in fm.keys()) # racks assigned over all stations in fluidModel
	fmB = sum(fm[i]['minBikes'] for i in fm.keys()) # bikes assigned over all stations in fluidModel

	cRatio = C/float(fmC)
	bRatio = B/float(fmB)

	if bRatio < cRatio:
		print "Bike Ratio < Rack Ratio, can scale directly."
		## WRITE CODE TO DO THIS

	# initialize scaled FM dictionary: b = desired bikes, c = desired capacity

	availBikes = B
	availRacks = C

	# Scale all bikes and racks by these numbers
	for i in fm.keys():

		# Calculate scaled bikes/racks
		fm[i]['sBikes'] = round(cRatio*fm[i]['minBikes'])
		fm[i]['sRacks'] = round(cRatio*fm[i]['minRacks'])

		# Calculate number of empty racks in scaled model
		fm[i]['availSpace'] = fm[i]['sRacks'] - fm[i]['sBikes']

		#Calculate the difference between the scaled bikes and ideal fluid model bikes 
		fm[i]['diffBikes'] = round(fm[i]['minBikes']) - fm[i]['sBikes']
		availBikes -= fm[i]['sBikes']
		availRacks -= fm[i]['sRacks'] 

	# Adjust if necessary: assign extra racks after scaling - assign to highest capacity stations:
	if availRacks < 0:
		print "Warning: with rounding, scaled racks exceeds available racks."

	if availRacks > 0:
		print "Initial scaling resulted in excess of %d racks. Assigned to highest capacity stations" % availRacks
		toAdd = sorted(fm, key = lambda i: fm[i].get('sRacks'), reverse = True)
		index = 0
		while availRacks > 0:
			sid = toAdd[index]
			fm[sid]['sRacks'] += 1
			fm[sid]['availSpace'] += 1
			availRacks -= 1
			index += 1

	return fm


def assignBikes(current, threshold):
	# Add bikes to stations based on a threshold bike number. For any stations that have 'diffBikes' > threshold,
	# try to add the difference between them to that station. If this exceeds the number of empty racks, fill the station.
	totalAdded = 0
	totalSystem = 0

	for i in current.keys():
		if current[i]['diffBikes'] < threshold: 
			numAdd = 0
		else: 
			numAdd = min(current[i]['diffBikes']-threshold, current[i]['availSpace'])
		current[i]['numAdd'] = numAdd
		current[i]['totalBikes'] = current[i]['sBikes'] + numAdd
		totalAdded += numAdd
		totalSystem += current[i]['totalBikes']

	return totalSystem, current

def chooseThreshold(fluidModel):
	# Iterate through thresholds, starting at the max 'diffBikes', until all extra bikes have been assigned.
	current = scaleByRacks(fluidModel)
	totalBikes = sum(current[i]['initLevel'] for i in current.keys())

	t = max(current[i]["diffBikes"] for i in current.keys())
	while True:

		totalSystem, assignment = assignBikes(current, t)
		print "With threshold=%d: %d total bikes assigned, out of %d available." % (t, totalSystem, totalBikes)

		if totalSystem < totalBikes:
			t -= 1
		else:
			# If needed remove extra bikes to balance totalSystem = totalBikes. 
			# Take bikes from the stations with 'diffBikes'=t (i.e. the last stations to get extra bikes)
			extra = totalSystem - totalBikes
			for i in assignment.keys():
				if extra > 0 and assignment[i]['diffBikes']==t and assignment[i]['availSpace']>0 and extra > 0:
					assignment[i]['totalBikes'] -= 1
					totalSystem -= 1
					extra -= 1
				elif extra == 0: 
					print "Assignment Complete: %d bikes assigned. Exceed available bikes by %d" % (totalSystem, totalBikes - totalSystem)
					print "Final Threshold: %d bikes" % t
					return assignment

mbm = cPickle.load(open("./mbm30min_v2.p", 'r'))
sM = eval(open('NewOrds.txt').read())

fmStart = initFluidModel(sM, mbm)

chooseThreshold(fmStart)