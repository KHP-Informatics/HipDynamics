import os
from HipDynamics.staging import *

def main():

    path = "/Users/Kerz/Documents/projects/HIPSCI/HipDynamicsPy/preferences.json"
    tbs = TableSetup(path)
    tbs.setup()
    table = tbs.table

    for i in range(24):
        idx = table.nextSourceIndexGroup()
        print(str(idx))

main()