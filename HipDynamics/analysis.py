#!/usr/bin/python3

from scipy import stats
from HipDynamics.staging import *

# For experiment
#   For line
#       Select for [FN] or Well
#       Get 'CellsDoubleFinal2' fields *** Start from here ***
#
#       Sort according to hours
#       1. Heatmapping
#           1.1 Binning in 20 bins
#           1.2 Plot heatmap
#       2. Linear Regression
#           2.1 Transform onto log scale
#           2.2 Get median per hour
#           2.3 Fit linear regression
#           2.4 Get gradient and y-intercept
#           2.5 Plot
#   3. Output csv per experiment

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
        if self.pref["transformToLogScale"]:
            self.transformDataToLogScale()
        medianData = self.computeMedians()
        inputData = self.collapseIntoRegressionTable(medianData)
        self.resultData = self.applyLinearRegression(inputData)
        return self.resultData

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
                slope, intercept, rValue, pValue, stdErr = stats.linregress(x, y)
                result.append({
                    "slope": slope,
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
        analysis = Analysis(analysisPreferences)

        data = self.retrieveDataOfNextIndexGroup()
        analysis.data = data
        result = analysis.runDimensionalityReduction()


    def __str__(self):
        pass

