#!/usr/bin/python3

from HipDynamics.analysis import *

def main():

    path = "/Users/Kerz/Documents/projects/HIPSCI/HipDynamicsPy/phaseFocusPreferences.json"
    tbs = TableSetup(path)
    tbs.setup()
    table = tbs.table
    index = table.index

    #for i in range(24):
    #    idxGroup = table.nextIndexGroup()
    #    meta = table.metadataOfRetrievedIndexGroup
    #    print(str(meta) + ": " + str(idxGroup))

    analysisW = AnalysisWrapper(table)
    analysisW.retrieveDataOfNextIndexGroup()
    data = analysisW.indexGroupData
    print(len(data))
    for d in data:
        print(str(d))

main()

