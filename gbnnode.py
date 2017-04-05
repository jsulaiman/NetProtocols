import argparse
import select
from socket import *
import sys
import time
#import thread
import threading
import os
import json
# from datetime import datetime

# A list of global variables to be used throughout the GBN program
argList = []  # Argument parser
timerOn = False  # Buffer for ack processing, initialized as 0 to signify unused
readyToPrint = True

# Initialize the base sequence number, next seq number, and the buffer
baseseqnum = 0
nextseqnum = 0
expectedseqnum = 0
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
        time.sleep(0.0001)
        
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
        stopSending = False
        basebuffer=baseseqnum
        
        try:
            while nextseqnum != bufferLength and stopSending == False:
                if nextseqnum < (basebuffer + window_size):
                    reserve_printer()
                    #print "base in send ", baseseqnum
                    #print "next in send", nextseqnum
                    #print "window", window_size
                    print("[%s] packet%d %s sent" % (repr(time.time()), buffer[nextseqnum]["sequence"], buffer[nextseqnum]["data"]))
                    senderSideSocket.sendto(json.dumps(buffer[nextseqnum]), (self_ip, int(peer_port)))
                    release_printer()
                    
                    if(baseseqnum == nextseqnum):
                        #thread.start_new_thread(start_timer, (buffer[nextseqnum]["sequence"],))
                        threadTimer = threading.Thread(target=start_timer,args=(buffer[nextseqnum]["sequence"],))
                        threadTimer.start()
                    nextseqnum = nextseqnum + 1   
                else:
                    stopSending = True
                    print ("in send packet else")
                    return True 
        except:
            print "in send packet expection"
            1;
          
    def process_timeout(pktNum):
        
        reserve_printer()
        print "base after timeout", baseseqnum
        print ("[%s] packet%d timeout" % (repr(time.time()), pktNum)) 
        release_printer()
        nextseqnum=baseseqnum
        send_packets_in_window()
    # Wait for incoming ack for 500msec                    
    
    def start_timer(pktNum):
        # Give the message a bit of time to reach the target
        # time.sleep(0.02)
        global timerOn
        timerOn = True
        t_start = time.time()
        t_end = time.time() + 0.5
        reserve_printer()
        print "in timer %d [%s]" % (pktNum, t_end)
        release_printer()
        while t_start < t_end:
                
                t_start = t_start + .01
                if(timerOn == False):
                    # Reset buffer
                    return True;
        
        timerOn = False
        process_timeout(pktNum)
        return True
        
    
    # Listen for incoming messages and process them            
    def receiver_processing():
        senderPort = None
        global timerOn
        global baseseqnum
        global nextseqnum
        global expectedseqnum
        while True:
            incomingPacket = None
            try:
                incomingPacket, (senderIp, senderPort) = senderSideSocket.recvfrom(1024)
            except:
                time.sleep(0.01)
            
            # Ignores packets sent from self
            if senderPort == self_port:
                1;
                
            elif incomingPacket:
                # try:
                    message = json.loads(incomingPacket)
                    #####print ("in get_message, capturing incoming msg", message)
                    # Check if it is a packet containing acknowledgment of a previously sent packet    

                    # RECEIVER SECTION
                    # Process incoming packet as Receiver
                    if(message["data"] != None and expectedseqnum==message["sequence"]):
                        
                        if emulation_mode == "-d":
                            if ((int(message["sequence"] + 1) % int(emulation_value)) == 0):
                                reserve_printer()
                                print("[%s] packet%d %s discarded" % (repr(time.time()), message["sequence"], message["data"]))
                                release_printer()
                            else:
                                reserve_printer()
                                print("[%s] packet%d %s received" % (repr(time.time()), message["sequence"], message["data"]))
                                release_printer()
                                
                                receivedSequence = message["sequence"]
                                expectedseqnum = message["sequence"] + 1
                                message["data"] = None
                                senderSideSocket.sendto(json.dumps(message), (self_ip, int(peer_port)))
                                reserve_printer()
                                print("[%s] ACK%d sent, expecting packet%s" % (repr(time.time()), receivedSequence, expectedseqnum))
                                release_printer()
                    
                    # SENDER SECTION
                    # Process incoming Ack as Sender
                    else:
                        # Emulate packet loss
                        if emulation_mode == "-d":                        
                            if ((int(message["sequence"]) == 0 or (int(message["sequence"]) % int(emulation_value)) != 0)):
                
                                if((int(message["sequence"])) == baseseqnum): 
                                    timerOn = False
                                    baseseqnum = baseseqnum + 1
                                    reserve_printer()
                                    print("[%s] ACK%d received, window moves to %d" % (repr(time.time()), message["sequence"], baseseqnum))
                                    release_printer()
                                    
                            else:
                                reserve_printer()
                                print("[%s] ACK%d discarded" % (repr(time.time()), message["sequence"]))
                                release_printer()
                # except:
                #    print ("[Exception: Cannot deliver an incoming chat transmission]")
        

    global timerOn
    disableMsg = "no"
    
    #thread.start_new_thread(receiver_processing, ())
    threadReceiver = threading.Thread(target=receiver_processing)
    threadReceiver.start()
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
        bufferLength = bufferLength + 1
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
        




    

