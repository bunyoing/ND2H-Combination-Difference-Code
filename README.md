# ND2H-Combination-Difference-Code
A Python program to find the combination differences for the ND2H molecule.

Combination differences for doubly-deuterated ammonia (ND2H)
ORBYTS 2024 MARVEL project, in collaboration with UCL.
 
Every transition to the same upper state should predict the same upper-state
energy (lower-state energy + transition frequency). This script works out that
prediction for each transition, averages it per upper state, and flags any
transition that differs from the average by more than the threshold, so
problem lines in the MARVEL dataset can be checked by hand.
 
Input files (in the same folder as this script):
  22CaDiFuTa-EmpiricalLevels.txt  empirical energy levels (lower states)
  ND2H-MARVEL-MAIN.txt            MARVEL transitions file
  segments.txt                    units (MHz or cm-1) for each data source
