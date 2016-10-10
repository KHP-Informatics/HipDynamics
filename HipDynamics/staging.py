#!/usr/bin/python3

import sys
import csv
import json
import numpy
import codecs
import pymysql as pymysql

class LookUpTable:
    def __init__(self):
        self.table = {}
        self.mapping = []
        self.mappingInputN = 0
        self.invalidCharacters =[]
        self.TIMEKEY = "TIME_DIMENSION"
        self.timeDimensionKey = ""
        self.indexGroupIteratorIdx = 0

    @property
    def invalidCharacters(self):
        return self.__invalidCharacters

    @invalidCharacters.setter
    def invalidCharacters(self, input):
        self.__invalidCharacters = input

    @property
    def table(self):
        return self.__table

    @table.setter
    def table(self, inputTable):
        self.__table = inputTable

    @property
    def indexHierarchy(self):
        return self.__indexHierarchy

    @indexHierarchy.setter
    def indexHierarchy(self, input):
        if len(input) != 0:
            keys = list(self.table.keys())
            for indexKey in input:
                if not TableSetup.checkForKey(0, keys, indexKey):
                    print("[ERROR] The index key \'{}\' was not found in this table.\n" \
                          "        Please double check your index hierarchy.".format(indexKey))
                    sys.exit()
            for i in range(len(input)):
                if input[i] == self.timeDimensionKey and self.timeDimensionKey != "":
                    input[i] = self.TIMEKEY
        self.__indexHierarchy = input

    @property
    def mapping(self):
        return self.__mapping

    @mapping.setter
    def mapping(self, mapInstructions):
        self.__mapping = mapInstructions
        self.mappingInputN = len(mapInstructions)
        self.mapTable()

    @property
    def timeDimensionKey(self):
        return self.__timeDimensionKey

    @timeDimensionKey.setter
    def timeDimensionKey(self, input):
        self.__timeDimensionKey = input

    @property
    def indexGroupIteratorKey(self):
        return self.__indexGroupIteratorKey

    @indexGroupIteratorKey.setter
    def indexGroupIteratorKey(self, input):
        if input == self.timeDimensionKey:
            input = self.TIMEKEY
        self.__indexGroupIteratorKey = input
        self.indexGroupIteratorIdx = 0
        print("\nLookUpTable Iterator Key\n========================\n"\
              "[√] \'{}\' set as index group selector for analysis.".format(input))

    def mapTable(self):
        for i in range(self.mappingInputN):
            d = self.mapping[i]
            for key in d.keys():
                self.table[key] = []

    def add(self, mappedInput):
        if self.mappingInputN != 0 and len(mappedInput) == self.mappingInputN:
            for i in range(self.mappingInputN):
                self.reduce(mappedInput[i], i)
        else:
            print("[Error]: Cannot add to table. Provide map instructions.\n" \
            "For more information: print(LookUpTable object)")

    def reduce(self, input, index):
        for key, value in self.mapping[index].items():
            if(len(value) == 0):
               self.table[key].append(input)
            else:
                substr = input[value[0]:value[1]]
                substr = self.cleanInput(substr)
                substr = self.formatInput(substr)
                self.table[key].append(substr)

    def cleanInput(self, substr):
        s = substr
        for inChar in self.invalidCharacters:
            s = s.replace(inChar, "")
        return s

    def formatInput(self, substr):
        s = substr
        try:
            s = int(s)
        except ValueError:
            pass
        return s

    def annotateWith(self, annoTable):
        print("\nLookUpTable Annotation\n======================")
        self.exitEvalMethod(type(self) == type(annoTable), "[ERROR] Annotation must occur with type: {}".format(str(type(self))))
        matchingKeys = self.getMatchingKeys(annoTable.table)
        self.exitEvalMethod(len(matchingKeys) != 0, "[WARN] No matching keys found. Annotation has been terminated.")
        for rowIdx in range(len(annoTable.table[matchingKeys[0]])):
            matchingKeysValueOfRow = self.getMatchingKeysValueOfRow(annoTable, matchingKeys, rowIdx)
            matchingKeysValuesOfRowIndeciesInSelf = self.getIndeciesOfMatchingValuesInSelf(matchingKeys, matchingKeysValueOfRow)
            self.annotateRow(annoTable, rowIdx, matchingKeysValuesOfRowIndeciesInSelf)

    def getMatchingKeys(self, lookUpTable):
        matchingKeys = []
        for key, value in lookUpTable.items():
            for keyMatch, valueMatch in self.table.items():
                if key == keyMatch:
                    matchingKeys.append(key)
        print("Matching keys: {}".format(matchingKeys))
        return matchingKeys

    def getMatchingKeysValueOfRow(self, lookUpTable, keys, row):
        matchingKeysValueOfRow = []
        for key in keys:
            matchingKeysValueOfRow.append(lookUpTable.table[key][row])
        return matchingKeysValueOfRow

    def getIndeciesOfMatchingValuesInSelf(self, filterKeys, filterValues):
        indeciesGroupFromKeys = self.getMatchingIndeciesPerKey(filterKeys, filterValues)
        indexOfSmallestArr = self.getIndexOfSmallestMatchingArray(indeciesGroupFromKeys)
        matchingIndecies = self.getIndeciesMatchingAcrossAllKeyGroups(indeciesGroupFromKeys, indexOfSmallestArr)
        return matchingIndecies

    def getMatchingIndeciesPerKey(self, filterKeys, filterValues):
        indecies = []
        for i in range(len(filterKeys)):
            matchingValueForKeyIdx = []
            for row in range(len(self.table[filterKeys[i]])):
                if filterValues[i] == self.table[filterKeys[i]][row]:
                    matchingValueForKeyIdx.append(row)
            indecies.append(matchingValueForKeyIdx)
        return indecies

    def getIndexOfSmallestMatchingArray(self, indexGroup):
        groupIdx = 0
        groupLength = len(indexGroup[0])
        for i in range(len(indexGroup)):
            if groupLength > len(indexGroup[i]):
                groupLength = len(indexGroup[i])
                groupIdx = i
        return groupIdx

    def getIndeciesMatchingAcrossAllKeyGroups(self, indexGroup, smIdxArr):
        smallestArr = indexGroup[smIdxArr]
        finalIdxs = []
        for i in range(len(smallestArr)):
            boolAppend = True
            for j in range(len(indexGroup)):
                boolInside = False
                for k in range(len(indexGroup[j])):
                    if indexGroup[j][k] == smallestArr[i]:
                        boolInside = True
                if not boolInside:
                    boolAppend = False
            if boolAppend:
                finalIdxs.append(smallestArr[i])
        return finalIdxs

    def annotateRow(self, annoTable, annoRow, selfIndecies):
        keys = list(self.table.keys())
        valNo = len(self.table[keys[0]])
        addedKeys = []
        for key, values in annoTable.table.items():
            for index in selfIndecies:
                try:
                    self.table[key][index] = values[annoRow]
                except KeyError:
                    self.table[key] = ["-"]*valNo
                    self.table[key][index] = values[annoRow]
                    addedKeys.append(key)
        if len(addedKeys) != 0:
            print("Added keys   : {}".format(addedKeys))

    def cleanMissingness(self, missingnessChar = "-"):
        print("\nLookUpTable Cleaning\n====================")
        missingIdxs = self.findMissingFields()
        missingIdxs.sort(reverse = True)
        self.removeRowsFromTable(missingIdxs)
        print("[WARN] {} row(s) containing missing fields were found and removed.".format(str(len(missingIdxs))))

    def findMissingFields(self):
        idxs = []
        for key, values in self.table.items():
            for i in range(len(values)):
                if values[i] == "-" and self.isPresent(idxs, i) == False:
                    idxs.append(i)
        return idxs

    def isPresent(self, arr, val):
        for field in arr:
            if field == val:
                return True
        return False

    def removeRowsFromTable(self, idxs):
        for idx in idxs:
            self.removeRowFromTable(idx)

    def removeRowFromTable(self, idx):
        for key, values in self.table.items():
                self.table[key].pop(idx)

    def assignTimeDimension(self, key):
        self.timeDimensionKey = key
        timeUnits = list(numpy.unique(self.table[key]))
        n = len(self.table[key])
        timeCol = timeUnits * int((n/len(timeUnits)))
        self.table[self.TIMEKEY] = timeCol

    def exitEvalMethod(self, bool, msg):
        if not bool:
            print(msg)
            sys.exit()

    def indexTable(self):
        print("\nLookUpTable Indexing\n====================")
        self.checkForIndexHierarchy()
        self.setupIndex()
        idxs = range(len(self.table[self.indexHierarchy[0]]))
        self.indexNextKey(idxs, self.indexHierarchy)
        self.indexSummary()
        print("Finished indexing.")

    def checkForIndexHierarchy(self):
        if len(self.indexHierarchy) == 0:
            print("[ERROR] You need to provide an index hierarchy to index this table.\n"\
                  "        Please consult the documentation for more information.")
            sys.exit()

    def setupIndex(self):
        self.index = {}
        for indexKey in self.indexHierarchy:
            self.index[indexKey] = []

    def indexNextKey(self, idxs, keys, keyIndex = 0):
        indexKey = keys[keyIndex]
        values = self.getValuesAtIdxsWithKey(idxs, indexKey)
        uniqueValues = numpy.unique(values)
        for val in uniqueValues:
            singleValueIdxs = []
            for i in range(len(idxs)):
                if val == self.table[indexKey][idxs[i]]:
                    singleValueIdxs.append(idxs[i])
            self.index[indexKey].append(singleValueIdxs)
            if (len(keys)-1) > keyIndex:
                idx = keyIndex + 1
                self.indexNextKey(singleValueIdxs, keys, idx)

    def getValuesAtIdxsWithKey(self, idxs, key):
        vals = []
        for idx in idxs:
            vals.append(self.table[key][idx])
        return vals

    def indexSummary(self):
        for i in range(len(self.indexHierarchy)):
            print("[√] {} (n = {})".format(self.indexHierarchy[i], str(len(self.index[self.indexHierarchy[i]]))))

    def nextSourceIndexGroup(self):
        idxs = self.nextIndexGroup()
        sourceIdxs = []
        for i in range(len(idxs)):
            sourceIdxs.append(self.table["Index"][idxs[i]])
        return sourceIdxs

    def nextIndexGroup(self):
        if len(self.index[self.indexGroupIteratorKey]) > self.indexGroupIteratorIdx:
            idxGroup = self.index[self.indexGroupIteratorKey][self.indexGroupIteratorIdx]
            self.indexGroupIteratorIdx = self.indexGroupIteratorIdx + 1
            return idxGroup
        return []

    def __str__(self):
        if(self.mappingInputN != 0):
            output = "\nHipDynamics LookUpTable\n=======================\n"
            for key, values in self.table.items():
                output += key + ":"
                no = 6
                if len(values) < 6:
                    no = len(values)
                for i in range(no):
                    output += "    " + str(values[i])
                output += " ... (n = {}, u = {})".format(str(len(values)), str(len(numpy.unique(values))))
                output += "\n"
            return output
        else:
            return "\nHipDynamics LookUpTable\n" \
                   "=======================\n" \
                   "The object holds vital plate information to dynamically retrieve\n" \
                   "relevant information during the analysis.\n\n" \
                   "In order to query data from DBs and / or .csvs, please provide map\n" \
                   "instructions with the following syntax:\n\n" \
                   "table.mapping = [\n    {\n       'output1': [1,2],\n" \
                   "       'output2': [idx1, idx2]\n    },\n    {...}\n}\n\n" \
                   "The syntax allows the object to map multiple input types (eg. strings,\n" \
                   "ints, etc) into sub categories.\n" \
                   "A possible application could be the decomposition of filenames holding\n" \
                   "important metadata. If the output array is left blank, the input is \n" \
                   "assigned to the output directly.\n\n "


