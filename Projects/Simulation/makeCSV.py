import csv
import cPickle

def singleOutput(name):
    statMapFile = "./data/AverageAllocationFromNames.txt"
    sM = eval(open(statMapFile).read())
    level = cPickle.load(open("./outputsDO/" + name + "Level.p", 'r'))
    capacity = cPickle.load(open("./outputsDO/" + name + "Capacity.p", 'r'))

    fieldnames = ["sid", "longitude", "latitude", "name", "capacity", "level", "fillLevel"]
    with open(str("./outputsDO/" + name + "StatMap.csv"),'wb') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for i in sM.keys():
            # Directory from sM
            # filewriter.writerow((i, sM[i]['ords'][0], sM[i]['ords'][1], sM[i]['name'], sM[i]['capacity'], sM[i]['level']))
            # From solution
            if capacity[i] != 0:
                filewriter.writerow((i, sM[i]['ords'][1], sM[i]['ords'][0], sM[i]['name'], capacity[i], level[i], level[i]/float(capacity[i])))
            else:
                filewriter.writerow((i, sM[i]['ords'][1], sM[i]['ords'][0], sM[i]['name'], capacity[i], level[i], -1))


def startingSoln(name):
    statMapFile = "./data/" + name + ".p"
    sM = cPickle.load(open(statMapFile, 'r'))

    fieldnames = ["sid", "longitude", "latitude", "name", "capacity", "level"]
    with open(str("./data/" + name + "StatMap.csv"),'wb') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for i in sM.keys():
            filewriter.writerow((i, sM[i]['ords'][1], sM[i]['ords'][0], sM[i]['name'], sM[i]['capacity'], sM[i]['bikes']))


def compareOutputsToCTMC(name):
    statMapFile = "./data/AverageAllocationFromNames.txt"
    sM = eval(open(statMapFile).read())
    level = cPickle.load(open("./outputsDO/" + name + "Level.p", 'r'))
    capacity = cPickle.load(open("./outputsDO/" + name + "Capacity.p", 'r'))
    ctmc = eval(open('./data/CTMCVaryRate6-10_15x.txt').read())

    fieldnames = ["sid", "longitude", "latitude", "name", "capacity_soln", "level_soln", "fillLevel_soln", "capacity_ctmc", "level_ctmc", "fillLevel_ctmc"]
    with open(str("./outputsDO/" + name + "StatMap.csv"),'wb') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for i in sM.keys():
            # Directory from sM
            # filewriter.writerow((i, sM[i]['ords'][0], sM[i]['ords'][1], sM[i]['name'], sM[i]['capacity'], sM[i]['level']))
            # From solution
            if capacity[i] != 0:
                filewriter.writerow((i, sM[i]['ords'][1], sM[i]['ords'][0], sM[i]['name'], capacity[i], level[i], level[i]/float(capacity[i]), ctmc[i]['capacity'], ctmc[i]['bikes'], ctmc[i]['bikes'] / float(ctmc[i]['capacity'])))
            else:
                filewriter.writerow((i, sM[i]['ords'][1], sM[i]['ords'][0], sM[i]['name'], capacity[i], level[i], -1, ctmc[i]['capacity'], ctmc[i]['bikes'], ctmc[i]['bikes'] / float(ctmc[i]['capacity'])))


def compareOutputs(name1, name2):
    statMapFile = "./data/AverageAllocationFromNames.txt"
    sM = eval(open(statMapFile).read())
    level1 = cPickle.load(open("./outputsDO/" + name1 + "Level.p", 'r'))
    capacity1 = cPickle.load(open("./outputsDO/" + name1 + "Capacity.p", 'r'))
    level2 = cPickle.load(open("./outputsDO/" + name2 + "Level.p", 'r'))
    capacity2 = cPickle.load(open("./outputsDO/" + name2 + "Capacity.p", 'r'))
    # ctmc = eval(open('./data/CTMCVaryRate6-10_15x.txt').read())

    fieldnames = ["sid", "longitude", "latitude", "name", "capacity_soln1", "level_soln1", "capacity_soln2", "level_soln2"]
    with open(str("./outputsDO/" + name1 + "_" + name2 + "StatMap.csv"),'wb') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for i in sM.keys():
            # Directory from sM
            # filewriter.writerow((i, sM[i]['ords'][0], sM[i]['ords'][1], sM[i]['name'], sM[i]['capacity'], sM[i]['level']))
            # From solution
            filewriter.writerow((i, sM[i]['ords'][1], sM[i]['ords'][0], sM[i]['name'], capacity1[i], level1[i], capacity2[i], level2[i]))
            

