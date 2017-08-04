import cPickle
import matplotlib.pyplot as plt
import operator

ctmc = cPickle.load(open("./outputs/equalNRS55.p", 'r'))
avg = cPickle.load(open("./outputs/equalNRS96.p", 'r'))



sortedctmc = sorted(ctmc.items(), key=operator.itemgetter(0))
ctmc_x = [ sortedctmc[i][0] for i in xrange(len(sortedctmc)) ]
ctmc_y = [ sortedctmc[i][1] for i in xrange(len(sortedctmc)) ]
sortedavg = sorted(avg.items(), key=operator.itemgetter(0))
avg_x = [ sortedavg[i][0] for i in xrange(len(sortedavg)) ]
avg_y = [ sortedavg[i][1] for i in xrange(len(sortedavg)) ]

# print "ctmc solutions:", ctmc_y
for i in range(len(avg_x)):
    print avg_x[i] , " ; " ,  avg_y[i]
# print "equal allocation solutions:", avg_x, avg_y

# # plt.locator_params(axis = 'y', nbins = 10)
# plt.clf()
# plt.figure()
# plt.plot(ctmc_x, ctmc_y, color='b', label = 'from CTMC solution')
# plt.plot(avg_x, avg_y, color='r', label = 'from equal allocation')
# plt.legend()
# plt.xlim(0,1000000)
# ax = plt.gca()
# ax.set_autoscale_on(False)
# ax.set_ylim([80,400])
# # plt.text(0, 520, 'CTMC solution')
# plt.title("Comparison of Selective Search from Different Starts")
# plt.xlabel("Number of Simulation Days")
# plt.ylabel("Objective values")
# plt.savefig("./outputs/comparisons.png")
# plt.show


# ctmcAllo = cPickle.load(open("./outputs/equalNRSAlloc55.p", 'r'))
# avgAllo = cPickle.load(open("./outputs/equalNRSAlloc96.p", 'r'))

# sortedctmcAllo = sorted(ctmcAllo.items(), key=operator.itemgetter(0))
# # ctmcAllo_x = [ sortedctmcAllo[i][0] for i in xrange(len(sortedctmcAllo)) ]
# ctmcAllo_y = [ sortedctmcAllo[i][1] for i in xrange(len(sortedctmcAllo)) ]
# sortedavgAllo = sorted(avgAllo.items(), key=operator.itemgetter(0))
# # avgAllo_x = [ sortedavgAllo[i][0] for i in xrange(len(sortedavgAllo)) ]
# avgAllo_y = [ sortedavgAllo[i][1] for i in xrange(len(sortedavgAllo)) ]

# plt.clf()
# plt.figure()
# plt.scatter(avgAllo_y, ctmcAllo_y, color='b', label = 'from CTMC solution')
# plt.grid()
# plt.plot([0, 70], [0, 70], 'r',  lw=2)
# plt.xlim(0,70)
# ax = plt.gca()
# ax.set_autoscale_on(False)
# ax.set_ylim([0,70])
# # plt.text(0, 520, 'CTMC solution')
# plt.title("Comparison of the Solution of Selective Search from Different Starts")
# plt.xlabel("Average Allocation")
# plt.ylabel("CTMC")
# plt.savefig("./outputs/comparisons2.png")
# plt.show