class LookUpTableWrapper:

    def __init__(self, lookUpTable = LookUpTable()):
        if type(LookUpTable()) == type(lookUpTable):
            self.table = lookUpTable
            self.dataSource = {"source": None}
            self.translationMap = []
        else:
            print("[ERROR] LookUpTableWrapper only accepts tables of type {}".format(str(type(LookUpTable()))))

    @property
    def table(self):
        return self.__table

    @table.setter
    def table(self, inputTable):
        self.__table = inputTable

    @property
    def translationMap(self):
        return self.__translationMap

    @translationMap.setter
    def translationMap(self, input):
        self.__translationMap = input

    def setDataSourceToMySQL(self, address, user, pwd, db, table):
        self.dataSource["source"] = "mysql"
        self.dataSource["mysql"] = {
            "address": address,
            "user": user,
            "pwd": pwd,
            "db": db,
            "table": table
        }

    def setDataSourceToCSV(self, path, rowOffset = 0):
        self.dataSource["source"] = "csv"
        self.dataSource["csv"] = {
            "path": path,
            "rowOffset": rowOffset
        }

    def populateTable(self, headers, rawData = []):
        if self.dataSource["source"] == "mysql":
            self.populateTableFromMysql(headers, rawData)
        if self.dataSource["source"] == "csv":
            self.populateTableFromCSV(headers, rawData)

    def populateTableFromMysql(self, headers, rawData = []):
        query = self.createQuery(headers)
        sqlInfo = self.dataSource["mysql"]
        db = pymysql.connect(sqlInfo["address"], sqlInfo["user"], sqlInfo["pwd"], sqlInfo["db"])
        cursor = db.cursor()
        try:
            cursor.execute(query)
        except:
            print("[Error]: unable to fetch data from MySQL.")
        else:
            results = cursor.fetchall()
            for row in results:
                row = self.formatRow(list(row), headers)
                self.table.add(list(row) + rawData)

    def createQuery(self, headers):
        query = "Select "
        for col in headers:
            query += "{}, ".format(col)
        query = query[:-2] + " from {};".format(self.dataSource["mysql"]["table"])
        return query

    def populateTableFromCSV(self, headers, rawData = []):
        with codecs.open(self.dataSource["csv"]["path"], "r", encoding='utf-8', errors='ignore') as inputFile:
            for i in range(self.dataSource["csv"]["rowOffset"]):
                next(inputFile)
            data = csv.DictReader(inputFile, delimiter = "\t")
            for result in data:
                row = []
                for key in headers:
                    row.append(result[key])
                row = self.formatRow(row, headers)
                self.table.add(row + rawData)

    def formatRow(self, row, headers):
        if len(self.translationMap) != 0:
            for trans in self.translationMap:
                keys = list(trans.keys())
                formatedRow = row
                for key in keys:
                    idxs = self.getIndeciesForKeysIn(headers, [key])
                    formatedRow = self.translate(row, idxs, trans[key])
                keysIdxs = self.getIndeciesForKeysIn(headers, keys)
                if len(keys) > 1:
                    formatedRow = self.concat(formatedRow, keysIdxs)
                return formatedRow
        else:
            return row

    def getIndeciesForKeysIn(self, arr, keys):
        idxs = []
        for i in range(len(arr)):
            for key in keys:
                if arr[i] == key:
                    idxs.append(i)
        return idxs

    def translate(self, row, idxs, transValues):
        transRow = row
        if len(transValues) != 0:
            for i in range(len(idxs)):
                transRow[idxs[i]] = transValues[int(transRow[idxs[i]])]
        return transRow

    def concat(self, row, idxs):
        insertIdx = idxs[0]
        concatStr = ""
        for i in range(len(idxs)):
            concatStr += "{}".format(str(row[idxs[i]]))
        idxs.sort()
        idxs.reverse()
        for i in range(len(idxs)-1):
            row.pop(idxs[i])
        row[insertIdx] = concatStr
        return row

