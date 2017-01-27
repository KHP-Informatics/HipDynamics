# -*- coding: utf-8 -*-
#!/usr/bin/python3
import csv
from HipDynamics.analysis import *
from HipDynamics.vis import QuickPlot

def startUpInfo():
    msg = "\n| | | (_)_ __ |  _ \ _   _ _ __   __ _ _ __ ___ (_) ___ ___\n"\
          "| |_| | | '_ \| | | | | | | '_ \ / _` | '_ ` _ \| |/ __/ __|\n"\
          "|  _  | | |_) | |_| | |_| | | | | (_| | | | | | | | (__\__ \ \n"\
          "|_| |_|_| .__/|____/ \__, |_| |_|\__,_|_| |_| |_|_|\___|___/\n"\
          "        |_|          |___/\n\n"\
          "Version: 1.0; Author: Maximilian Kerz (www.maximiliankerz.com)"
    print(msg)

def main():

    startUpInfo()
    path = ""
    if len(sys.argv) > 1:
        path = sys.argv[1]
    if path == "":
        path = input("Please enter path to preferences.json file: ")
    tbs = TableSetup(path)
    tbs.setup()
    table = tbs.table
    analysisPref = tbs.analysisPreferences
    analysisW = AnalysisWrapper(table)
    analysisW.runAnalysis(analysisPref)
    analysisW.writeOutputToCSV(analysisPref["outputPath"])

    data = analysisW.outputTable

    #Example of using HipDynamics.QuickPlot for visualisations
    #qp = QuickPlot(data)
    #qp.outputPath = '/'
    #qp.plot(indexBy='Line', labelWith='FN', withMeasure='gradient', show=False, saveFigure=True)


main()
