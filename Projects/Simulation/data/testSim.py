import SimulationRunner1
import numpy.random
import random

sM = eval(open('OldOrds.txt').read())
print ('Finished loading station map.')
mbm = {}
for i in range(24):
    mbm.update(eval(open('./mbmData/minbymin' + str(i) + '.txt').read()))
# mbm.update(eval(open('./mbmData/minbymin' + str(5) + '.txt').read()))
print ('Finished loading flow rates.')

level = {}
# Read solution
for sid in sM:
    level[sid] = sM[sid]['level']

numpy.random.seed(9)
random.seed(9)
data1 = SimulationRunner1.runDay(mbm, SimulationRunner1.statMapTestSol(level), 7.0*60, 8.0*60)
random.seed(9)
numpy.random.seed(9)
data2 = SimulationRunner1.runDay(mbm, SimulationRunner1.statMapTestSol(level), 8.0*60, 9.0*60)
random.seed(9)
numpy.random.seed(9)
data3 = SimulationRunner1.runDay(mbm, SimulationRunner1.statMapTestSol(level), 7.0*60, 9.0*60)
print data1[0:3], data1[5]
print data2[0:3], data2[5]
print data3[0:3], data3[5]