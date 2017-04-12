NAME: Johan Sulaiman
UNI: js5063

HOW TO COMPILE AND RUN THE PROGRAM
The following code's purpose is to perform network protocols emulation, specifically the Go-Back-N (GBN) protocol and the Distance Vector Routing Algorithm-based protocol.
The code is written and runnable with python 2.7.6. It contains three executables:
gbnnode.py: This executable implements a simple Go-Back-N protocol which is part of the link layer.
dvnode.py: This executable implements a Distance-Vector Routing algorithm, which is part of the network layer.
cnnode.py:


PROGRAM FEATURES
A. gbnnode.py: There are two nodes involved here, a sender node and a receiver node. The sender sends UDP packets to the receiver, utilizing GBN. 
It takes the following as parameters: 
* self-port: the sending port
* peer-port: the receiver port
* window-size: the size of the window in GBN
* emulation mode: either deterministic or probabilistic emulation of lost or dropped packets
* emulation value: the frequency or the probability of how packets should be dropped by the emulator

Every packet contains one character in the data section. It also contains a header component that is used to store the segment ID of the packet. 
ACKs are sent back to the sender from the receiver, with the data section containing null.

At the start of the program the entries inputted by the user using the <send> command is placed in a buffer.

The program utilizes multithreading; one thread to listen for incoming packets, and another to perform timeout and sending/resending mechanism.

B. dvnode.py: A graph based program, where graph: G = (N,E). Where N is a set of routers = {u,v,w,x,y,z} and E is a set of links = {(u,v),(u,x),(v,x),(v,w),(x,w),(x,y),(w,y),(w,z),(y,z)}


USAGE SCENARIOS

ALGORITHM AND DATA STRUCTURES EXPLANATION
GBNNODE.PY: 
* The packet in gbnnode.py is implemented using a list of dictionaries.
Each dictionary has two components: the "data" and the "header" . The "data" section of the dictionary contains the 1 character data in the case
of sender packet, or contains null in the case of a receiver packet. The header contains the following: 1) "sequence" represents the packet header which contains the packet's sequence number.
The entries are in order to aid the program to figure out packets' order. 2) "Acked" represents whether the packet has been sent "no", or has been acknowledged "yes". 3) "fin", which represents whether
the packet is involved in the transmission of the last packet or not.
* A buffer is a container of the individual data about to be sent
* A window is specified as a parameter during program launch. This determines the size of the GBN window, which helps ensure reliable data transfer.
* The program also implements a timer, which will timeout if an expected ACK is not received within 500ms. At a timeout event, every packet in the window
will be resent, and the timer restarted.
* The timer starts after the fi
* The receiver only sends an ACK when it receives an expected, in-order packet from the receiver. If not, it will do nothing.
* json is imported to assist in sending and receiving packets in json format

ADDITIONAL FEATURES/FUNCTIONS

REFERENCES
https://docs.python.org/2/howto/sockets.html
https://www.howtoforge.com/tutorial/install-git-and-github-on-ubuntu-14.04/
JSON versus XML: http://www.json.org/xml.html
Encoding and decoding JSON in Python: https://pythonspot.com/json-encoding-and-decoding-with-python/
Python multithreading tutorial: https://pymotw.com/2/threading/	