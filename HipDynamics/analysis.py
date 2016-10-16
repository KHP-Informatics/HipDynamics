#!/usr/bin/python3

import pymysql as pymysql
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

    def __init__(self):
        pass


class AnalysisWrapper:

    def __init__(self, lookUpTable):
        if type(LookUpTable()) == type(lookUpTable):
            self.table = lookUpTable
            self.dataSource = self.table.sourceFeatureAccessInfo
            self.columns = self.retrieveDataColumns()
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
            if self.dataSource["type"] == "MySQL":
                self.indexGroupData = self.retrieveDataOfNextIndexGroupeFromMysql()
            if self.dataSource["type"] == "CSV":
                self.indexGroupData = self.retrieveDataOfNextIndexGroupeFromCSV()

    def retrieveDataOfNextIndexGroupeFromMysql(self):
        idxs = self.table.nextIndexGroup()
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
        idxsConcat = ", ".join(str(idx) for idx in idxs)
        query = "select {} from {} where {} in ({});".format(columnsConcat,
                                                             sqlInfo["table"],
                                                             sqlInfo["Index"],
                                                             idxsConcat)
        return query

    def retrieveDataOfNextIndexGroupeFromCSV(self):
        idxs = self.table.nextIndexGroup()
        data = []
        for idxGroup in idxs:
            data.append(self.queryDataFromCSV(idxGroup))
        return data

    def queryDataFromCSV(self, idxGroup):
        csvInfo = self.dataSource["CSV"]
        resultTable = LookUpTable()
        resultTable.mapping = LookUpTable.generateLookUpTableMapFromList(0, self.columns)
        for idx in idxGroup:
            resultList = self.arrangeResultsinColumnOrder(self.dataInMemory[idx])
            resultTable.add(resultList)
        return resultTable.table

    def arrangeResultsinColumnOrder(self, dictionary):
        resultList = []
        for col in self.columns:
            resultList.append(dictionary[col])
        return resultList

