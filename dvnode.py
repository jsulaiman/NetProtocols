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
neighborList=[]
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
            routingTableStructure = {"TargetNode": 0,"SourceNode":0,"Distance":9, "NextHop": None, "isTargetAndSourceNeighbors": True, "nodeExists": None, "DistToNextHop": 0}
            
            routingTableStructure["SourceNode"] = self_port
            routingTableStructure["TargetNode"] = int(i)
            routingTableStructure["nodeExists"] = True
            SelfRoutingTable.append(routingTableStructure)
            neighborList.append(routingTableStructure["TargetNode"])
    
    count = 0
    for i in SelfRoutingTable:
        i["Distance"]=round(float(neighborDistance[count]),2)
        count+=1

def print_table():
    #print SelfRoutingTable
    print("[%s] Node %d Routing Table " % (repr(time.time()), self_port))
    
    for i in SelfRoutingTable:
        if i["NextHop"]==None:
            print " - (%s) -> Node %d" %(format(i["Distance"],".1f"),i["TargetNode"])
        else:
            print " - (%s) -> Node %d; Next hop -> Node %d" %(format(i["Distance"],".1f"),i["TargetNode"],i["NextHop"])

def send_table_to_neighbors():
    # Create a UDP datagram socket for the client
    for i in SelfRoutingTable:
        if i["isTargetAndSourceNeighbors"]==True:
            reserve_printer()
            print("[%s] Message sent from Node %d to Node %d" %(repr(time.time()), self_port,int(i["TargetNode"])))
            senderSideSocket.sendto(json.dumps(SelfRoutingTable), (self_ip, int(i["TargetNode"])))
            release_printer()

def routing_table_receiver_processing():
    global sendToNeighbors
    global firstTimeReceiving
    senderPort = None
    NextHopIsNeighbor=False

    while True:
        incomingPacket = None
        try:
            incomingPacket, (senderIp, senderPort) = senderSideSocket.recvfrom(1024)
        except:
            time.sleep(0.01)
        
        # Ignores packets sent from self
        if senderPort == self_port:
            1;
        
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
                    if j["TargetNode"]==i["SourceNode"]and i["TargetNode"]!=i["SourceNode"]:
                        thisNeighborDistance=j["Distance"]
                        for k in neighborList:
                            if i["TargetNode"]==j["SourceNode"]:
                                if i["NextHop"]!=None and i["NextHop"]==k:
                                    NextHopIsNeighbor=True
                                    NextHopNeighbor=i["NextHop"]
                                    #print "NextHop: ", NextHopNeighbor
            #print message
            
            for i in message:
                if int(i["TargetNode"])==self_port:
                    1;
                # Add new node to SelfRoutingTable, set distance to maximum
                elif i["nodeExists"]==False:
                    
                    routingTableStructure = {"TargetNode": 0,"SourceNode":0,"Distance":9, "NextHop": None, "isTargetAndSourceNeighbors": False, "nodeExists": None, "DistToNextHop": 0}
                    
                    routingTableStructure["SourceNode"] = self_port
                    routingTableStructure["TargetNode"] = int(i["TargetNode"])
                    routingTableStructure["NextHop"] = int(i["SourceNode"]) 
                    routingTableStructure["nodeExists"] = True
                    routingTableStructure["DistToNextHop"]=thisNeighborDistance
                    SelfRoutingTable.append(routingTableStructure)
            
                    print_table()
                    
                # Start Bellman-Ford algorithm
                elif i["nodeExists"]==True:
                    #===========================================================
                    # for j in SelfRoutingTable:
                    #     if i["SourceNode"]==j["TargetNode"] and i["TargetNode"]==j["SourceNode"]:
                    #     currentNeighborDistance = j["Distance"]
                    #===========================================================
                    for j in SelfRoutingTable:
                        if i["TargetNode"]==j["TargetNode"]:
                            if (i["Distance"]+thisNeighborDistance)<j["Distance"]:
                                #print ("routing source:%d ,old distance: %f, new distance to %d: %f , neighbor's distance to %d: %f, neighbor's next hop:%s" 
                                #       %(i["SourceNode"],j["Distance"],j["TargetNode"],i["Distance"]+thisNeighborDistance,j["SourceNode"],thisNeighborDistance,str(i["NextHop"])))
                                j["Distance"]=i["Distance"]+thisNeighborDistance
                                
                                
                                if NextHopIsNeighbor==True:
                                    j["NextHop"]=NextHopNeighbor
                                
                                else:
                                    j["NextHop"]=i["SourceNode"]
                                print_table()
                                send_table_to_neighbors()
                        
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
    
    
threadReceiver = threading.Thread(target=routing_table_receiver_processing)
threadReceiver.start()
if isLastNode == True:
    send_table_to_neighbors()

