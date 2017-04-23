import argparse
import select
from socket import *
import sys
import time
import threading
import os
import json
import random
from platform import release

# A list of global variables to be used throughout the GBN program
argList = []  # Argument parser
timerOn = False  # Initialize Timer as False
readyToPrint = True #Printer reserver, set as ready To Print
windowSize=5
window_size=5
emulationMode="-p"

# Initialize the base sequence number, next seq number, the buffer, and the counters
baseseqnum = 0
nextseqnum = 0
expectedseqnum = 0
bufferLength = 0
stopSending = False
lostPacketCounter = 0
packetCount = 0
AckCount = 0
totalWeightCount=0
lostWeightCount=0
buffer = []
clearToSend=True


# A list of global variables to be used throughout the DV program
argList = []  # Argument parser
readyToPrint = True
isLastNode = False
sendToNeighbors=False
SelfRoutingTable =[]
neighborList=[]
receiverList=[]
senderNodeList=[]
neighborDistance = []
firstTimeReceiving = True

# Read all arguments into a list, with error handling
for eachArg in sys.argv:   
        argList.append(eachArg)

self_port = int(argList[1])
argList.pop(0);argList.pop(0)

if argList[0]!="receive":
    print ("Please follow the following argument format: cnnode <local-port> receive <neighbor1-port> <loss-rate-1> <neighbor2-port> <loss-rate-2> ... <neighborM-port> <loss-rate-M> send <neighbor(M+1)-port> <neighbor(M+2)-port> ... <neighborN-port> [last]")
    sys.exit()
    
argList.pop(0)

#print argList
receiveSection=True

for i in argList:
    if i != "send" and receiveSection==True:
            receiverList.append(i)

    elif i == "send":
        receiveSection=False
    elif receiveSection==False:
        senderNodeList.append(i)

neighborProbDistance = receiverList[1::2]
neighborNodes = receiverList[0::2]


for i in neighborProbDistance:
    #print "neighborProbDistance: %s" %(neighborProbDistance)
    neighborDistance.append(0.00)
    #print "neighborDistance: %s" %(neighborDistance)

#===============================================================================
# print receiverList
# print neighborDistance
# print neighborNodes
# print senderNodeList
#===============================================================================

if len(senderNodeList)!=0:
    if senderNodeList[len(senderNodeList)-1]=="last":
        isLastNode = True
        firstTimeReceiving=False
        senderNodeList.pop()
        
if len(neighborNodes) > 16:
    print ("Too many nodes (maximum 16")
    sys.exit()

def start_timer(peer_port):
    # Give the message a bit of time to reach the target
    global timerOn
    timerOn = True
    t_start = time.time()
    t_end = time.time() + 0.5

    while (t_start < t_end and timerOn == True):
            #reserve_printer()
            
            #print "packet%d is in timer: [%s], stop at [%s]" % (pktNum, t_start,t_end)
            #release_printer()
            t_start = t_start + .01
            time.sleep(0.01)
            #if(timerOn == False):
                # Reset buffer
            #    return True;
    
    #Timeout if not interrupted by timerOn=False mid waiting
    if timerOn==True:
        timerOn = False
        process_timeout(peer_port)

def send_all_packets_in_window(peer_port):
        global baseseqnum
        global nextseqnum
        global stopSending
        global packetCount
        global totalWeightCount
        basebuffer=baseseqnum
        endWindow=basebuffer+window_size
        
        #if basebuffer < bufferLength:
            #print ("base:%d, next:%d" %(baseseqnum,nextseqnum))
        timerOn=False
        threadTimer = threading.Thread(target=start_timer,args=(peer_port,))
        threadTimer.start()
         
        while ((basebuffer < endWindow) and (basebuffer < bufferLength)):
                if buffer[basebuffer]["Acked"]!="yes":
                    buffer[basebuffer]["Acked"]="no"
                # To let ACK received message displayed first in printer
                time.sleep(0.006)
                #reserve_printer()
                #print("[%s] packet%d %s sent to %s" % (repr(time.time()), buffer[basebuffer]["sequence"], buffer[basebuffer]["data"], peer_port))
                senderSideSocket.sendto(json.dumps(buffer[basebuffer]), (self_ip, int(peer_port)))
                #release_printer()
                totalWeightCount+=1
                packetCount=packetCount+1
                basebuffer = basebuffer+1  
    
