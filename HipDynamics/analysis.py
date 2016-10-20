# -*- coding: utf-8 -*-
#!/usr/bin/python3

import datetime
from scipy import stats
from HipDynamics.staging import *

class Analysis:

    def __init__(self, pref):
        self.pref = pref
        self.data = []

    @property
    def pref(self):
        return self.__pref

    @pref.setter
    def pref(self, input):
        if input["transformToLogScale"]:
            print("[WARN] In order to perform a log transformation, all negative\n" \
                  "       values will be inverted and 0 values set to 1e-10.")
        self.__pref = input

    @property
    def data(self):
        return self.__data

    @data.setter
    def data(self, input):
        self.__data = input

    @property
    def result(self):
        return self.__resultData

    def runDimensionalityReduction(self):
        if len(self.data) < 2:
            print("[WARN] dimensionalityReduction aborted. One or no data point submitted.\n"\
                  "       It cannot be collapsed further.")
            return []
        self.setMissingValuesToZero()
        if self.pref["transformToLogScale"]:
            self.transformDataToLogScale()
        medianData = self.computeMedians()
        inputData = self.collapseIntoRegressionTable(medianData)
        self.resultData = self.applyLinearRegression(inputData)
        return self.resultData

    def setMissingValuesToZero(self):
        for i in range(len(self.data)):
            keys = list(self.data[i].keys())
            for key in keys:
                vals = self.data[i][key]
                for j in range(len(vals)):
                    if vals[j] == "": vals[j] = 0
                self.data[i][key] = vals

    def transformDataToLogScale(self):
        for i in range(len(self.data)):
            keys = list(self.data[i].keys())
            for key in keys:
                vals = numpy.array(self.data[i][key]).astype(float)
                vals = [abs(val) for val in vals]
                for j in range(len(vals)):
                    if vals[j] == 0: vals[j] = 1e-10
                self.data[i][key] = numpy.log(vals).tolist()

    def computeMedians(self):
        medianData = self.data.copy()
        for i in range(len(medianData)):
            keys = list(medianData[i].keys())
            for key in keys:
                vals = numpy.array(medianData[i][key]).astype(float)
                medianData[i][key] = [numpy.median(vals).tolist()]
        return medianData

    def collapseIntoRegressionTable(self, data):
        keys = list(data[0].keys())
        collapsedTable = LookUpTable()
        collapsedTable.mapping = LookUpTable.generateLookUpTableMapFromList(0, keys)
        for table in data:
            dim = []
            for key in keys:
                dim.append(table[key][0])
            collapsedTable.add(dim)
        return collapsedTable.table

    def applyLinearRegression(self, regressData):
        keys = list(regressData.keys())
        resultTable = LookUpTable()
        resultTable.mapping = LookUpTable.generateLookUpTableMapFromList(0, keys)
        result = []
        for key in keys:
            y = regressData[key]
            x = range(len(y))
            if len(x) > 1:
                gradient, intercept, rValue, pValue, stdErr = stats.linregress(x, y)
                result.append({
                    "gradient": gradient,
                    "intercept": intercept,
                    "rValue": rValue,
                    "pValue": pValue,
                    "stdErr": stdErr
                })
            else:
                print("[WARN] The input vector for linear regression has less than 2 values. Make sure\n"\
                      "       you selected the appropriate indexIteratorSelector. For more information\n"\
                      "       consult the documentation.")
        resultTable.add(result)
        return resultTable.table




