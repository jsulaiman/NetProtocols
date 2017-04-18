import argparse
import select
from socket import *
import sys
import time
import threading
import os
import json
import random
from email.mime import base


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
        time.sleep(0.001)
        
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
        
        #if basebuffer < bufferLength:
            #print ("base:%d, next:%d" %(baseseqnum,nextseqnum))
        timerOn=False
        threadTimer = threading.Thread(target=start_timer)
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
        global timerOn
        
        
        #print ("in send_packets. next: %d, base: %d, window: %d, bufferLength: %d" %(nextseqnum,baseseqnum,window_size,bufferLength))
        while ((nextseqnum < bufferLength) and (nextseqnum < (baseseqnum + window_size)) ):
                
                buffer[nextseqnum]["Acked"]="no"
                reserve_printer()
                #print "base in send", baseseqnum
                #print "next in send", nextseqnum
                #print ("baseseqnum: %d, nextseqnum: %d, bufferLength: %d,window: %d" %(baseseqnum, nextseqnum, bufferLength, window_size))
                print("[%s] packet%d %s sent" % (repr(time.time()), buffer[nextseqnum]["sequence"], buffer[nextseqnum]["data"]))
                senderSideSocket.sendto(json.dumps(buffer[nextseqnum]), (self_ip, int(peer_port)))
                release_printer()
                
                if(baseseqnum == nextseqnum):
                    timerOn=False
                    threadTimer = threading.Thread(target=start_timer)
                    threadTimer.start()
                nextseqnum = nextseqnum + 1  
                #time.sleep(0.01)

    def process_timeout():
        global baseseqnum
        reserve_printer()
        #print "base after timeout", baseseqnum
        print ("[%s] packet%d timeout" % (repr(time.time()), baseseqnum)) 
        release_printer()
        
        send_all_packets_in_window()          
    
    def start_timer():
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
        
        #Timeout
        if timerOn==True:
            timerOn = False
            process_timeout()
    
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
        
        # Global references to allow for buffer reset
        global stopSending
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
                            if(expectedseqnum==message["sequence"]): 
                                reserve_printer()
                                #print ("modulo: %d, prob drop: %s" %((int(message["sequence"] + 1) % int(deterministicValue)),probabilisticallyDropped))
                                print("[%s] packet%d %s discarded" % (repr(time.time()), message["sequence"], message["data"]))
                                release_printer()
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
                                        senderSideSocket.sendto(json.dumps(message), (self_ip, int(peer_port)))
                                        # Turn off timer
                                        if timerOn == True:
                                            timerOn = False

                                        
                                        reserve_printer()
                                        print("[%s] packet%d %s received" % (repr(time.time()), message["sequence"], lastpacketnum))
                                        print("[%s] ACK%d sent, expecting packet%s" % (repr(time.time()), message["sequence"], expectedseqnum))
                                        release_printer()
                                        
                                        time.sleep(1)
                                        reserve_printer()
                                        #print("[%s] Last ACK%d sent" % (repr(time.time()), message["sequence"]))
                                        print ("[Summary] %d/%d packets dropped, loss rate = %s" %(lostPacketCounter,packetCount,format(float(lostPacketCounter)/packetCount,".2f")))
                                        release_printer()
                                        
                                        baseseqnum = 0
                                        nextseqnum = 0
                                        expectedseqnum = 0
                                        bufferLength = 0
                                        stopSending = False
                                        lostPacketCounter = 0
                                        packetCount = 0
                                        AckCount = 0
                                        buffer = []
                                        timerOn = False
                                        process_send()

                       
                                    #Send ACK
                                    else:
                                        reserve_printer()
                                        #print ("detvalue: %d, modulo: %d, prob drop: %s" %(int(deterministicValue),(int(message["sequence"] + 1) % int(deterministicValue)),probabilisticallyDropped))
                                        print("[%s] packet%d %s received" % (repr(time.time()), message["sequence"], message["data"]))
                                        release_printer()
                                        packetCount=packetCount+1
                            
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
                                reserve_printer()
                                #print ("detvalue: %d, modulo: %d, prob drop: %s" %(int(deterministicValue),(int(message["sequence"] + 1) % int(deterministicValue)),probabilisticallyDropped))
                                print("[%s] packet%d %s received" % (repr(time.time()), message["sequence"], message["data"]))
                                release_printer()
                                packetCount=packetCount+1
                    
                                receivedSequence = message["sequence"]
                                message["data"] = None
                                senderSideSocket.sendto(json.dumps(message), (self_ip, int(peer_port)))
                                reserve_printer()
                                print("[%s] ACK%d sent, expecting packet%s" % (repr(time.time()), receivedSequence, expectedseqnum))
                                release_printer()
                    
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
                                    #print "in fin print summary"
                                    buffer[baseseqnum]["Acked"]="yes"
                                    #timerOn=False
                                    baseseqnum = baseseqnum + 1
                                    AckCount=AckCount+1
                                    if timerOn == True:
                                        timerOn = False
                                    
                                    reserve_printer()
                                    print("[%s] ACK%d received, window moves to %d" % (repr(time.time()), message["sequence"], baseseqnum))
                                    release_printer()
                                    # Turn off timer
                                    
                                    time.sleep(1)
                                    reserve_printer()
                                    print ("[Summary] %d/%d packets discarded, loss rate = %s" %(lostPacketCounter,AckCount,format(float(lostPacketCounter)/AckCount,".2f")))
                                    release_printer()
                                    
                                    baseseqnum = 0
                                    nextseqnum = 0
                                    expectedseqnum = 0
                                    bufferLength = 0
                                    stopSending = False
                                    lostPacketCounter = 0
                                    packetCount = 0
                                    AckCount = 0
                                    buffer = []
                                    timerOn = False
                                    process_send()
                                    
                            # Emulate packet loss
                            elif ((int(message["sequence"]) != 0) and (deterministicallyDropped==True or probabilisticallyDropped==True)):
                                reserve_printer()
                                print("[%s] ACK%d discarded" % (repr(time.time()), message["sequence"]))
                                release_printer()
                                lostPacketCounter=lostPacketCounter+1
                                packetCount=packetCount+1
                                AckCount=AckCount+1
                                
                            elif (deterministicallyDropped==False or probabilisticallyDropped == False):
                                #print "ACK received is %d, Next is: %d, base is: %d" %(message["sequence"],nextseqnum,baseseqnum)
                                if((int(message["sequence"])) == baseseqnum): 
                                    buffer[baseseqnum]["Acked"]="yes"
                                    timerOn = False
                                    baseseqnum = baseseqnum + 1

                                    reserve_printer()
                                    print("[%s] ACK%d received, window moves to %d" % (repr(time.time()), message["sequence"], baseseqnum))
                                    release_printer()
                                    
                                    if baseseqnum != bufferLength:
                                        if buffer[baseseqnum]["Acked"]!="":
                                            timerOn=False
                                            threadTimer = threading.Thread(target=start_timer)
                                            threadTimer.start()
                                            send_packets_in_window()
                                        elif buffer[baseseqnum]["Acked"]=="no":
                                            timerOn=False
                                            threadTimer = threading.Thread(target=start_timer)
                                            threadTimer.start()
                                    
                                    #time.sleep(0.01)
                                    #packetCount=packetCount+1
                                    AckCount=AckCount+1
                                elif((int(message["sequence"])) > baseseqnum and baseseqnum!=0):
                                    timerOn = False
                                    AckGap = (int(message["sequence"]) - baseseqnum)
                                    
                                    if baseseqnum != bufferLength:       
                                        while (AckGap != 0):
                                            buffer[(baseseqnum-AckGap)]["Acked"]="yes"
                                            #timerOn=False
                                            AckGap = AckGap - 1
                                            baseseqnum = baseseqnum + 1
                                            reserve_printer()
                                            print("[%s] ACK%d received, window moves to %d" % (repr(time.time()), (baseseqnum-AckGap), (baseseqnum-AckGap+1)))
                                            release_printer()
                                            AckCount=AckCount+1
                                        if buffer[baseseqnum]["Acked"]!="":
                                            timerOn=False
                                            threadTimer = threading.Thread(target=start_timer)
                                            threadTimer.start()
                                            send_packets_in_window()
                                        elif buffer[baseseqnum]["Acked"]=="no":
                                            timerOn=False
                                            threadTimer = threading.Thread(target=start_timer)
                                            threadTimer.start()


                        else:
                            print ("else in Ack")
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
        self_port = int(argList[1])
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
    launchNode(self_port, peerPort, windowSize, emulationMode, emulationValue)
        




    