def send_packets_in_window(peer_port):
    global baseseqnum
    global nextseqnum
    global stopSending
    global timerOn
    global window_size
    global totalWeightCount
    endOfWindow=baseseqnum+window_size
    
    #print ("in send_packets. next: %d, base: %d, window: %d, bufferLength: %d" %(nextseqnum,baseseqnum,window_size,bufferLength))
    while ((nextseqnum < bufferLength) and (nextseqnum < endOfWindow) ):
            #Adding if to defuse list index out of range bug
            if buffer[nextseqnum]["Acked"]=="":
                buffer[nextseqnum]["Acked"]="no"
                #print buffer[nextseqnum]
                
                #To let ACK message received display first in printer
                time.sleep(0.006)
                #reserve_printer()
                #print("[%s] packet%d %s sent to %s" % (repr(time.time()), buffer[nextseqnum]["sequence"], buffer[nextseqnum]["data"], peer_port))
                #release_printer()
                senderSideSocket.sendto(json.dumps(buffer[nextseqnum]), (self_ip, int(peer_port)))
                
                #Fixing program not terminating due to timer not timing out bug
                if(buffer[nextseqnum]["Acked"]=="no"):
                    timerOn=False
                    threadTimer = threading.Thread(target=start_timer,args=(peer_port,))
                    threadTimer.start()
            #Restart timer if it is already on
            if(buffer[baseseqnum]["Acked"]=="no"):
                timerOn=False
                threadTimer = threading.Thread(target=start_timer,args=(peer_port,))
                threadTimer.start()
            #if nextseqnum < bufferLength:   
            nextseqnum = nextseqnum + 1 
            totalWeightCount+=1 
                    #time.sleep(0.01)
            #else:
                
                #print ("nextseqnum is equal to bufferlength")
            #    timerOn = False

def process_timeout(port_to_send_timer):
    global baseseqnum
    global bufferLength
    global lostWeightCount
    
    # Prevent timeout messages on out of boundary packets
    if baseseqnum<(bufferLength-1):
        #reserve_printer()
        #print "base after timeout", baseseqnum
        #print ("[%s] packet%d timeout" % (repr(time.time()), baseseqnum)) 
        #release_printer()
        lostWeightCount+=1
    
        send_all_packets_in_window(port_to_send_timer)          
    
        
def launchNode(self_port, peer_port, window_size, emulation_mode, emulation_value,node_type):
    
    global clearToSend
    # Create a UDP datagram socket for the client
    #senderSideSocket = socket(AF_INET, SOCK_DGRAM)
    #self_ip = gethostname()
    #senderSideSocket.bind((self_ip, self_port))          
    
    def process_send():
        global timerOn
        global bufferLength
        global lostPacketCounter
        global packetCount
        #thread.start_new_thread(routing_table_receiver_processing, ())
        #threadReceiver = threading.Thread(target=probe_receiver_processing)
        #threadReceiver.start()
        #print("node>"),
        # Listen to keyboard input and process        
        #keyboardInput = raw_input().strip()
        packets = list("abcde")

        
        # Put all packets with sequence numbers in the buffer
        for i in packets:
            packetWithHeader = {"sequence": bufferLength, "data": i, "fin": "", "Acked": ""}
            bufferLength = bufferLength + 1
            buffer.append(packetWithHeader)
        
        #time.sleep(0.5)
        packetCount = bufferLength
        buffer[(bufferLength-1)]["fin"]= "yes"
        
        #Add extra spaces after buffer to capture out of order packets
        extraSpaceCounter = 0
        while extraSpaceCounter < 15:
            packetWithHeader = {"sequence": bufferLength, "data": i, "fin": "", "Acked": ""}
            buffer.append(packetWithHeader)
            extraSpaceCounter+=1
        
        firstThread = threading.Thread(target=send_packets_in_window,args=(peer_port,))
        firstThread.start()
        
        #while stopSending == False:
        #    time.sleep(0.01)
            
        #firstThread.join()
        
    if node_type=="prober":
        process_send()            
    

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
            routingTableStructure = {"TargetNode": 0,"SourceNode":0,"Distance":9, "NextHop": None, "isTargetAndSourceNeighbors": True, "nodeExists": None, "DistToNextHop": 0, "TotalPackets":0, "TotalDroppedPackets":0}
            
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
            print " - (%s) -> Node %d" %(format(i["Distance"],".2f"),i["TargetNode"])
        else:
            print " - (%s) -> Node %d; Next hop -> Node %d" %(format(i["Distance"],".2f"),i["TargetNode"],i["NextHop"])
                        