class TableSetup:

    def __init__(self):
        self.path = ""
        self.pref = {}

    def __init__(self, preferencePath):
        self.path = preferencePath
        with open(preferencePath) as data:
            self.pref = json.load(data)

    @property
    def pref(self):
        return self.__pref

    @pref.setter
    def pref(self, preferences):
        self.__pref = preferences

    @property
    def table(self):
        return self.__table

    @table.setter
    def table(self, inputTable):
        self.__table = inputTable

    def setup(self):
        self.checkPreferences()
        self.table = self.setupLookUpTable("primary_lookUpTable")
        if self.pref["dataSource"]["annotation_lookUpTable"]["source"]["type"] != None:
            annoTable = self.setupLookUpTable("annotation_lookUpTable")
            self.table.annotateWith(annoTable)
        self.table.assignTimeDimension(self.pref["timeDimensionColName"])
        self.table.cleanMissingness()
        self.table.indexHierarchy = self.pref["indexHierarchy"]
        self.table.indexTable()
        self.table.indexGroupIteratorKey = self.pref["indexIteratorSelector"]
        self.table.sourceFeaturePatternSelector = self.pref["sourceFeaturePatternSelector"]
        if not self.pref["production"]:
            print(self.table)
        print("\n*** SETUP SUCCESSFUL ***\n")

    def checkPreferences(self):
        print("\nHipDynamics Setup Check\n=======================")
        keys = list(self.pref.keys())
        self.evalKeyCheck(keys, "dataSource")
        self.evalKeyCheck(keys, "production")
        self.evalKeyCheck(keys, "timeDimensionColName")
        self.evalKeyCheck(keys, "indexHierarchy")
        self.evalKeyCheck(keys, "indexIteratorSelector")
        self.evalKeyCheck(keys, "sourceFeaturePatternSelector")
        keysSetup = list(self.pref["dataSource"].keys())
        self.evalKeyCheck(keysSetup, "primary_lookUpTable")
        keysTable = list(self.pref["dataSource"]["primary_lookUpTable"].keys())
        self.evalKeyCheck(keysTable, "source")
        keysSource = list(self.pref["dataSource"]["primary_lookUpTable"]["source"].keys())
        self.evalKeyCheck(keysSource, "type")
        typeSourceKey = self.pref["dataSource"]["primary_lookUpTable"]["source"]["type"]
        self.evalKeyCheck(keysSource, typeSourceKey)
        self.evalKeyCheck(keysTable, "map")
        indexKey = list(self.pref["dataSource"]["primary_lookUpTable"]["map"][0].keys())
        self.evalKeyCheck(indexKey, "Index")
        self.evalKeyCheck(keysTable, "invalidCharacters")
        self.evalKeyCheck(keysTable, "translationMap")
        self.evalKeyCheck(keysSetup, "annotation_lookUpTable")
        keysTable = list(self.pref["dataSource"]["annotation_lookUpTable"].keys())
        self.evalKeyCheck(keysTable, "source")
        keysSource = list(self.pref["dataSource"]["annotation_lookUpTable"]["source"].keys())
        self.evalKeyCheck(keysSource, "type")
        typeSourceKey = self.pref["dataSource"]["annotation_lookUpTable"]["source"]["type"]
        self.evalKeyCheck(keysSource, typeSourceKey)
        self.evalKeyCheck(keysTable, "map")
        self.evalKeyCheck(keysTable, "invalidCharacters")
        self.evalKeyCheck(keysTable, "translationMap")
        print("PASS.")

    def setupLookUpTable(self, lookUpTableSelector):
        table = LookUpTable()
        table.mapping = self.pref["dataSource"][lookUpTableSelector]["map"]
        table.invalidCharacters = self.pref["dataSource"][lookUpTableSelector]["invalidCharacters"]
        sourceType = self.pref["dataSource"][lookUpTableSelector]["source"]["type"]
        sourceSpecs = self.pref["dataSource"][lookUpTableSelector]["source"][sourceType]
        wrapper = LookUpTableWrapper(table)
        if len(self.pref["dataSource"][lookUpTableSelector]["translationMap"]) != 0:
            wrapper.translationMap = self.pref["dataSource"][lookUpTableSelector]["translationMap"]
        if sourceType == "MySQL":
            wrapper.setDataSourceToMySQL(sourceSpecs["address"],
                                         sourceSpecs["user"], sourceSpecs["pwd"],
                                         sourceSpecs["db"], sourceSpecs["table"])
        if sourceType == "CSV":
            wrapper.setDataSourceToCSV((sourceSpecs["path"] + sourceSpecs["fileName"]), sourceSpecs["rowOffset"])
        wrapper = self.populateTableHelper(wrapper, sourceSpecs, sourceType)
        table = wrapper.table
        if not self.pref["production"]:
            print(table)
        return table

    def populateTableHelper(self, wrapper, sourceSpecs, sourceType):
        if sourceType == "CSV":
            if sourceSpecs["isDirectory"]:
                pass # need to add multiple files capability here
            else:
                raw = self.evalRaw(sourceSpecs)
                wrapper.setDataSourceToCSV((sourceSpecs["path"] + sourceSpecs["fileName"]), sourceSpecs["rowOffset"])
                wrapper.populateTable(sourceSpecs["columnNames"], raw)
        if sourceType == "MySQL":
            wrapper.setDataSourceToMySQL(sourceSpecs["address"],
                                         sourceSpecs["user"], sourceSpecs["pwd"],
                                         sourceSpecs["db"], sourceSpecs["table"])
            wrapper.populateTable(sourceSpecs["columnNames"], sourceSpecs["raw"])
        return wrapper

    def evalRaw(self, sourceSpecs):
        keys = list(sourceSpecs.keys())
        if self.checkForKey(keys, sourceSpecs["raw"][0]) and len(sourceSpecs["raw"]) == 1:
            return [sourceSpecs[sourceSpecs["raw"][0]]]
        return sourceSpecs["raw"]

    def evalKeyCheck(self, arr, key):
        check = self.checkForKey(arr, key)
        if not check:
            print("[X]: The key \'{}\' was not found in the specified\n"\
                  "     preference file. Please consult the documentation.\nFAIL.".format(key))
            sys.exit()
        else:
            print("[√]: Key \'{}\' found.".format(key))

    def checkForKey(self, arr, key):
        for item in arr:
            if item == key:
                return True
        return False

    def __str__(self):
        info = "\nHipDynamics TableSetup\n======================\n" \
            "Type {} is a HipDynamics helper. Create a preference.json\n" \
            "file in which data sources, annotation tables and analysis types\n" \
            "can be specified. For more information on how to setup the \n" \
            "prefrence.json file look up the documentation on our website.\n".format(str(type(self)))
        return info
