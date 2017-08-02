gitignore ignores pickle files due to storage limit on github. Please ask nj227@cornell.edu for mbm data.
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
# Others
## BikeSimCorrals.py
- with corrals (by Tom)
## outputsDO
- ouput files for thesis and WSC paper
- template for QGIS maps