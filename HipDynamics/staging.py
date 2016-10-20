# -*- coding: utf-8 -*-
#!/usr/bin/python3

import os
import sys
import csv
import json
import numpy
import codecs
import pymysql as pymysql

class LookUpTable:
    def __init__(self):
        self.table = {}
        self.requiresIndexAssignment = False
        self.index = {}
        self.mapping = []
        self.mappingInputN = 0
        self.invalidCharacters =[]
        self.TIMEKEY = "TIME_DIMENSION"
        self.timeDimensionKey = ""
        self.indexHierarchy = []
        self.indexGroupIteratorIdx = 0
        self.sourceFeaturePatternSelector = None
        self.sourceFeatureAccessInfo = None
        self.metadataOfRetrievedIndexGroup = ""

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
                          "        Please double check your indexHierarchy keys.".format(indexKey))
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
        if self.requiresIndexAssignment:
            mapInstructions.append({"Index": []})
        self.__mapping = mapInstructions
        self.mappingInputN = len(self.__mapping)
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
        if len(self.indexHierarchy) == 0:
            print("[ERROR] The indexHierarchy must be set before setting the indexGroupIteratorKey.")
            sys.exit()
        if input == self.timeDimensionKey:
            input = self.TIMEKEY
        self.__indexGroupIteratorKey = input
        self.indexGroupIteratorIdx = 0
        print("\nLookUpTable Iterator Key\n========================\n"\
              "[√] \'{}\' set as index group selector for analysis.".format(input))
        self.indexGroupIteratorKeyIdxs = []
        for i in range(len(self.indexHierarchy)):
            if self.indexHierarchy[i] == self.__indexGroupIteratorKey:
                self.indexGroupIteratorKeyIdxs.append(i)
        if self.indexGroupIteratorKeyIdxs[0] < (len(self.indexHierarchy)-1):
            self.indexGroupIteratorKeyIdxs.append(self.indexGroupIteratorKeyIdxs[0]+1)
        else:
            print("[WARN] The selected indexGroupIteratorKey (indexIteratorSelector) is not followed\n"\
                  "       by another dimension. The latter will result in a one-dimensional index iteration\n"\
                  "       which may affect your analysis. For more information consult the documentation.")


    @property
    def sourceFeaturePatternSelector(self):
        return self.__sourceFeaturePatternSelector

    @sourceFeaturePatternSelector.setter
    def sourceFeaturePatternSelector(self, input):
        self.__sourceFeaturePatternSelector = input

    @property
    def sourceFeatureAccessInfo(self):
        return self.__sourceFeatureAccessInfo

    @sourceFeatureAccessInfo.setter
    def sourceFeatureAccessInfo(self, input):
        self.__sourceFeatureAccessInfo = input

    def mapTable(self):
        for i in range(self.mappingInputN):
            d = self.mapping[i]
            for key in d.keys():
                self.table[key] = []

    def add(self, mappedInput):
        if self.requiresIndexAssignment:
            mappedInput.append(len(self.table["Index"]))
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
            if (len(self.table[key])-1) >= idx:
                self.table[key].pop(idx)

    def assignTimeDimension(self, key):
        self.timeDimensionKey = key
        timeCol = self.table[key].copy()
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
        self.compressIndex()
        self.indexSummary()
        print("Finished indexing.")

    def checkForIndexHierarchy(self):
        if len(self.indexHierarchy) == 0:
            print("[ERROR] You need to provide an index hierarchy to index this table.\n"\
                  "        Please consult the documentation for more information.")
            sys.exit()

    def setupIndex(self):
        for indexKey in self.indexHierarchy:
            self.index[indexKey] = []

    def indexNextKey(self, idxs, keys, keyIndex = 0):
        indexKey = keys[keyIndex]
        values = self.getValuesAtIdxsWithKey(idxs, indexKey)
        uniqueValues = self.getUnsortedUniqueValues(values)
        for val in uniqueValues:
            singleValueIdxs = []
            for i in range(len(idxs)):
                if val == self.table[indexKey][idxs[i]]:
                    singleValueIdxs.append(idxs[i])
            self.index[indexKey].append(singleValueIdxs)
            if (len(keys)-1) > keyIndex:
                idx = keyIndex + 1
                self.indexNextKey(singleValueIdxs, keys, idx)

    def getUnsortedUniqueValues(self, values):
        npValues = numpy.array(values)
        npUniqueIdxs = numpy.unique(npValues, return_index=True)[1]
        npUniqueValues = npValues[numpy.sort(npUniqueIdxs)]
        uniqueValues = npUniqueValues.tolist()
        return uniqueValues

    def getValuesAtIdxsWithKey(self, idxs, key):
        vals = []
        for idx in idxs:
            vals.append(self.table[key][idx])
        return vals

    def indexSummary(self):
        for i in range(len(self.indexHierarchy)):
            print("[√] {} (n = {})".format(self.indexHierarchy[i], str(len(self.index[self.indexHierarchy[i]]))))

    def compressIndex(self):
        pass

    def nextIndexGroup(self):
        idxs = self.nextLookUpTableIndexGroup()
        self.metadataOfRetrievedIndexGroup = self.gatherMetaDataOfUpstreamDimensions(idxs)
        if len(self.indexGroupIteratorKeyIdxs) == 2:
            complexDimIdxs = self.retrieveMatchingIndexGroupsOfDownstreamDimension(idxs)
            sourceIdxs = []
            for indexGroup in complexDimIdxs:
                sourceIdxs.append(self.translateIndeciesToSourceIndecies(indexGroup))
            return sourceIdxs
        else:
            sourceIdxs = self.translateIndeciesToSourceIndecies(idxs)
        return sourceIdxs

    def nextLookUpTableIndexGroup(self):
        if len(self.index[self.indexGroupIteratorKey]) > self.indexGroupIteratorIdx:
            idxGroup = self.index[self.indexGroupIteratorKey][self.indexGroupIteratorIdx]
            self.indexGroupIteratorIdx = self.indexGroupIteratorIdx + 1
            return idxGroup
        return []

    def gatherMetaDataOfUpstreamDimensions(self, idxs):
        meta = []
        if len(idxs) == 0: return meta
        idx = idxs[0]
        for i in range((self.indexGroupIteratorKeyIdxs[0]+1)):
            meta.append({self.indexHierarchy[i]: self.table[self.indexHierarchy[i]][idx]})
        return meta

    def retrieveMatchingIndexGroupsOfDownstreamDimension(self, idxs):
        downstreamIndexKey = self.indexHierarchy[self.indexGroupIteratorKeyIdxs[1]]
        twoDimList = []
        for indexGroup in self.index[downstreamIndexKey]:
            if self.isIndexGroupInIdxsList(indexGroup, idxs):
                twoDimList.append(indexGroup)
        return twoDimList

    def isIndexGroupInIdxsList(self, indexGroup, idxsList):
        for index in indexGroup:
            for idx in idxsList:
                if index == idx:
                    return True
        return False

    def translateIndeciesToSourceIndecies(self, idxs):
        sourceIdxs = []
        for i in range(len(idxs)):
            sourceIdxs.append(self.table["Index"][idxs[i]])
        return sourceIdxs

    def generateLookUpTableMapFromList(self, vals):
        map = []
        for val in vals:
            map.append({val: []})
        return map

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

    def setDataSourceToCSV(self, path, rowOffset = 0, delimiter=","):
        self.dataSource["source"] = "csv"
        self.dataSource["csv"] = {
            "path": path,
            "rowOffset": rowOffset,
            "delimiter": delimiter
        }

    def populateTable(self, headers, rawData = []):
        if self.dataSource["source"] == "mysql":
            self.populateTableFromMysql(headers, rawData)
        if self.dataSource["source"] == "csv":
            self.populateTableFromCSV(headers, rawData, self.dataSource["csv"]["delimiter"])

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
        db.close()

    def createQuery(self, headers):
        query = "Select "
        for col in headers:
            query += "{}, ".format(col)
        query = query[:-2] + " from {};".format(self.dataSource["mysql"]["table"])
        return query

    def populateTableFromCSV(self, headers, rawData = [], delimiter = ","):
        with codecs.open(self.dataSource["csv"]["path"], "r", encoding='utf-8', errors='ignore') as inputFile:
            for i in range(self.dataSource["csv"]["rowOffset"]):
                next(inputFile)
            data = csv.DictReader(inputFile, delimiter=str(delimiter))
            for result in data:
                row = []
                for key in headers:
                    try:
                        row.append(result[key])
                    except KeyError:
                        print("[ERROR] The key '{}' could not be exracted from" \
                              " the specified file: {}.".format(key, self.dataSource["csv"]["path"]))
                        sys.exit()
                row = self.formatRow(row, headers)
                self.table.add(row + rawData)
            inputFile.close()

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

    def __init__(self, preferencePath):
        self.assumptions = "[WARN] Assumptions have been made about your data based on the specified preferences:\n"
        self.hasAssumptions = False
        self.assumptionNo = 0
        self.hasIndex = True
        self.pref = {}
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

    @property
    def analysisPreferences(self):
        return self.__pref["analysis"]

    @analysisPreferences.setter
    def analysisPreferences(self, input):
        self.__pref["analysis"] = input

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
        self.table.sourceFeatureAccessInfo = self.getSourceFeatureAccessInfo()
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
        self.evalKeyCheck(keys, "analysis")
        keysSetup = list(self.pref["dataSource"].keys())
        self.evalKeyCheck(keysSetup, "primary_lookUpTable")
        keysTable = list(self.pref["dataSource"]["primary_lookUpTable"].keys())
        self.evalKeyCheck(keysTable, "source")
        keysSource = list(self.pref["dataSource"]["primary_lookUpTable"]["source"].keys())
        self.evalKeyCheck(keysSource, "type")
        typeSourceKey = self.pref["dataSource"]["primary_lookUpTable"]["source"]["type"]
        self.evalKeyCheck(keysSource, typeSourceKey)
        self.evalKeyCheck(keysTable, "map")
        mapDicts = list(self.pref["dataSource"]["primary_lookUpTable"]["map"])
        self.evalArrDictKeyCheck(mapDicts, "Index")
        self.evalKeyCheck(keysTable, "invalidCharacters")
        self.evalKeyCheck(keysTable, "translationMap")
        self.evalKeyCheck(keysSetup, "annotation_lookUpTable")
        keysTable = list(self.pref["dataSource"]["annotation_lookUpTable"].keys())
        self.evalKeyCheck(keysTable, "source")
        keysSource = list(self.pref["dataSource"]["annotation_lookUpTable"]["source"].keys())
        self.evalKeyCheck(keysSource, "type")
        typeSourceKey = self.pref["dataSource"]["annotation_lookUpTable"]["source"]["type"]
        if typeSourceKey != None:
            self.evalKeyCheck(keysSource, typeSourceKey)
            self.evalKeyCheck(keysTable, "map")
        else:
            self.addAssumption("No annotation source was found. All relevant information for indexing " \
                           "are contained in the primary LookUpTable.")
        self.evalKeyCheck(keysTable, "invalidCharacters")
        self.evalKeyCheck(keysTable, "translationMap")
        self.evalKeyCheck(keysSetup, "analysis_source")
        typeSourceKey = self.pref["dataSource"]["analysis_source"]["source"]["type"]
        if typeSourceKey != None:
            keysSource = list(self.pref["dataSource"]["analysis_source"]["source"].keys())
            self.evalKeyCheck(keysSource, typeSourceKey)
        else:
            self.addAssumption("No analysis source was found. All relevant information for analysis"\
                               " are contained in the primary LookUpTable.")
        if self.hasAssumptions:
            print(self.assumptions)
        print("PASS.")

    def addAssumption(self, msg):
        self.hasAssumptions = True
        self.assumptionNo = self.assumptionNo + 1
        self.assumptions += "   [{}] ".format(self.assumptionNo)
        self.assumptions += "{}\n".format(msg)

    def setupLookUpTable(self, lookUpTableSelector):
        table = LookUpTable()
        if lookUpTableSelector == "primary_lookUpTable" and not self.hasIndex:
            table.requiresIndexAssignment = True
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
            wrapper.setDataSourceToCSV((sourceSpecs["path"] + sourceSpecs["fileName"]),
                                       sourceSpecs["rowOffset"], sourceSpecs["delimiter"])
        wrapper = self.populateTableHelper(wrapper, sourceSpecs, sourceType)
        table = wrapper.table
        if not self.pref["production"]:
            print(table)
        return table

    def populateTableHelper(self, wrapper, sourceSpecs, sourceType):
        if sourceType == "CSV":
            if sourceSpecs["isDirectory"]:
                files = os.listdir(sourceSpecs["path"])
                filteredFiles = self.filterForStringsContainingX(files, sourceSpecs["fileNameContains"])
                sourceSpecs["fileNames"] = filteredFiles
                for fileName in sourceSpecs["fileNames"]:
                    sourceSpecs["fileName"] = fileName
                    raw = self.evalRaw(sourceSpecs)
                    wrapper.setDataSourceToCSV((sourceSpecs["path"] + "/" + sourceSpecs["fileName"]),
                                               sourceSpecs["rowOffset"], sourceSpecs["delimiter"])
                    wrapper.populateTable(sourceSpecs["columnNames"], raw)
            else:
                raw = self.evalRaw(sourceSpecs)
                wrapper.setDataSourceToCSV((sourceSpecs["path"] + "/" + sourceSpecs["fileName"]),
                                           sourceSpecs["rowOffset"], sourceSpecs["delimiter"])
                wrapper.populateTable(sourceSpecs["columnNames"], raw)
        if sourceType == "MySQL":
            wrapper.setDataSourceToMySQL(sourceSpecs["address"],
                                         sourceSpecs["user"], sourceSpecs["pwd"],
                                         sourceSpecs["db"], sourceSpecs["table"])
            wrapper.populateTable(sourceSpecs["columnNames"], sourceSpecs["raw"])
        return wrapper

    def evalRaw(self, sourceSpecs):
        keys = list(sourceSpecs.keys())
        if len(sourceSpecs["raw"]) == 1:
            if self.checkForKey(keys, sourceSpecs["raw"][0]):
                return [sourceSpecs[sourceSpecs["raw"][0]]]
        return sourceSpecs["raw"]

    def filterForStringsContainingX(self, strings, stringX):
        if stringX != "" or stringX != None:
            filtered = []
            for string in strings:
                if stringX in string:
                    filtered.append(string)
            return filtered
        return strings

    def evalArrDictKeyCheck(self, arrDict, key):
        evalKeys = list(arrDict[0].keys())
        for d in arrDict:
            keys = list(d.keys())
            check = self.checkForKey(keys, key)
            if check:
                evalKeys = keys
        self.evalKeyCheck(evalKeys, key)


    def evalKeyCheck(self, arr, key):
        check = self.checkForKey(arr, key)
        if not check and key != "Index":
            print("[X]: The key \'{}\' was not found in the specified\n"\
                  "     preference file. Please consult the documentation.\nFAIL.".format(key))
            sys.exit()
        if not check and key == "Index":
            self.addAssumption("Index in LookUpTable was not defined. A row index is created automatically.")
            self.hasIndex = False
        print("[√]: Key \'{}\' found.".format(key))

    def checkForKey(self, arr, key):
        for item in arr:
            if item == key:
                return True
        return False

    def getSourceFeatureAccessInfo(self):
        dataSource = self.pref["dataSource"]["analysis_source"]["source"]
        if dataSource["type"] == None:
            dataSource = self.pref["dataSource"]["primary_lookUpTable"]["source"]
        return dataSource

    def __str__(self):
        info = "\nHipDynamics TableSetup\n======================\n" \
            "Type {} is a HipDynamics helper. Create a preference.json\n" \
            "file in which data sources, annotation tables and analysis types\n" \
            "can be specified. For more information on how to setup the \n" \
            "prefrence.json file look up the documentation on our website.\n".format(str(type(self)))
        return info
