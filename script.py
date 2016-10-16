#!/usr/bin/python3

from HipDynamics.analysis import *

def main():

    path = "/Users/Kerz/Documents/projects/HIPSCI/HipDynamicsPy/hipsciPreferences.json"
    tbs = TableSetup(path)
    tbs.setup()
    table = tbs.table
    index = table.index

    #analysisW = AnalysisWrapper(table)
    #analysisW.retrieveDataOfNextIndexGroup()

main()

