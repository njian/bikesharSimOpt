import cPickle

with open('realBikes7_20161115.txt', 'r') as f:
	data = eval(f.read())

sM = {}
for item in data['stationBeanList']:
	sid = item['id']
	sM[sid] = {}
	sM[sid]['name'] = item['stationName']
	sM[sid]['ords'] = [item['longitude'], item['latitude']]
	sM[sid]['bikes'] = item['availableBikes']
	sM[sid]['capacity'] = item['totalDocks']

cPickle.dump(sM, open('realBikes7_20161115.p', 'wb'))

import csv
fieldnames = ["sid", "name", "longitude", "latitude", "bikes", "capacity"]
with open('./fluidModel/realBikes7_20161115.csv', 'wb') as csvfile:
	writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
	writer.writeheader()
	filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
	for sid in sM.keys():
		filewriter.writerow((sid, sM[sid]['name'], sM[sid]['ords'][0], sM[sid]['ords'][1], sM[sid]['bikes'], sM[sid]['capacity']))