def send_probe_packets():
    nodeType="prober"
    emulationValue = 0
    global clearToSend
    #capture loss rate
    for i in senderNodeList:
        clearToSend=False
        peerPort = i
        reserve_printer()
        print ("probing %s" %peerPort)
        release_printer()
        launchNode(self_port, peerPort, windowSize, emulationMode, emulationValue, nodeType)
        # Complete processing loss rate for 1 node first
        #while clearToSend==False:
        #    print ("in waiting")
        #    time.sleep(0.05)
    #update cost
    
def send_table_to_neighbors():
    # Create a UDP datagram socket for the client
    for i in SelfRoutingTable:
        if i["isTargetAndSourceNeighbors"]==True:
            reserve_printer()
            print("[%s] Message sent from Node %d to Node %d" %(repr(time.time()), self_port,int(i["TargetNode"])))
            senderSideSocket.sendto(json.dumps(SelfRoutingTable), (self_ip, int(i["TargetNode"])))
            release_printer()

# Listen for incoming messages and process them            
def probe_receiver_processing(probe_message,destination_port):
    senderPort = None
    emulation_mode = "-p"
    emulation_value = float(0.00) #Initialize loss rate to 0
    detPacketCounter = 0
    newWeightCost=0
    global timerOn
    global baseseqnum
    global nextseqnum
    global expectedseqnum
    global bufferLength
    global lostPacketCounter
    global packetCount
    global AckCount
    global buffer
    global totalWeightCount
    global lostWeightCount
    
    #Import receiver nodes and weights
    global neighborProbDistance
    global neighborNodes
    global SelfRoutingTable
    # Global references to allow for buffer reset
    global stopSending
    global bufferLength
    
    detPacketCounter=0
    
    message = probe_message
    #print ("in get_message, capturing incoming msg", message)
    # Check if it is a packet containing acknowledgment of a previously sent packet    
    
    ReceiverProbabilisticallyDropped = False
    deterministicallyDropped = False
    deterministicValue = 9999999999999999999 #Ensure that modulo of this number is always going to be a non zero
        
    # RECEIVER SECTION
    # Process incoming packet as Receiver
    if (message["data"] != None):
        detPacketCounter=detPacketCounter+1
        
        #look up node weight by destination_port
        count = 0
        while count < len(neighborNodes):
            if int(neighborNodes[count])==int(destination_port):
                emulation_value=float(neighborProbDistance[count])
                #print "Node: %s, weight: %s, emul_value: %.5f"%(neighborNodes[count],float(neighborProbDistance[count]),round(emulation_value,3))
            count+=1
        
        if emulation_mode == "-p":
            emulProb=float(emulation_value)
            if emulProb > 0:
                random_number = float(random.random())
                if random_number < emulProb:
                    ReceiverProbabilisticallyDropped = True
                    #print ("random number: %s, emulProb: %s" %(random_number,emulProb))
        elif emulation_mode == "-d":
            deterministicValue = emulation_value
            if((int(detPacketCounter) % int(deterministicValue)) == 0):
                deterministicallyDropped = True
        
        if((deterministicallyDropped==True or ReceiverProbabilisticallyDropped==True) and message["fin"]!="printSummary" and message["fin"]!="yes"):
            if(expectedseqnum==message["sequence"]): 
                #reserve_printer()
                #print ("modulo: %d, prob drop: %s" %((int(message["sequence"] + 1) % int(deterministicValue)),probabilisticallyDropped))
                #print("[%s] packet%d %s discarded from %s. Fin tag is: %s" %(repr(time.time()), message["sequence"], message["data"],destination_port,message["fin"]))
                #release_printer()
                lostPacketCounter=lostPacketCounter+1
                packetCount=packetCount+1    
        else:
            if(expectedseqnum==message["sequence"]): 
                #print ("Counter: %d. Modulo: %d " %(detPacketCounter,(int(detPacketCounter) % int(deterministicValue))))
                    if message["fin"]== "yes":
                        lastpacketnum=message["data"]
                        message["data"] = None
                        message["fin"]="printSummary"
                        expectedseqnum=message["sequence"] + 1
                        packetCount=packetCount+1
                        senderSideSocket.sendto(json.dumps(message), (self_ip, int(destination_port)))

                        #reserve_printer()
                        #print("[%s] packet%d %s received" % (repr(time.time()), message["sequence"], lastpacketnum))
                        #print("[%s] ACK%d sent, expecting packet%s" % (repr(time.time()), message["sequence"], expectedseqnum))
                        #release_printer()
                        
                        time.sleep(1)
                        #reserve_printer()
                        #print ("[Summary] %d/%d packets dropped, loss rate = %s" %(lostPacketCounter,packetCount,format(float(lostPacketCounter)/packetCount,".2f")))
                        #print ("Link to %d: %d packets sent, %d packets lost, loss rate %f" %(destination_port,packetCount,lostPacketCounter,format(float(lostPacketCounter)/packetCount,".2f")))
                        #release_printer()
                        
                        emulationValue = float(lostPacketCounter)/packetCount
                        #print ("new node weight: %s" %format(emulationValue,".2f"))
                        print ("Link to %d: %d packets sent, %d packets lost, loss rate %s" %(destination_port,packetCount,lostPacketCounter,format(float(lostPacketCounter)/packetCount,".2f")))
                        
                        #Update Self Routing Table with the new counts for the destination node
                        
                        for i in SelfRoutingTable:
                            if i["TargetNode"]==int(destination_port):
                                #print i["TargetNode"]
                                i["TotalPackets"]=i["TotalPackets"]+packetCount
                                i["TotalDroppedPackets"]=i["TotalDroppedPackets"]+lostPacketCounter
                                i["Distance"]=round(float(i["TotalDroppedPackets"])/float(i["TotalPackets"]),2)
                                #print i["Distance"]
                        
                        send_table_to_neighbors()
                        print_table()
                        #clearToSend = True
                        nodeType = "listener"
                        expectedseqnum = 0
                        stopSending = False
                        lostPacketCounter = 0
                        packetCount = 0
                        #AckCount = 0

                        #launchNode(self_port, destination_port, windowSize, emulationMode, emulationValue, nodeType)
                        #process_send()

       
                    #Send ACK
                    else:
                        #reserve_printer()
                        #print ("detvalue: %d, modulo: %d, prob drop: %s" %(int(deterministicValue),(int(message["sequence"] + 1) % int(deterministicValue)),probabilisticallyDropped))
                        #print("[%s] packet%d %s received" % (repr(time.time()), message["sequence"], message["data"]))
                        #release_printer()
                        packetCount=packetCount+1
            
                        receivedSequence = message["sequence"]
                        expectedseqnum = message["sequence"] + 1
                        message["data"] = None
                        senderSideSocket.sendto(json.dumps(message), (self_ip, int(destination_port)))
                        #reserve_printer()
                        #print("[%s] ACK%d sent, expecting packet%s" % (repr(time.time()), receivedSequence, expectedseqnum))
                        #release_printer()
            #Ignore out of expectation packets
            elif (message["sequence"]>expectedseqnum): 
                1;
            else:
                #reserve_printer()
                #print ("detvalue: %d, modulo: %d, prob drop: %s" %(int(deterministicValue),(int(message["sequence"] + 1) % int(deterministicValue)),probabilisticallyDropped))
                #print("[%s] packet%d %s received" % (repr(time.time()), message["sequence"], message["data"]))
                #release_printer()
                packetCount=packetCount+1
    
                receivedSequence = message["sequence"]
                message["data"] = None
                senderSideSocket.sendto(json.dumps(message), (self_ip, int(destination_port)))
                #reserve_printer()
                #print("[%s] ACK%d sent to %s, expecting packet%s" % (repr(time.time()), receivedSequence, destination_port, expectedseqnum))
                #release_printer()
    
    # SENDER SECTION
    # Process incoming Ack as Sender
    else:
        detPacketCounter=detPacketCounter+1
        # Process ACK, move window as appropriate
        if emulation_mode == "-p":
            emulProb=float(emulation_value)
            if emulProb > 0:
                random_number = float(random.random())
                if random_number < emulProb:
                    sendProbabilisticallyDropped = True
                
        if emulation_mode == "-d":
            deterministicValue = emulation_value
            if((int(detPacketCounter) % int(deterministicValue)) == 0):
                deterministicallyDropped = True
        
        #Never drop ACKs
        sendProbabilisticallyDropped = False
        if (emulation_mode == "-d" or emulation_mode == "-p"):                        
            if message["fin"]== "printSummary":
                # Process cummulative ACKs
                if((int(message["sequence"])) > baseseqnum and baseseqnum!=0):
                    timerOn = False
                    AckGap = (int(message["sequence"]) - baseseqnum)
                    if baseseqnum < bufferLength:       
                        #Acknowledge all packets before this current Cummulative ACK
                        while (AckGap != 0):
                            if buffer[baseseqnum]["Acked"]=="no":
                                buffer[(baseseqnum-AckGap)]["Acked"]="yes"
                                #timerOn=False
                                AckGap = AckGap - 1
                                baseseqnum = baseseqnum + 1
                                #reserve_printer()
                                #print("[%s] ACK%d received, window moves to %d" % (repr(time.time()), (baseseqnum-AckGap), (baseseqnum-AckGap+1)))
                                #release_printer()
                                AckCount=AckCount+1
                        #Now base is current
                
                if buffer[baseseqnum]["Acked"]=="no":
                    buffer[baseseqnum]["Acked"]="yes"
                    baseseqnum = baseseqnum + 1
                    AckCount=AckCount+1
                    timerOn = False
                    time.sleep(0.006)
                    #reserve_printer()
                    #print("[%s] ACK%d received, window moves to %d" % (repr(time.time()), message["sequence"], baseseqnum))
                    #release_printer()
                    # Turn off timer, let remaining incoming ACKs printed first
                newWeightCost=float(lostWeightCount/totalWeightCount)
                time.sleep(1)
                reserve_printer()
                print ("[Summary] %d/%d packets discarded, loss rate = %s" %(lostPacketCounter,AckCount,format(float(lostPacketCounter)/AckCount,".2f")))
                #print ("Link to %d: %d packets sent, %d packets lost, loss rate %f" %(destination_port,totalWeightCount,lostWeightCount,float(lostWeightCount/totalWeightCount)))
                #release_printer()
                
                clearToSend=True
                emulationValue = 0
                nodeType = "prober"
                baseseqnum = 0
                nextseqnum = 0
                expectedseqnum = 0
                bufferLength = 0
                stopSending = False
                lostPacketCounter = 0
                packetCount = 0
                AckCount = 0
                totalWeightCount=0
                lostWeightCount=0
                buffer = []
                timerOn = False
                launchNode(self_port, destination_port, windowSize, emulationMode, emulationValue, nodeType)
                #process_send()
                    
            # Emulate packet loss
            elif ((int(message["sequence"]) != 0) and (deterministicallyDropped==True or sendProbabilisticallyDropped==True)):
                #reserve_printer()
                #print("[%s] ACK%d discarded" % (repr(time.time()), message["sequence"]))
                #release_printer()
                #lostPacketCounter=lostPacketCounter+1
                #packetCount=packetCount+1
                #AckCount=AckCount+1
                1;
            elif (deterministicallyDropped==False or sendProbabilisticallyDropped == False):
                #print "ACK received is %d, Next is: %d, base is: %d" %(message["sequence"],nextseqnum,baseseqnum)
                if((int(message["sequence"])) == baseseqnum and buffer[baseseqnum]["Acked"]!="yes"): 
                    buffer[baseseqnum]["Acked"]="yes"
                    timerOn = False
                    baseseqnum = baseseqnum + 1
                    #reserve_printer()
                    #print("[%s] ACK%d received, window moves to %d" % (repr(time.time()), message["sequence"], baseseqnum))
                    #release_printer()
                    
                    #Allow print messages
                    time.sleep(0.006)
                    if baseseqnum < bufferLength:
                        #Timer restart with new window's packets sent
                        if buffer[baseseqnum]["Acked"]=="":
                            timerOn=False
                            threadTimer = threading.Thread(target=start_timer,args=(destination_port,))
                            threadTimer.start()
                            send_packets_in_window(destination_port)
                        # If first packet is already on it's way but not ACKed, restart timer
                        elif buffer[baseseqnum]["Acked"]=="no":
                            timerOn=False
                            threadTimer = threading.Thread(target=start_timer,args=(destination_port,))
                            threadTimer.start()
                    
                    #time.sleep(0.01)
                    #packetCount=packetCount+1
                    AckCount=AckCount+1
                # Process cummulative ACKs
                elif((int(message["sequence"])) > baseseqnum and baseseqnum!=0):
                    timerOn = False
                    AckGap = (int(message["sequence"]) - baseseqnum)
                    
                    if baseseqnum < bufferLength:       
                        #Acknowledge all packets before this current Cummulative ACK
                        while (AckGap != 0):
                            buffer[(baseseqnum-AckGap)]["Acked"]="yes"
                            #timerOn=False
                            AckGap = AckGap - 1
                            baseseqnum = baseseqnum + 1
                            #reserve_printer()
                            #print("[%s] ACK%d received, window moves to %d" % (repr(time.time()), (baseseqnum-AckGap), (baseseqnum-AckGap+1)))
                            #release_printer()
                            AckCount=AckCount+1
                        #Now base is current
                        if buffer[baseseqnum]["Acked"]!="":
                            timerOn=False
                            threadTimer = threading.Thread(target=start_timer,args=(destination_port,))
                            threadTimer.start()
                            send_packets_in_window(destination_port)
                        elif buffer[baseseqnum]["Acked"]=="no":
                            timerOn=False
                            threadTimer = threading.Thread(target=start_timer,args=(destination_port,))
                            threadTimer.start()


        else:
            print ("else in Ack")

