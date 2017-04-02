import argparse
import select
from socket import *
import sys
import time
import thread
import os
import json
from datetime import datetime
import random

# A list of global variables to be used throughout the chat program
argList = []  # Argument parser
userList = []  # Holds user table with online status
userIdList = []  # Holds user ID only
ackBuffer = 0  # Buffer for ack processing, initialized as 0 to signify unused
readyToPrint = True

# Parse a message into the appropriate categories
def parse_keyboard_input(s):
    pkts = []
    a = s.split(' ')
    if len(a) > 3 or a[0] != "send":
        return False
    else:
        pkts = list(a[1])
        return pkts

def reserve_printer():
    global readyToPrint
    
    while readyToPrint == False:
        time.sleep(0.01)
        
    readyToPrint = False
    
def release_printer():
    global readyToPrint
    readyToPrint = True
    
    
# Validate arguments length to not exceed the most arguments that could be handled
def validate_args_length(arg):
    if len(arg) > 6:
        return False
    return True
                
# Launch sender node
def launchNode(self_port, peer_port, window_size, emulation_mode, emulation_value):
    # Create a UDP datagram socket for the client
    senderSideSocket = socket(AF_INET, SOCK_DGRAM)
    self_ip = gethostname()
    senderSideSocket.bind((self_ip, self_port))          
    
    # Send ack to message sender host  
    def send_Ack(myName, tIp, tPort, ackId):
        #####print ("in send_Ack", ackId)
        outjson = { "username": myName, "message": "", "ackFlag": ackId}
        senderSideSocket.sendto(json.dumps(outjson), (tIp, tPort))
    
    # Wait for incoming ack for 500msec                    
    def get_Ack(outjson):
        #Give the message a bit of time to reach the target
        time.sleep(0.02)
        
        global ackBuffer
        t_start = time.time()
        t_end = time.time() + .5
        while t_start < t_end:
                # print(outjson["ackFlag"], "=", ackBuffer)
                
                t_start = t_start + .01
                #####print("in get_Ack, ackBuffer: ",ackBuffer, " ackFlag:",outjson["ackFlag"])
                if(ackBuffer == (outjson["ackFlag"]*-1)):
                    # Reset buffer
                    ackBuffer = 0
                    return True
        ackBuffer = 0
        return False
    
    # Listen for incoming messages and process them            
    def receiver_processing():
        senderPort = None
        global ackBuffer
        global baseseqnum
        global nextseqnum
        while True:
            incomingPacket = None
            try:
                incomingPacket, (senderIp, senderPort) = senderSideSocket.recvfrom(1024)
            except:
                time.sleep(0.01)
            
            #Ignores packets sent from self
            if senderPort == self_port:
                1;
                
            elif incomingPacket:
                #try:
                    message = json.loads(incomingPacket)
                    #####print ("in get_message, capturing incoming msg", message)
                    # Check if it is a packet containing acknowledgment of a previously sent packet    

                    
                    
                    
                    # Process incoming packet as Receiver
                    if(message["data"] != None):
                        reserve_printer()
                        print("[%s] packet%d %s received" %(time.time(), message["sequence"], message["data"]) )
                        release_printer()
                        
                        receivedSequence = message["sequence"]
                        message["sequence"]=message["sequence"]+1
                        message["data"]=None
                        senderSideSocket.sendto(json.dumps(message), (self_ip, int(peer_port)))
                        reserve_printer()
                        print("[%s] ACK packet%d sent, expecting packet%s" %(time.time(), receivedSequence, message["sequence"]) )
                        release_printer()
                        # print ackBuffer
                    # Process incoming Ack as Sender
                    else:
                        #Emulate packet loss
                        if emulation_mode == "-d":
                            print("-d debug")
                        w=1
                        reserve_printer()
                        #print("debugACK")
                        print("[%s] ACK%d received, window moves to %d" %(time.time(), message["sequence"],w))
                        release_printer()
                #except:
                #    print ("[Exception: Cannot deliver an incoming chat transmission]")
        

    # Initialize the base sequence number, next seq number, and the buffer
    segId = 0
    baseseqnum = 0
    nextseqnum = 0
    buffer = []
    
    global ackBuffer
    disableMsg = "no"
    
    thread.start_new_thread(receiver_processing, ())
    
    print("node>"),
    # Listen to keyboard input and process        
    keyboardInput = raw_input().strip()
    
    packets = parse_keyboard_input(keyboardInput)
    
    if packets == False:
        print("Unknown command.")
        sys.exit()
    
    # Put all packets with sequence numbers in the buffer
    for i in packets:
        packetWithHeader = {"sequence": segId, "data": i}
        segId = segId+1
        buffer.append(packetWithHeader)
    
    while nextseqnum != segId:
        if nextseqnum < (baseseqnum+window_size):
            senderSideSocket.sendto(json.dumps(buffer[nextseqnum]), (self_ip, int(peer_port)))
            reserve_printer()
            print("[%s] packet%d %s sent" %(time.time(), buffer[nextseqnum]["sequence"], buffer[nextseqnum]["data"]) )
            release_printer()
            #if baseseqnum == nextseqnum:
        
            nextseqnum = nextseqnum+1
                    
    
###############################################################
# Command Line Processing
#
#
#
###############################################################

   
# Read all arguments into a list, with error handling
for eachArg in sys.argv:   
        argList.append(eachArg)
    
    # error handling
try:
        selfPort = int(argList[1])
        peerPort = int(argList[2])
        windowSize = int(argList[3])
        emulationMode = argList[4]
        emulationValue = argList[5]
        
except:
        print ("Invalid client arguments, please invoke clients following this sample convention: $ python gbnnode.py <self-port> <peer-port> <window-size> [ -d <value-of-n> j -p <value-of-p>]")
        sys.exit(1)
    
if validate_args_length(argList) == False:
        print ("Too many command line arguments. Please check your arguments for accuracy. Consult UDP Chat README for help")
        sys.exit(1)

elif emulationMode != "-d" and emulationMode != "-p":
        print ("Please invoke either deterministic mode (-d) or probabilistic mode (-p)")
        exit
        
else:
    launchNode(selfPort, peerPort, windowSize, emulationMode, emulationValue)
        




    

