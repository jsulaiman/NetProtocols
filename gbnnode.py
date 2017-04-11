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
timerOn = False  # Buffer for ack processing, initialized as 0 to signify unused
readyToPrint = True

# Initialize the base sequence number, next seq number, and the buffer
baseseqnum = 0
nextseqnum = 0
expectedseqnum = 0
bufferLength = 0
stopSending = False
lostPacketCounter = 0
packetCount = 0
AckCount = 0
timerRestart = "no"
buffer = []
timerInterrupt = "off"

    
    
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
    
    # Create a UDP datagram socket for the client
    senderSideSocket = socket(AF_INET, SOCK_DGRAM)
    self_ip = gethostname()
    senderSideSocket.bind((self_ip, self_port))          
    
    def send_all_packets_in_window():
        global baseseqnum
        global nextseqnum
        global stopSending
        global packetCount
        basebuffer=baseseqnum
        endWindow=basebuffer+window_size
        
        if basebuffer < bufferLength:
            #print ("base:%d, next:%d" %(baseseqnum,nextseqnum))
            threadTimer = threading.Thread(target=start_timer,args=(buffer[basebuffer]["sequence"],))
            threadTimer.start()
         
        while ((basebuffer < endWindow) and (basebuffer < bufferLength)):
                if buffer[basebuffer]["Acked"]!="yes":
                    buffer[basebuffer]["Acked"]="no"
                reserve_printer()
                print("[%s] packet%d %s sent" % (repr(time.time()), buffer[basebuffer]["sequence"], buffer[basebuffer]["data"]))
                senderSideSocket.sendto(json.dumps(buffer[basebuffer]), (self_ip, int(peer_port)))
                release_printer()
                packetCount=packetCount+1
                basebuffer = basebuffer+1  
    
    def send_packets_in_window():
        global baseseqnum
        global nextseqnum
        global stopSending
        
        #print ("in send_packets. next: %d, base: %d, window: %d, bufferLength: %d" %(nextseqnum,baseseqnum,window_size,bufferLength))
        while (nextseqnum < (baseseqnum + window_size) and nextseqnum < bufferLength):
                buffer[nextseqnum]["Acked"]="no"
                reserve_printer()
                #print "base in send", baseseqnum
                #print "next in send", nextseqnum
                #print "window", window_size
                print("[%s] packet%d %s sent" % (repr(time.time()), buffer[nextseqnum]["sequence"], buffer[nextseqnum]["data"]))
                senderSideSocket.sendto(json.dumps(buffer[nextseqnum]), (self_ip, int(peer_port)))
                release_printer()
                
                if(baseseqnum == nextseqnum):
                    timerRestart="yes"
                    threadTimer = threading.Thread(target=start_timer,args=(buffer[nextseqnum]["sequence"],))
                    threadTimer.start()
                nextseqnum = nextseqnum + 1  
                time.sleep(0.01)

    def process_timeout(pktNum):
        global baseseqnum
        reserve_printer()
        #print "base after timeout", baseseqnum
        print ("[%s] packet%d timeout" % (repr(time.time()), pktNum)) 
        release_printer()
        
        if baseseqnum == pktNum:
            send_all_packets_in_window()
    # Wait for incoming ack for 500msec                    
    
    def start_timer(pktNum):
        # Give the message a bit of time to reach the target
        # time.sleep(0.02)
        global timerRestart
        global timerOn
        timerOn = True
        global timerInterrupt
        t_start = time.time()
        t_end = time.time() + 0.5
        #reserve_printer()
        #print "in timer %d [%s]" % (pktNum, t_end)
        #release_printer()
        while (t_start < t_end and buffer[pktNum]["Acked"]=="no" and timerInterrupt=="off"):
                #reserve_printer()
                #print "buffer", buffer[pktNum]
                #print "packet%d is in timer: [%s], stop at [%s]" % (pktNum, t_start,t_end)
                #release_printer()
                t_start = t_start + .01
                time.sleep(0.01)
                #if(timerOn == False):
                    # Reset buffer
                #    return True;
        
        timerOn = False
        timerInterrupt="no"
        
        if (buffer[pktNum]["Acked"]=="yes" or timerRestart=="yes" or timerInterrupt=="yes"):
            timerRestart="no"
            
        else:
            process_timeout(pktNum)
    
    # Listen for incoming messages and process them            
    def receiver_processing():
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
        global timerInterrupt
        
        # Global references to allow for buffer reset
        global stopSending
        global timerRestart
        
        global bufferLength
        
        detPacketCounter=0
        
        while True:
            incomingPacket = None
            try:
                incomingPacket, (senderIp, senderPort) = senderSideSocket.recvfrom(1024)
            except:
                time.sleep(0.01)
                print ("waiting")
            
            # Ignores packets sent from self
            if senderPort == self_port:
                1;
                
            elif incomingPacket:
                # try:
                    message = json.loads(incomingPacket)
                    #print ("in get_message, capturing incoming msg", message)
                    # Check if it is a packet containing acknowledgment of a previously sent packet    
                    
                    probabilisticallyDropped = False
                    deterministicallyDropped = False
                    deterministicValue = 9999999999999999999 #Ensure that modulo of this number is always going to be a non zero
                        
                    # RECEIVER SECTION
                    # Process incoming packet as Receiver
                    if (message["data"] != None):
                        detPacketCounter=detPacketCounter+1
                        
                        if emulation_mode == "-p":
                            emulProb=float(emulation_value)
                            if emulProb > 0:
                                random_number = float(random.random())
                                if random_number < emulProb:
                                    probabilisticallyDropped = True
                            
                        elif emulation_mode == "-d":
                            deterministicValue = emulation_value
                            if((int(detPacketCounter) % int(deterministicValue)) == 0):
                                deterministicallyDropped = True
                                
                        if(deterministicallyDropped==True or probabilisticallyDropped==True):
                            reserve_printer()
                            #print ("modulo: %d, prob drop: %s" %((int(message["sequence"] + 1) % int(deterministicValue)),probabilisticallyDropped))
                            print("[%s] packet%d %s discarded" % (repr(time.time()), message["sequence"], message["data"]))
                            release_printer()
                            lostPacketCounter=lostPacketCounter+1
                            packetCount=packetCount+1    
                        else:
                            reserve_printer()
                            #print ("detvalue: %d, modulo: %d, prob drop: %s" %(int(deterministicValue),(int(message["sequence"] + 1) % int(deterministicValue)),probabilisticallyDropped))
                            print("[%s] packet%d %s received" % (repr(time.time()), message["sequence"], message["data"]))
                            release_printer()
                            packetCount=packetCount+1
                                
                            if(expectedseqnum==message["sequence"]): 
                                #print ("Counter: %d. Modulo: %d " %(detPacketCounter,(int(detPacketCounter) % int(deterministicValue))))
                                    if message["fin"]== "yes":
                                        message["data"] = None
                                        message["fin"]="printSummary"
                                        expectedseqnum=message["sequence"] + 1
                                        senderSideSocket.sendto(json.dumps(message), (self_ip, int(peer_port)))
                                        time.sleep(2.5)
                                        reserve_printer()
                                        print("[%s] ACK%d sent, expecting packet%s" % (repr(time.time()), message["sequence"], expectedseqnum))
                                        print ("[Summary] %d/%d packets dropped, loss rate = %d%%" %(lostPacketCounter,packetCount,lostPacketCounter*100/packetCount))
                                        release_printer()
                                        time.sleep(1)

                                        baseseqnum = 0
                                        nextseqnum = 0
                                        expectedseqnum = 0
                                        bufferLength = 0
                                        stopSending = False
                                        lostPacketCounter = 0
                                        packetCount = 0
                                        AckCount = 0
                                        timerRestart = "no"
                                        buffer = []
                                        timerOn = False
                                        process_send()
                                                                                
                                    #Send ACK
                                    else:
                                        receivedSequence = message["sequence"]
                                        expectedseqnum = message["sequence"] + 1
                                        message["data"] = None
                                        senderSideSocket.sendto(json.dumps(message), (self_ip, int(peer_port)))
                                        reserve_printer()
                                        print("[%s] ACK%d sent, expecting packet%s" % (repr(time.time()), receivedSequence, expectedseqnum))
                                        release_printer()
                            #Ignore out of expectation packets
                            elif (message["sequence"]>expectedseqnum): 
                                1;
                            else:
                                1;
                    
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
                                    probabilisticallyDropped = True
                                
                        if emulation_mode == "-d":
                            deterministicValue = emulation_value
                            if((int(detPacketCounter) % int(deterministicValue)) == 0):
                                deterministicallyDropped = True
                                
                        if (emulation_mode == "-d" or emulation_mode == "-p"):                        
                            if message["fin"]== "printSummary":
                                    buffer[baseseqnum]["Acked"]="yes"
                                    timerInterrupt="on"
                                    baseseqnum = baseseqnum + 1
                                    AckCount=AckCount+1
                                    time.sleep(2.5)
                                    reserve_printer()
                                    print("[%s] ACK%d received, window moves to %d" % (repr(time.time()), message["sequence"], 0))
                                    print ("[Summary] %d/%d packets discarded, loss rate = %d%%" %(lostPacketCounter,AckCount,lostPacketCounter*100/AckCount))
                                    release_printer()
                                    
                                    time.sleep(1)
                                    
                                    baseseqnum = 0
                                    nextseqnum = 0
                                    expectedseqnum = 0
                                    bufferLength = 0
                                    stopSending = False
                                    lostPacketCounter = 0
                                    packetCount = 0
                                    AckCount = 0
                                    timerRestart = "no"
                                    buffer = []
                                    timerOn = False
                                    process_send()
                                    
                                    #time.sleep(2)
                            # Emulate packet loss
                            if (deterministicallyDropped==True or probabilisticallyDropped==True):
                                reserve_printer()
                                print("[%s] ACK%d discarded" % (repr(time.time()), message["sequence"]))
                                release_printer()
                                lostPacketCounter=lostPacketCounter+1
                                packetCount=packetCount+1
                                AckCount=AckCount+1
                                
                            elif ((int(message["sequence"]) == 0) or deterministicallyDropped==False or probabilisticallyDropped == False):
                                
                                #print "ACK received is %d, Next is: %d, base is: %d" %(message["sequence"],nextseqnum,baseseqnum)
                                if((int(message["sequence"])) == baseseqnum): 
                                    #timerOn = False
                                    buffer[baseseqnum]["Acked"]="yes"
                                    timerInterrupt="on"
                                    baseseqnum = baseseqnum + 1
                                    reserve_printer()
                                    print("[%s] ACK%d received, window moves to %d" % (repr(time.time()), message["sequence"], baseseqnum))
                                    release_printer()
                                    if buffer[baseseqnum]["Acked"]=="no":
                                        start_timer(baseseqnum)
                                    time.sleep(0.01)
                                    #packetCount=packetCount+1
                                    AckCount=AckCount+1
                                elif((int(message["sequence"])) > baseseqnum and baseseqnum!=0):
                                    #timerOn = False
                                    AckGap = (int(message["sequence"]) - baseseqnum)
                                              
                                    while (AckGap != 0):
                                        buffer[(baseseqnum-AckGap)]["Acked"]="yes"
                                        timerInterrupt="on"
                                        AckGap = AckGap - 1
                                        baseseqnum = baseseqnum + 1
                                        reserve_printer()
                                        print("[%s] ACK%d received, window moves to %d" % (repr(time.time()), (baseseqnum-AckGap), (baseseqnum-AckGap+1)))
                                        release_printer()
                                        AckCount=AckCount+1
                                    if buffer[baseseqnum]["Acked"]=="no":
                                        start_timer(baseseqnum)
                                    time.sleep(0.01)
                                else:
                                    start_timer(message["sequence"])

                            

                        else:
                            1;
                            #print "ACK received is %d, Expected is: %d" %(message["sequence"],expectedseqnum)
                # except:
                #    print ("[Exception: Cannot deliver an incoming chat transmission]")
        
    def process_send():
        global timerOn
        global bufferLength
        global lostPacketCounter
        global packetCount
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
            packetWithHeader = {"sequence": bufferLength, "data": i, "fin": "", "Acked": ""}
            bufferLength = bufferLength + 1
            buffer.append(packetWithHeader)
        
        packetCount = bufferLength
        buffer[(bufferLength-1)]["fin"]= "yes"
        firstThread = threading.Thread(target=send_packets_in_window)
        firstThread.start()
        
        #while stopSending == False:
        #    time.sleep(0.01)
            
        #firstThread.join()

    process_send()              
    
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
        




    

