import argparse
import select
from socket import *
import sys
import time
import threading
import os
import json
import random


# A list of global variables to be used throughout the GBN program
argList = []  # Argument parser
readyToPrint = True
routingTableEntry = {"NeighborNode": 0, "Distance": 0, "NextHop": 0}
nodeRoutingTable = []
# Read all arguments into a list, with error handling
for eachArg in sys.argv:   
        argList.append(eachArg)
    
    # error handling


selfPort = int(argList[1])
argList.pop(0)
argList.pop(1)

neighborDistance = argList[1::2]
neighborNodes = argList[0::2]

if len(neighborNodes) > 16:
    print ("Too many nodes (maximum 16")
    sys.exit()
    
for i in neighborNodes:
    if int(i) < 1024:
        print("Please enter a port number that is greater than 1024")
        sys.exit()
    else:
        routingTableEntry["NeighborNode"]=int(i)
        nodeRoutingTable.append(routingTableEntry)
   
for i in neighborDistance:
        routingTableEntry["Distance"]=float(i)
        nodeRoutingTable.append(routingTableEntry)
        
             
print nodeRoutingTable




    
