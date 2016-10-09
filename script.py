import os
from HipDynamics.staging import *

def main():

    path = "/Users/Kerz/Documents/projects/HIPSCI/HipDynamicsPy/preferences.json"
    tbs = TableSetup(path)
    tbs.setup()
    table = tbs.table

main()