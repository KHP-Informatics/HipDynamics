<img src="HDOpenS-Logo.png" width="100"> # HipDynamics 
HipDynamics is a data analytics middleware that allows you to slice multi-dimensional data sets according to a pre-defined context. It is completely data type agnostic, supports database access and multi data set mergers. HipDynamics is designed to abstract away many of the tedious and repetitive data formating tasks required before one is actually able to apply an analysis.


#### Born in Academia. Built for Ease-of-Use
 Research in wet laboraties generate ever larger data sets which increase in complexity, particularly in the event of introducing the dimension of time. HipDynamics is capable of slicing and dicing your data set into managable and context-related chunks. These can then be passed on to run any required analysis. The paper '_A novel automated high-content analysis pipeline capturing cell population dynamics from induced pluripotent stem cell live imaging data_' published in the [Journal of Biomolecular Screnning, 2016][JBS2016] explores stem cell population dynamics using extracted phenotypic data and performing linear regression on hundreds of cell lines and thousands of images. The package was specifically designed to deal with large amounts of data efficiently and reliably. 

## HipDynamics Documentation
The package consists out of two modules, an analysis module and a staging module. Implementation, configuration and its middleware concepts are explained below.

#### Implementation
In order to make use of HipDynamics, simply download the repository, drop the HipDynamics package into your project and import it using the `import HipDynamics.*` statement.

#### Configuration
In order to configure HipDynamics, you can specify a preferences.json file or dynamically create it at run-time in your project and parse the JSON into the `TableSetup` object. The schema of the latter JSON will be explained in this section.
 
#### Defining the DataSources
Let's get the most complex bit out of the way. Data sets come in all shapes and size. Put in other words, one data set may be as simple as one large file, or distributed between multiple files, database tables, some even store vital metadata, separately. Yes, HipDynamics can handle all of these cases, so bear with us.

___

#### The primary_lookUpTable
The `primary_lookUpTable` contains the columns of your data set which are required to selectively slice your data set. Once created, it is used to query the right data at run time of your analysis and efficiently allocate / dealloacte memory with required information only. It is also the table to which any additional metadata contained in separate files is merged with (see _The annnotation_lookUpTable_ for more information)

Properties:
- `source`
- `map`
- `translationMap`
- `invalidCharacters`

If your data set is contained in one file or database table only, you can safely ignore the following two sections on the `annotation_lookUpTable` and `analysis_source`. Simply leave them in the default state as shown in the `preferencesSample.json` example.

___

#### The annotation_lookUpTable
The `annotation_lookUpTable` comes into play when your `primary_lookUpTable`'s content is not sufficient enough to allow appropriate slicing of the data. In cases where meta data is stored independetly of its raw data, the `annotation_lookUpTable` becomes a vital tool. There can only be one `annotation_lookUpTable` property in your configuration file, however it can be configured to search through folders to annotate the `primary_lookUpTable` with the content of all files within it (also supports string-matching).

Properties:
- `source`
- `map`
- `translationMap`
- `invalidCharacters`

#### The analysis_source
The `analysis_source` must be specified in cases where the source of the `primary_lookUpTable` does not contain the raw data set which is supposed to be sliced.

Properties:
- `source`

___

#### Configuring the 'source' property
The `source`'s properties are defined below:

| Property | Example | Definition |
|----------|---------|------------|
| `type` | `"type": "CSV"` | The type of data source. Choose between "CSV", "TXT" (tab-delimited) and "MySQL". |
| `CSV` | `"CSV": {...}` | The CSV property contains all information necessary to fill or annotate a table. Its properties are found in the next table.|
| `MySQL` | `"MySQL"`: {...} | The MySQL property contains all information necessary to fill or annotate a table. Its properties are found in the next table. |

CSV

| Property | Example | Definition |
|----------|---------|------------|
| `path` | `"path": "/Input/Path"` | The path to file or folder containing the data source. |
| `filename` | `"fileName": "InputFile.csv"` | The input filename can be specified here. In the case of searching an entire directory assign an empty string: `""` |
| `delimter` | `"delimiter": ","` |  The delimiter used within the file. |
| `rowOffset` | `"rowOffset": 0` | In some cases, files contain headers. If you'd like to ignore them, enter the number of rows you'd like to skip. |
| `columnNames` | `"columnNames": ["Frame", "Lineage ID", ...]` | Specify the column names which you would like to use to slice your data set with. |
| `isDirectory` | `"isDirectory": false` | Set it to `true`, if you'd like to import files from an entire folder. |
| `filenames` | `"fileNames":[]` | Specifiy multiple filenames to import. Leave as empty array (`[]`) otherise.
| `fileNameContains` | `"fileNameContains": "string"` | To selectively search a folder, specify the string it contains. |
| `raw` | `"raw": []` | If there are properties or values that you like to attach to import for all values specify them here. A magic property is `fileName` which will import the filename of the file currently being loaded after reading a row of the specified `columnnames`. |