def makeStartingSolns():
    statMapFile = "./data/AverageAllocationFromNames.txt"
    avg = eval(open(statMapFile).read())
    ctmc = eval(open('./data/CTMCVaryRate6-10_15x.txt').read())

    fieldnames = ["sid", "latitude", "longitude", "name", "capacity_avg", "level_avg", "capacity_ctmc", "level_ctmc"]
    with open(str("./outputsDO/tablePlots/StatMap.csv"),'wb') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for i in avg.keys():
            filewriter.writerow((i, avg[i]['ords'][1], avg[i]['ords'][0], avg[i]['name'], avg[i]['capacity'], avg[i]['bikes'], ctmc[i]['capacity'], ctmc[i]['bikes']))
       

def makeAlterEnds(name1, name2, metric="AlterEnds"):
    statMapFile = "./data/AverageAllocationFromNames.txt"
    sM = eval(open(statMapFile).read())
    soln1 = cPickle.load(open("./outputsDO/" + name1 + metric + ".p", 'r'))
    soln2 = cPickle.load(open("./outputsDO/" + name2 + metric + ".p", 'r'))
    # ctmc = eval(open('./data/CTMCVaryRate6-10_15x.txt').read())

    fieldnames = ["sid", "longitude", "latitude", "name", (metric + "1"), (metric + "2")]
    with open(str("./outputsDO/" + name1 + "_" + name2 + metric + ".csv"),'wb') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for i in sM.keys():
            filewriter.writerow((i, sM[i]['ords'][1], sM[i]['ords'][0], sM[i]['name'], soln1[i], soln2[i]))
 

def makeObjCounts(name):
    statMapFile = "./data/AverageAllocationFromNames.txt"
    sM = eval(open(statMapFile).read())
    fs = cPickle.load(open("./outputsDO/" + name + "FailedStarts" + ".p", 'r'))
    ae = cPickle.load(open("./outputsDO/" + name + "AlterEnds" + ".p", 'r'))
    # ctmc = eval(open('./data/CTMCVaryRate6-10_15x.txt').read())

    fieldnames = ["sid", "longitude", "latitude", "name", "failedStarts", "alterEnds"]
    with open(str("./outputsDO/" + name + "ObjCounts" + ".csv"),'wb') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        filewriter = csv.writer(csvfile, delimiter=',', quotechar='|', quoting=csv.QUOTE_MINIMAL)
        for i in sM.keys():
            filewriter.writerow((i, sM[i]['ords'][1], sM[i]['ords'][0], sM[i]['name'], fs[i] if fs.has_key(i) else 0, ae[i] if ae.has_key(i) else 0))

if __name__ == '__main__':
    # Make csv of a single output
    # filename1 = "CTMCVaryRate6to24_15xid12id60CapsTableRnCaps"
    # filename2 = "CTMCVaryRate6to24_15xid12id62CapsTableRnCaps"
    # filename = "FluidModelid32cheatingCaps"
    # singleOutput(filename)
    # makeAlterEnds(filename1, filename2, "failedStarts")
    # Make csv of two outputs for comparison
    # compareOutputs(filename1, filename2)
    # compareOutputsToCTMC(filename)

    # fileName = "CTMCVaryRate6to24_15xid12id62CapsTableRnCaps"
    # makeObjCounts(fileName)
    # makeStartingSolns()

    solutionName = "fluidModelUB_Dec15x"
    startingSoln(solutionName)

