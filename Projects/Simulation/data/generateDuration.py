# import cPickle
import time
import numpy

# mbm = cPickle.load(open('mbm30min_v2.p','r'))
# duration = {}
# for t in mbm.keys():
#     for s1 in mbm[t].keys():
#         duration[s1] = {}
# for t in mbm.keys():
#     for s1 in mbm[t].keys():
#         for s2 in mbm[t][s1]['dests'].keys():
#             duration[s1][s2] = 1

# # check
# for t in mbm.keys():
#     for s1 in mbm[t].keys():
#         if not duration.has_key(s1):
#             print "error1"
#         for s2 in mbm[t][s1]['dests'].keys():
#             if not duration[s1].has_key(s2):
#                 print "error2", s1, s2

# cPickle.dump(duration, open('duration.p', 'wb'))

durations = eval(open('PairwiseCyclingDurations.txt').read())
intercept = 0.5769 
slope = 0.9116
sigma = 0.2389 # sqrt of 0.0570636366697
testDurList = range(4, 3743) # 3739 durations 

numpy.random.seed(1)
duration = []
t0 = time.time()
for testDur in testDurList:
	duration.append (round((testDur**slope)* \
                        numpy.exp(intercept)*numpy.random.lognormal(0,sigma)/60.0 ))
t1 = time.time()
print "T = D^beta1*exp(beta0+epsilon):  ", t1 - t0, numpy.mean(duration)

numpy.random.seed(1)
duration = []
t0 = time.time()
for testDur in testDurList:
	duration.append(numpy.exp(slope*numpy.log(testDur) + numpy.random.normal(0,sigma) + intercept)/60.0) 
t1 = time.time()
print "T = exp(beta1*ln(D) + beta0 + epsilon):  ", t1 - t0, numpy.mean(duration)

numpy.random.seed(1)
duration = []
t0 = time.time()
for testDur in testDurList:
	duration.append(numpy.random.poisson(testDur)/60.0)
t1 = time.time()
print "Poisson", t1 - t0, numpy.mean(duration)

numpy.random.seed(1)
duration = []
t0 = time.time()
for testDur in testDurList:
	duration.append(round((testDur**slope*numpy.exp(intercept)/60.0)*numpy.random.lognormal(0, sigma)))
t1 = time.time()
print "mult*lognormal", t1 - t0, numpy.mean(duration)

# numpy.random.seed(1)
# duration = []
# t0 = time.time()
# for testDur in testDurList:
# 	duration.append(numpy.random.normal(0, sigma)/60.0)
# t1 = time.time()
# print "Just normal", t1 - t0, numpy.mean(duration)

# numpy.random.seed(1)
# duration = []
# t0 = time.time()
# for testDur in testDurList:
# 	duration.append(numpy.exp(numpy.random.normal(0,sigma))/60.0) 
# t1 = time.time()
# print "normal exp", t1 - t0, numpy.mean(duration)

# numpy.random.seed(1)
# duration = []
# t0 = time.time()
# for testDur in testDurList:
# 	duration.append(numpy.random.lognormal(0,sigma)/60.0) 
# t1 = time.time()
# print "lognormal", t1 - t0, numpy.mean(duration)