MySQL

| Property | Example | Definition |
|----------|---------|------------|
| `address` | `"address": "127.0.0.1"` | Specify the address of the MySQL server. |
| `user` | `"user": "username"` | Specify the username. |
| `pwd` | `"pwd": "password"` |  Specify the password for the user. |
| `db` | `"db": "database name"` | Specify the database name. |
| `table` | `"table": "table name"` | Specify the table name. |
| `columnNames` | `"columnNames": ["Frame", "Lineage ID", ...]`| Specify the column names which you would like to use to slice your data set with.|
| `raw` | `"raw": []` | If there are properties or values that you like to attach to import for all values specify them here. A magic property is `fileName` which will import the filename of the file currently being loaded after reading a row of the specified `columnnames`. |


#### Configuring the 'map' property
The `map` property is dynamic and depends on the columns you've specified in the `source` property. The name you specify in the map will be the identifier for the remainder of all downstream operations and outputs. 

Example:
Given the following source specification:
>```"columnName": ["Latitude", "Longitude"], "raw": ["London_01-01-1970.csv"]```

The data vector that will be added to the specified table will look like this:
>```["51.5074° N", "0.1278° W", "London_01-01-1970.csv"]```

The map property allows you to assign your own choice of column names:
>```"map": [ {"Lat": []}, {"Lon": []}, {"FileName": []} ]```

Resulting in the follwing table entry:

> | Lat | Lon | Filename |
> |----------|---------|------------|
> | 51.5074° N | 0.1278° W | London_01-01-1970.csv |

However, the map property is more powerful than that. It allows you to extract metadata from strings and assign those to new columns.
> ```"map": [ {"Lat": []}, {"Lon": []}, {"City": [0,5], "Date": [7, 16]} ]```

The slightly altered map property would result in the following entry of a chosen table (based on the input of step 2):

> | Lat | Lon | City | Date |
> |----------|---------|------------|
> | 51.5074° N | 0.1278° W | London | 01-01-1970 |


#### Configuring the `translationMap` property
In some cases, it is necessary to translate inputs into other values, from an integer to a string as an example. In other cases, one might want to merge to columns from the input source before inserting them into the table. This what the tranlationMap allows. **Important**: The input vector will first be parsed through the `translationMap` process, before being forwarded to the `map` process which will in turn added the input vector the specified table. As a result it is important to consider how your input vector might change and adjust your `map` accordingly.

Exmaple:
Consider the following scenario: Traditionally, 96 well plates, designed for cell cultures, identifies each row of wells as A, B, C, etc. and each column as 1, 2, 3, etc. with a layout of 8 x 12. As result, a well is usually identified as A2 or C3. However, some analytics tools export well coordinates as separate numeric coordinates in two columns, such as 1, 2 or 3, 3. In such a case, one might want to revert the coordinates to the traditional notation. 
> Source extract: `"columnNames": ["Row", "Col"]`
> Input vector: `[1, 2]` - where the first value identifies the row and the second the column.

The following translation map allows `[1, 2]` to be translated into `A2`:
>```"translationMap": [ {"Row": ["A", "B", "C", "D", "E", "F", "G", "H"], "Col": [] } ]```

For each input vector, the `translationMap` process selects the values with columnnames that were specified in a `translationMap` entry. If the vector (`[]`) for that particular identifer is empty, the value will not be translated. Should the vector contain values, it will match the index to the value. In the end, all identifiers in a given `translationMap` entry are concatenated and passed with the remaining values of the input vector to the `map` process.

#### Specifying invalid characters
During translation and mapping processes, such as substring extraction one might want to remove unwanted characters, such - or _ .

The `invalidCharacters` property can hold any number of unwanted characters or substrings, which will be removed at the end of each string operation process during `translationMap` and `map` processes.

___

#### Indexing and Slicing properties

| Property | Example | Definition |
|----------|---------|------------|
| `timeDimensionColName` | `"timeDimensionColName": "Frame"` | Specify the address of the MySQL server. |
| `indexHierarchy` | `"indexHierarchy": ["Lineage", "TrackingID", "Frame"]` | Specify the username. |
| `indexIteratorSelector` | `"indexIteratorSelector": "TrackingID"` |  Specify the password for the user. |
| `sourceFeaturePatternSelector` | `"sourceFeaturePatternSelector": "test"` | Specify the database name. |

___

#### Setting analysis parameters
The `analysis` property can hold any configuration that you'd like to pass into your own analysis object. It will not be altered during the process of data set slicing.
See the `preferenceSample.json` for an example implementation of the default linear regression analysis. 


[JBS2016]: http://journals.sagepub.com/doi/pdf/10.1177/1087057116652064 
