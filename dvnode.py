import argparse
import select
from socket import *
import sys
import time
import threading
import os
import json
import random
from platform import node


# A list of global variables to be used throughout the DV program
argList = []  # Argument parser
readyToPrint = True

nodeRoutingTable = {}
# Read all arguments into a list, with error handling
for eachArg in sys.argv:   
        argList.append(eachArg)

print argList

selfPort = int(argList[1])
argList.pop(0)
argList.pop(0)
print selfPort
print argList

neighborDistance = argList[1::2]
neighborNodes = argList[0::2]

if len(neighborNodes) > 16:
    print ("Too many nodes (maximum 16")
    sys.exit()

count = 0
for i in neighborNodes:
        # test for use of 'localhost' or other hostname mappings
        neighborId = count 
        nodeRoutingTable[count] = {}
        nodeRoutingTable[neighborId]["Node"] = i
        count+=1


count = 0
for i in nodeRoutingTable:
    nodeRoutingTable[count]["Distance"]=neighborDistance[count]
    count+=1
    
print nodeRoutingTable