class AnalysisWrapper:

    def __init__(self, lookUpTable):
        if type(LookUpTable()) == type(lookUpTable):
            self.table = lookUpTable
            self.dataSource = self.table.sourceFeatureAccessInfo
            self.columns = self.retrieveDataColumns()
            self.indexGroupData = []
            self.outputResultHeader = []
            self.outputTable = []
        else:
            print("[ERROR] AnalysisWrapper only accepts tables of type {}".format(str(type(LookUpTable()))))

    def retrieveDataColumns(self):
        if self.dataSource != None and self.table.sourceFeaturePatternSelector != None:
            if self.dataSource["type"] == "MySQL":
                return self.querySelectiveColumnsFromMysql()
            if self.dataSource["type"] == "CSV":
                return self.querySelectiveColumnsFromCSV()
        else:
            print("[ERROR] AnalysisWrapper requires a table sourceFeatureAccessInfo.\n" \
                  "        For more information, consult the documentation.")
            sys.exit()

    def querySelectiveColumnsFromMysql(self):
        sqlInfo = self.dataSource["MySQL"]
        query = self.createSelectiveColumnQueryForMySQL(sqlInfo, self.table.sourceFeaturePatternSelector)
        db = pymysql.connect(sqlInfo["address"], sqlInfo["user"], sqlInfo["pwd"], sqlInfo["db"])
        cursor = db.cursor()
        try:
            cursor.execute(query)
        except:
            print("[Error]: unable to fetch data from MySQL.")
        else:
            results = list(cursor.fetchall())
            singleDresults = []
            for result in results:
                singleDresults.append(result[0])
            return singleDresults
        db.close()

    def createSelectiveColumnQueryForMySQL(self, sqlInfo, whereSelector = None):
        query = "select column_name from information_schema.columns where"\
                " table_name='{}' and column_name like '%{}%';".format(sqlInfo["table"],
                                                                        whereSelector)
        return query

    def querySelectiveColumnsFromCSV(self):
        csvInfo = self.dataSource["CSV"]
        path = csvInfo["path"] + "/" + csvInfo["fileName"]
        with codecs.open(path, "r", encoding='utf-8', errors='ignore') as inputFile:
            for i in range(csvInfo["rowOffset"]):
                next(inputFile)
            data = csv.DictReader(inputFile, delimiter=csvInfo["delimiter"])
            self.dataInMemory = []
            for result in data:
                self.dataInMemory.append(result)
            inputFile.close()
        return list(self.dataInMemory[0].keys())

    def retrieveDataOfNextIndexGroup(self):
        idxs = self.table.nextIndexGroup()
        if len(idxs) == 0:
            return []
        if self.dataSource["type"] == "MySQL":
            self.indexGroupData = self.retrieveDataOfNextIndexGroupeFromMysql(idxs)
        if self.dataSource["type"] == "CSV":
            self.indexGroupData = self.retrieveDataOfNextIndexGroupeFromCSV(idxs)
        print(self.formatMetadata(self.table.metadataOfRetrievedIndexGroup, len(self.indexGroupData)))
        return self.indexGroupData


    def retrieveDataOfNextIndexGroupeFromMysql(self, idxs):
        data = []
        for idxGroup in idxs:
            data.append(self.queryDataFromMysql(idxGroup))
        return data

    def queryDataFromMysql(self, idxs):
        sqlInfo = self.dataSource["MySQL"]
        query = self.createDataQueryForMySQL(sqlInfo, idxs, self.columns)
        db = pymysql.connect(sqlInfo["address"], sqlInfo["user"], sqlInfo["pwd"], sqlInfo["db"])
        cursor = db.cursor()
        try:
            cursor.execute(query)
        except:
            print("[Error]: unable to fetch data from MySQL.")
        else:
            results = list(cursor.fetchall())
            resultsTable = LookUpTable()
            resultsTable.mapping = LookUpTable.generateLookUpTableMapFromList(0, self.columns)
            for i in range(len(results)):
                resultsTable.add(results[i])
            return resultsTable.table
        db.close()

    def createDataQueryForMySQL(self, sqlInfo, idxs, columns):
        columnsConcat = ", ".join(columns)
        if type(idxs) is list:
            idxsConcat = ", ".join(str(idx) for idx in idxs)
        else:
            idxsConcat = str(idxs)
        query = "select {} from {} where {} in ({});".format(columnsConcat,
                                                             sqlInfo["table"],
                                                             sqlInfo["Index"],
                                                             idxsConcat)
        return query

    def retrieveDataOfNextIndexGroupeFromCSV(self, idxs):
        data = []
        for idxGroup in idxs:
            data.append(self.queryDataFromCSV(idxGroup))
        return data

    def queryDataFromCSV(self, idxGroup):
        csvInfo = self.dataSource["CSV"]
        resultTable = LookUpTable()
        resultTable.mapping = LookUpTable.generateLookUpTableMapFromList(0, self.columns)
        if type(idxGroup) is list:
            for idx in idxGroup:
                resultList = self.arrangeResultsInColumnOrder(self.dataInMemory[idx])
                resultTable.add(resultList)
        else:
            resultList = self.arrangeResultsInColumnOrder(self.dataInMemory[idxGroup])
            resultTable.add(resultList)
        return resultTable.table

    def arrangeResultsInColumnOrder(self, dictionary):
        resultList = []
        for col in self.columns:
            resultList.append(dictionary[col])
        return resultList

    def formatMetadata(self, meta, noOfDataPoints = None):
        msg = "[√] "
        for m in meta:
            keys = list(m.keys())
            value = m[keys[0]]
            msg += "{}: {} -> ".format(keys[0], value)
        msg += "n = {}".format(str(noOfDataPoints))
        return msg

    def runAnalysis(self, analysisPreferences):
        print("\nHipDynamics Analysis\n====================\n")
        analysis = Analysis(analysisPreferences)
        result = self.nextAnalysisRun(analysis)
        while result != None:
            if result != []:
                row = self.formatOutputRow(result, analysisPreferences["regressionMeasures"])
                self.addRowToOutputTable(row, analysisPreferences["regressionMeasures"])
            result = self.nextAnalysisRun(analysis)
        print("\n*** ANALYSIS SUCCESSFUL ***\n")

    def nextAnalysisRun(self, analysis):
        data = self.retrieveDataOfNextIndexGroup()
        if len(data) == 0: return None
        analysis.data = data
        result = analysis.runDimensionalityReduction()
        return result

    def formatOutputRow(self, result, measures):
        if len(self.outputResultHeader) == 0:
            self.outputResultHeader = list(result.keys())
        metaVal = self.formatMetadataOutputRow()
        resultVal = self.formatResultOutputRow(result, measures)
        return metaVal + resultVal

    def formatMetadataOutputRow(self):
        row = []
        for d in self.table.metadataOfRetrievedIndexGroup:
            keys = list(d.keys())
            row.append(d[keys[0]])
        return row

    def formatResultOutputRow(self, result, measures):
        row = []
        for measure in measures:
            for key in self.outputResultHeader:
                row.append(result[key][0][measure])
        return row

    def addRowToOutputTable(self, row, measures):
        if len(self.outputTable) == 0:
            header = self.getHeader(measures)
            self.outputTable.append(header)
        self.outputTable.append(row)

    def getHeader(self, measures):
        meta = self.getMetadataHeader()
        result = self.getResultHeader(measures)
        return meta + result

    def getMetadataHeader(self):
        header = []
        for d in self.table.metadataOfRetrievedIndexGroup:
            keys = list(d.keys())
            header.append("{}-{}".format("index", keys[0]))
        return header

    def getResultHeader(self, measures):
        row = []
        for measure in measures:
            for key in self.outputResultHeader:
                row.append("{}-{}".format(measure, key))
        return row

    def writeOutputToCSV(self, outputPath):
        path = "{}/HipDynamics_{}.csv".format(outputPath, datetime.datetime.now().strftime('%d-%m-%Y_%H-%M'))
        with open(path, 'w', newline='') as csvfile:
            outputWriter = csv.writer(csvfile, delimiter=',')
            for row in self.outputTable:
                outputWriter.writerow(row)

    def __str__(self):
        pass