def five_seconds_DV_update():
    send_table_to_neighbors()
    while True:
        time.sleep(5)
        send_table_to_neighbors()
    
def routing_table_receiver_processing():
    #GBN Variables
    senderPort = None
    detPacketCounter = 0
    global timerOn
    global baseseqnum
    global nextseqnum
    global expectedseqnum
    global bufferLength
    global lostPacketCounter
    global packetCount
    global AckCount
    global buffer
    
    # Global references to allow for buffer reset
    global stopSending
    global bufferLength
    
    detPacketCounter=0
        
    global sendToNeighbors
    global firstTimeReceiving
    NextHopIsNeighbor=False
    thisNeighborDistance=0

    while True:
        #print "waiting"
        incomingPacket = None
        try:
            incomingPacket, (senderIp, senderPort) = senderSideSocket.recvfrom(1024)
        except:
            
            time.sleep(0.01)
        
        # Ignores packets sent from self
        if senderPort == self_port or senderPort == None:
            #print "In check:", senderPort
            1;
        
        
        elif incomingPacket:
            message = json.loads(incomingPacket)
            #message = incomingPacket
            #print message
            
            # Process table updates according to Bellman-Ford
            if type(message) is list:
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
                        routingTableStructure = {"TargetNode": 0,"SourceNode":0,"Distance":9, "NextHop": None, "isTargetAndSourceNeighbors": True, "nodeExists": None, "DistToNextHop": 0, "TotalPackets":0, "TotalDroppedPackets":0}
                        #routingTableStructure = {"TargetNode": 0,"SourceNode":0,"Distance":9, "NextHop": None, "isTargetAndSourceNeighbors": False, "nodeExists": None, "DistToNextHop": 0}
                        
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

                    threadReceiver = threading.Thread(target=five_seconds_DV_update)
                    threadReceiver.start()
                    
                    #send probes after the network becomes ready
                    threadReceiver = threading.Thread(target=send_probe_packets)
                    threadReceiver.start()
                #print SelfRoutingTable
            else:
                #print "probe receiving on"
                probe_receiver_processing(message,senderPort)
    
initialize_self_table()
print_table()

senderSideSocket = socket(AF_INET, SOCK_DGRAM)
self_ip = gethostname()
senderSideSocket.bind((self_ip, self_port))  
    
    
threadReceiver = threading.Thread(target=routing_table_receiver_processing)
threadReceiver.start()
if isLastNode == True:
    send_table_to_neighbors()

