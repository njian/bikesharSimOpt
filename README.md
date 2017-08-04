gitignore ignores pickle files due to the storage limit on github. Please ask nj227@cornell.edu for mbm data.
# Under Simulation folder
# Chapter 3 of thesis (pseudo-gradient search)
gradSearchCapsTableRecal, BikeSimCapsTable, SimulationRunnerCapsTable.py:
- pseudo-gradient search idea using gradient "table"
- recalculates pseudo-gradient after each match
- with local randomization
- most recent version, corresponding to Heuristic 9
## gradSearchCapsTableRandom.py
- with randomization but no recalculation
## gradSearchCapsTable.py
- without local randomization
# Chapter 2 of thesis (WSC paper [here](http://dl.acm.org/citation.cfm?id=3042182))
## gradSearch, BikeSim, SimulationRunner_v2.py:
- used for Heuristic 1 in the paper
- optimizing bikes only
- no consideration for the stations that are empty (full) in AM but full (empty) in PM
## gradSearchDecomp, BikeSimDecomp, SimulationRunnerDecomp.py:
- used for Heuristic 2 in the paper
- optimizing bikes only
- considers the stations with AM and PM symmetry
## gradSearchCaps, BikeSimCaps, SimulationRunnerCaps.py:
- used for Heuristic 3 in the paper
- optimizing both bikes and docks
- no consideration for the stations that are empty (full) in AM but full (empty) in PM
## gradSearchCapsDecomp, BikeSimCapsDecomp, SimulationRunnerCapsDecomp.py:
- used for Heuristic 4 in the paper
- optimizing both bikes and docks
- considers the stations with AM and PM symmetry
## SimulationRunnerCapsMbm.py, BikeSimMbm.py
- use this to record minute by minute bike levels
## test.py, test_gradSearchCapsTable.py
- unit tests
## makeCSV.py, objCount.py
- utility functions
## BikeSimCorrals.py
- with corrals (by Tom)
# Under data folder
- Some sample data
## CTMCVaryRate6-10_15x.txt, CTMCVaryRate6-24_15x.txt
- the varying rate CTMC solution calculated from 1.5X flow rates of Dec 2015 data, optimizing both bikes and docks from 6-10 am and entire day
## CTMCVaryRateBikesOnly6-10_15x.txt, CTMCVaryRateBikesOnly6-24_15x.txt
- only optimizing bikes
## check*.py
- utility files for testing purpose
## durationsLNMultiplier2.txt
- multipliers for the lognormal durations. See BikeSim for usage.
## AverageAllocationFromNames.txt
- equal allocation solution
# CoordsAndNames.txt
- station names and coordinates
# Under outputsDO folder
- *.qml: templates for QGIS graphs