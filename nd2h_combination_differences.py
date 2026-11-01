"""
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
"""

import pandas as pd

EMPIRICAL_LEVELS = "22CaDiFuTa-EmpiricalLevels.txt"
TRANSITIONS_FILE = "ND2H-MARVEL-MAIN.txt"
SEGMENTS_FILE = "segments.txt"
THRESHOLD = 0.03                      # cm-1
MHZ_TO_WAVENUMBER = 1e6 / 29979245800  # multiply MHz by this to get cm-1


def readFile(filename, columnNames=None):
    if columnNames is None:
        return pd.read_csv(filename, sep=r"\s+")
    return pd.read_csv(filename, sep=r"\s+", names=columnNames)


def writeToFile(dataFrame, fileName):
    with open(fileName, "w+") as fileToWriteTo:
        fileToWriteTo.write(dataFrame.to_string(index=False))


def applyFunction(function, dataFrame):
    """Apply a function to every row of a DataFrame."""
    return dataFrame.apply(lambda x: function(x), result_type="expand", axis=1)


def groupApplyFunction(function, groupByColumn, dataFrame):
    """Apply a function to each group of a DataFrame grouped by one column."""
    # Selecting all columns explicitly keeps the grouping column in each group
    # (newer pandas versions drop it otherwise).
    groupedDataFrame = dataFrame.groupby(groupByColumn, group_keys=False)[list(dataFrame.columns)]
    return groupedDataFrame.apply(lambda x: function(x))


# --- Empirical (lower-state) energy levels, tagged by their quantum numbers ---
empiricalEnergies = readFile(EMPIRICAL_LEVELS)
empiricalEnergies["Tag\""] = (empiricalEnergies["nu1"].astype(str) + "-" + empiricalEnergies["nu2"].astype(str)
                              + "-" + empiricalEnergies["nu3a"].astype(str) + "-" + empiricalEnergies["nu3b"].astype(str)
                              + "-" + empiricalEnergies["nu4a"].astype(str) + "-" + empiricalEnergies["nu4b"].astype(str)
                              + "-" + empiricalEnergies["J"].astype(str) + "-" + empiricalEnergies["Ka"].astype(str)
                              + "-" + empiricalEnergies["Kc"].astype(str) + "-" + empiricalEnergies["inv"])

# --- MARVEL transitions ---
marvelColumns = ["nu", "unc1", "unc2", "nu1'", "nu2'", "nu3a'", "nu3b'", "nu4a'", "nu4b'", "J'", "Ka'", "Kc'", "inv'",
                 "nu1\"", "nu2\"", "nu3a\"", "nu3b\"", "nu4a\"", "nu4b\"", "J\"", "Ka\"", "Kc\"", "inv\"", "Source"]
transitions = readFile(TRANSITIONS_FILE, marvelColumns)

# --- Convert MHz sources to wavenumbers (cm-1) using the segments file ---
segments = readFile(SEGMENTS_FILE, ["Segment", "Units"])


def trimSegment(row):
    row["Segment"] = row["Source"].split(".")[0]
    return row


transitions = applyFunction(trimSegment, transitions)
transitions = transitions.merge(segments, on="Segment")
transitions = transitions.drop("Segment", axis=1)


def convertToWavenumber(row):
    if row["Units"] == "MHz":
        row["nu"] = row["nu"] * MHZ_TO_WAVENUMBER
        row["unc1"] = row["unc1"] * MHZ_TO_WAVENUMBER
        row["unc2"] = row["unc2"] * MHZ_TO_WAVENUMBER
    return row


transitions = applyFunction(convertToWavenumber, transitions)


# --- Tag upper (') and lower (") states of each transition ---
def generateTags(row):
    row["Tag'"] = (str(row["nu1'"]) + "-" + str(row["nu2'"]) + "-" + str(row["nu3a'"])
                   + "-" + str(row["nu3b'"]) + "-" + str(row["nu4a'"]) + "-" + str(row["nu4b'"])
                   + "-" + str(row["J'"]) + "-" + str(row["Ka'"]) + "-" + str(row["Kc'"])
                   + "-" + str(row["inv'"]))
    row["Tag\""] = (str(row["nu1\""]) + "-" + str(row["nu2\""]) + "-" + str(row["nu3a\""])
                    + "-" + str(row["nu3b\""]) + "-" + str(row["nu4a\""]) + "-" + str(row["nu4b\""])
                    + "-" + str(row["J\""]) + "-" + str(row["Ka\""]) + "-" + str(row["Kc\""])
                    + "-" + str(row["inv\""]))
    return row


transitions = applyFunction(generateTags, transitions)

# --- Lower-state energy E" from the empirical levels; predicted upper-state energy E' ---
transitions = transitions.merge(empiricalEnergies[["Tag\"", "E/CM-1"]])
transitions["E\""] = transitions["E/CM-1"]
transitions = transitions.drop("E/CM-1", axis=1)
transitions["E'"] = transitions["nu"] + transitions["E\""]


# --- Combination differences: flag transitions that disagree with their upper state's average ---
def applyCombinationDifferences(dataFrame):
    dataFrame["Eavg'"] = dataFrame["E'"].mean()
    dataFrame["Problem"] = abs(dataFrame["Eavg'"] - dataFrame["E'"]) > THRESHOLD
    dataFrame["Return"] = dataFrame["Problem"].any()
    return dataFrame


transitions = groupApplyFunction(applyCombinationDifferences, "Tag'", transitions)

problematicTransitions = transitions[transitions["Return"]]
print(problematicTransitions[["Source", "Tag'", "Tag\"", "E'", "nu", "unc1", "Eavg'", "Problem", "E\""]].to_string())
