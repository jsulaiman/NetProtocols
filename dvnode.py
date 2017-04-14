import argparse
import select
from socket import *
import sys
import time
import threading
import os
import json
import random

# A list of global variables to be used throughout the DV program
argList = []  # Argument parser
readyToPrint = True
isLastNode = False
sendToNeighbors=False
SelfRoutingTable =[]
firstTimeReceiving = True
# Read all arguments into a list, with error handling
for eachArg in sys.argv:   
        argList.append(eachArg)

self_port = int(argList[1])
argList.pop(0);argList.pop(0)

#print argList

neighborDistance = argList[1::2]
neighborNodes = argList[0::2]

if neighborNodes[len(neighborNodes)-1]=="last":
    isLastNode = True
    firstTimeReceiving=False
    neighborNodes.pop()
    
if len(neighborNodes) > 16:
    print ("Too many nodes (maximum 16")
    sys.exit()
    
def reserve_printer():
    global readyToPrint
    
    while readyToPrint == False:
        time.sleep(0.0001)
        
    readyToPrint = False
    
def release_printer():
    global readyToPrint
    readyToPrint = True
    
    
#Current node initialization
def initialize_self_table():
    for i in neighborNodes:
            #initialize routing Table Structure
            routingTableStructure = {"TargetNode": 0,"SourceNode":0,"Distance":9, "NextHop": None, "isTargetAndSourceNeighbors": True, "nodeExists": None}
            
            routingTableStructure["SourceNode"] = self_port
            routingTableStructure["TargetNode"] = int(i)
            routingTableStructure["nodeExists"] = True
            SelfRoutingTable.append(routingTableStructure)
    
    count = 0
    for i in SelfRoutingTable:
        i["Distance"]=round(float(neighborDistance[count]),2)
        count+=1

def print_table():
    #print SelfRoutingTable
    print("[%s] Node %d Routing Table " % (repr(time.time()), self_port))
    
    for i in SelfRoutingTable:
        if i["NextHop"]==None:
            print " - (%f) -> Node %d" %(i["Distance"],i["TargetNode"])
        else:
            print " - (%f) -> Node %d' Next hop -> Node %d" %(i["Distance"],i["TargetNode"],i["NextHop"])

def send_table_to_neighbors():
    # Create a UDP datagram socket for the client
    for i in SelfRoutingTable:
        if i["isTargetAndSourceNeighbors"]==True:
            reserve_printer()
            print("[%s] Message sent from Node %d to Node %d" %(repr(time.time()), self_port,int(i["TargetNode"])))
            senderSideSocket.sendto(json.dumps(SelfRoutingTable), (self_ip, int(i["TargetNode"])))
            release_printer()

def receiver_processing():
    global sendToNeighbors
    global firstTimeReceiving
    senderPort = None
    
    def update_table():
        for i in SelfRoutingTable:
            1;
        #print message
        #print SelfRoutingTable
        #print print_table()
    
    while True:
        incomingPacket = None
        try:
            incomingPacket, (senderIp, senderPort) = senderSideSocket.recvfrom(1024)
        except:
            time.sleep(0.01)
        
        # Ignores packets sent from self
        if senderPort == self_port:
            print 1;
        
        # Process table updates according to Bellman-Ford
        elif incomingPacket:
            message = json.loads(incomingPacket)
            #message = incomingPacket
            print("[%s] Message received at Node %d from Node %d" %(repr(time.time()), self_port,senderPort))
            
            #Add any new node to SelfRoutingTable
            
            #Mark a node as existing
            for i in message:
                i["nodeExists"]=False
                for j in SelfRoutingTable:
                    if i["TargetNode"]==j["TargetNode"]:
                        i["nodeExists"]=True
            
            print message
            
            for i in message:
                # Add new node to SelfRoutingTable
                if i["nodeExists"]==False and int(i["TargetNode"])!=self_port:
                    routingTableStructure = {"TargetNode": 0,"SourceNode":0,"Distance":9, "NextHop": None, "isTargetAndSourceNeighbors": False, "nodeExists": None}
                    
                    routingTableStructure["SourceNode"] = self_port
                    routingTableStructure["TargetNode"] = int(i["TargetNode"])
                    routingTableStructure["NextHop"] = int(i["SourceNode"]) 
                    routingTableStructure["nodeExists"] = True
                    SelfRoutingTable.append(routingTableStructure)
            
                    print print_table()
            
            if firstTimeReceiving==True:
                #print firstTimeReceiving
                firstTimeReceiving=False
                send_table_to_neighbors()
            #print SelfRoutingTable
    
initialize_self_table()
print_table()

senderSideSocket = socket(AF_INET, SOCK_DGRAM)
self_ip = gethostname()
senderSideSocket.bind((self_ip, self_port))  
    
    
threadReceiver = threading.Thread(target=receiver_processing)
threadReceiver.start()
if isLastNode == True:
    send_table_to_neighbors()

