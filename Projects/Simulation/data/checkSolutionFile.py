import pickle

avg = eval(open('AverageAllocationFromNames.txt').read())

extraBike = 0
for sid in avg.keys():
    if avg[sid]['capacity'] > 60:
    	avg[sid]['capacity'] = 60
    	if avg[sid]['bikes'] > avg[sid]['capacity']:
    		extraBike += avg[sid]['bikes'] - avg[sid]['capacity']

    if avg[sid]['capacity'] < 16:
    	avg[sid]['capacity'] = 16

while extraBike > 0:
	for sid in avg.keys():
		if avg[sid]['capacity'] > avg[sid]['bikes']:
			avg[sid]['bikes'] += 1
			extraBike -= 1

# Check again
badSolution = 0
for sid in avg.keys():
	if avg[sid]['capacity'] >= 16 and avg[sid]['capacity'] <= 60 and avg[sid]['capacity'] >= avg[sid]['bikes'] and avg[sid]['bikes'] >= 0:
		continue
	else:
		badSolution = 1

if badSolution == 1:
	print "Problem with sid = ", sid, "info: cap, bikes = ", avg[sid]['capacity'], avg[sid]['bikes']
else:
	with open('AverageAllocationFromNamesConstrained.p', 'wb') as out_file:
		pickle.dump(avg, out_file)
		out_file.close()
	print "Everything looks good! File dumped."