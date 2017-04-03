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
#from concurrent.futures import process

# A list of global variables to be used throughout the chat program
argList = []  # Argument parser
userList = []  # Holds user table with online status
userIdList = []  # Holds user ID only
timerOn = False  # Buffer for ack processing, initialized as 0 to signify unused
readyToPrint = True
# Initialize the base sequence number, next seq number, and the buffer

baseseqnum = 0
nextseqnum = 0
buffer = []
    
    
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

    bufferLength = 0
    
    # Create a UDP datagram socket for the client
    senderSideSocket = socket(AF_INET, SOCK_DGRAM)
    self_ip = gethostname()
    senderSideSocket.bind((self_ip, self_port))          
    
    
    def send_packets_in_window():
        global baseseqnum
        global nextseqnum
        print "base", baseseqnum
        print "next", nextseqnum
        
        while nextseqnum != bufferLength:
            if nextseqnum < (baseseqnum+window_size):
                senderSideSocket.sendto(json.dumps(buffer[nextseqnum]), (self_ip, int(peer_port)))
                reserve_printer()
                print("[%s] packet%d %s sent" %(time.time(), buffer[nextseqnum]["sequence"], buffer[nextseqnum]["data"]) )
                release_printer()
                
                if(baseseqnum==nextseqnum):
                    thread.start_new_thread(start_timer,())
            
                nextseqnum = nextseqnum+1    
        
        
    def process_timeout():
        print "in timeout"
        processedPacketId = baseseqnum
        lastPacket = nextseqnum    
        send_packets_in_window()
        start_timer()
    # Wait for incoming ack for 500msec                    
    
    def start_timer():
        #Give the message a bit of time to reach the target
        time.sleep(0.02)
        global timerOn
        timerOn = True
        t_start = time.time()
        t_end = time.time() + .5
        while t_start < t_end:
                print "in timer", time.time(), t_start, t_end
                # print(outjson["ackFlag"], "=", timerOn)
                
                t_start = t_start + .01
                #####print("in start_timer, timerOn: ",timerOn, " ackFlag:",outjson["ackFlag"])
                if(timerOn == True):
                    # Reset buffer
                    1;
                else:
                    return True;
        
        process_timeout()
        timerOn = False
    
    # Listen for incoming messages and process them            
    def receiver_processing():
        senderPort = None
        global timerOn
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

                    # RECEIVER SECTION
                    # Process incoming packet as Receiver
                    if(message["data"] != None):
                        
                        if emulation_mode == "-d":
                            if ((int(message["sequence"]+1) % int(emulation_value)) == 0):
                                reserve_printer()
                                print("[%s] packet%d %s discarded" %(time.time(), message["sequence"], message["data"]) )
                                release_printer()
                            else:
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
                    
                    # SENDER SECTION
                    # Process incoming Ack as Sender
                    else:
                        #Emulate packet loss
                        if emulation_mode == "-d":
                            if ((int(message["sequence"]) % int(emulation_value)) == 0):
                                reserve_printer()
                                print("[%s] ACK%d discarded" %(time.time(), message["sequence"]))
                                release_printer()
                        
                            else:
                                
                                if((int(message["sequence"])-1)==baseseqnum): 
                                    timerOn=False
                                    reserve_printer()
                                    print("[%s] ACK%d received, window moves to %d" %(time.time(), message["sequence"],message["sequence"]))
                                    release_printer()
                                    baseseqnum=baseseqnum+1
                #except:
                #    print ("[Exception: Cannot deliver an incoming chat transmission]")
        

    global timerOn
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
        packetWithHeader = {"sequence": bufferLength, "data": i}
        bufferLength = bufferLength+1
        buffer.append(packetWithHeader)
    
    send_packets_in_window()

                    
    
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
        




    

