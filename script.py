#!/usr/bin/python3

from HipDynamics.analysis import *

def main():

    path = "/Users/Kerz/Documents/projects/HIPSCI/HipDynamicsPy/phaseFocusPreferences.json"
    tbs = TableSetup(path)
    tbs.setup()
    table = tbs.table
    analysisPref = tbs.analysisPreferences

    analysisW = AnalysisWrapper(table)
    analysisW.runAnalysis(analysisPref)



main()

