from socket import *
import sys 
import argparse
import re
from struct import *


"""________________________________________________________________________________________________
                                            HEADER
    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
"""

def create_packet(seq, ack, flags, win, data):
    #creates a packet with header information and application data
    #the input arguments are sequence number, acknowledgment number
    #flags (we only use 4 bits),  receiver window and application data 
    #struct.pack returns a bytes object containing the header values
    #packed according to the header_format !IIHH
    header_format = '!IIHH'
    header = pack (header_format, seq, ack, flags, win)

    #once we create a header, we add the application data to create a packet
    #of 1472 bytes
    packet = header + data
    print (f'packet containing header + data of size {len(packet)}') #just to show the length of the packet
    return packet


def parse_header(header):
    #taks a header of 12 bytes as an argument,
    #unpacks the value based on the specified header_format
    #and return a tuple with the values
    header_format = '!IIHH'
    header_from_msg = unpack(header_format, header)
    #parse_flags(flags)
    return header_from_msg
    

def parse_flags(flags):
    #we only parse the first 3 fields because we're not 
    #using rst in our implementation
    syn = flags & (1 << 3)
    ack = flags & (1 << 2)
    fin = flags & (1 << 1)
    return syn, ack, fin

"""________________________________________________________________________________________________
                                           END OF HEADER
    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
"""





""" _______________________________________________________________________________________________
                                         CLIENT
    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
"""

def handleClient(serverIP,port):
    socketClient = socket(AF_INET,SOCK_DGRAM) #Creating socket for client
    server_address=(serverIP,port)

   
    ###################################################################################################
    #Making a data packet with 1460bytes
    emptydata=b''
    sequence_number = 0

    acknowledgment_number = 0
    window = 0 # window value should always be sent from the receiver-side
    flags = 8 # we are not going to set any flags when we send a data packet

    #msg now holds a packet, including our custom header and (no) data
    msg = create_packet(sequence_number, acknowledgment_number, flags, window, emptydata)

    #Send the syn to the server
    socketClient.sendto(msg,server_address)

     # set timeout
    socketClient.settimeout(0.5)

    try:
        #recevies a synack
        syn_ack_packet, _ = socketClient.recvfrom(1472)

        #Decodes the syn ack
        syn_ack_packet = syn_ack_packet.decode

        #gets the header
        header_from_syn_ack = syn_ack_packet[:12]

        #Gets all the elements from the header
        seq, ack, flags, win = parse_header (header_from_syn_ack.decode)
        print(f'seq={seq}, ack={ack}, flags={flags}, recevier-window={win}')

        # parse flagg part
        syn_flagg, ack_flagg, fin_flagg = parse_flags(flags)

        if(syn_flagg==8 and ack_flagg==4):
            # Send ACK packet to server
            ack_packet = create_packet(sequence_number, acknowledgment_number, flags, window, emptydata)
            socket.sendto(ack_packet.encode(), (server_address))
            print("Connection establish!")
        else:
            print("Error: SYN-ACK not received.")

    except socket.timeout:
        print("Time out while waiting for SYN-ACK") 

    
    ###################################################################################################

""" _______________________________________________________________________________________________
                                         END OF CLIENT
    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
"""
   




"""________________________________________________________________________________________________
                                         SERVER
    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
"""
def handleServer(port, IP):
    serverSocket = socket(AF_INET, SOCK_DGRAM) 
    serverPort = port #port number of the server
    emptydata= b''

    try:
        #Binding socket to a IP adress and port
        serverSocket.bind((IP, serverPort)) 
    except:
        print("Bind failed. Error : ")
        sys.exit()

    try:
        #receives the SYN from client
        SYN_msg, client_address = serverSocket.recvfrom(2048) # check SYN packet from client
        
        #Parse the header
        seq, ack, flags, win = parse_header(SYN_msg.decode)
        print(f'seq={seq}, ack={ack}, flags={flags}, recevier-window={win}')

        #parse the flag field
        syn_flag, ack_flag, fin_flag = parse_flags(flags)
        print (f'syn_flag = {syn_flag}, fin_flag={fin_flag}, and ack_flag={ack_flag}')

        if(syn_flag==8):

            #Setting the header elements
            sequence_number = 0
            acknowledgment_number = 0
            window = 0
            flags = 12 # (SYN = 8) + (ACK = 4) = 12

            #Creating SYN ACK packet
            SYN_ACK_msg=create_packet(sequence_number,acknowledgment_number,flags,window,emptydata)
            
            #Sends SYN_ACK to client
            serverSocket.sendto(SYN_ACK_msg.encode(),client_address)

            #Recieves ACK from client
            ACK_msg, client_address = serverSocket.recvfrom(2048) # check SYN packet from client
            ACK_msg = ACK_msg.decode
            
            #Take the header from the ACK
            header_from_ACK = ACK_msg[:12]
            
            #Parse the header
            seq, ack, flags, win = parse_header (header_from_ACK)
            print(f'seq={seq}, ack={ack}, flags={flags}, recevier-window={win}')

            #parse the flag field
            syn_flag, ack_flag, fin_flag = parse_flags(flags)
            print (f'syn_flag = {syn_flag}, fin_flag={fin_flag}, and ack_flag={ack_flag}')

            if(ack_flag==4):
                print("Connection established with ", client_address)
            else:
                print("Error: ACK not received!")
        else:
            print("Error: SYN not received!")
        
            return client_address
    except:
        print("Connection establishent failed")
        sys.exit()

"""________________________________________________________________________________________________
                                        END OF SERVER
    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
"""






"""________________________________________________________________________________________________
                                        OTHER FUNCTIONS
    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
"""

#Checking Ip address inn in --bind and --serverip argument
def check_IP(val):
    #Checking that the string is in the right format
    value = re.match('^[0-9]{1,3}[.][0-9]{1,3}[.][0-9]{1,3}[.][0-9]{1,3}', val)
    if not value:
        print("Not a valid IP address. I nedd to be in the format of: \n X.X.X.X \n Where X is a number between 0-127.")
        sys.exit
    return val #Returning the val that was in the right format, so that it can be used


"""________________________________________________________________________________________________
                                       END OF OTHER FUNCTIONS
    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
"""





"""________________________________________________________________________________________________
                                        ADDING ARGUMENTS
    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
"""

parser = argparse.ArgumentParser(description="Portfolio 2", epilog="End of help")

# Server arguments
parser.add_argument("-s", "--server", help="Enable the server mode", action='store_true')
parser.add_argument("-b", "--bind", type=check_IP, help="IP address in dotted decimal notaion format", default="127.0.0.1")
parser.add_argument("-p", "--port", type=int, help="Port number the server should listen to in server mode/ select server's port number in client mode", default=8088)



# Client arguments
parser.add_argument("-c", "--client", help="Enable the client mode", action='store_true')
parser.add_argument('-I', "--serverip", type=check_IP, help="IP adress of the server", default="127.0.0.1")


args = parser.parse_args()



"""________________________________________________________________________________________________
                                        HANDLE ARGUMENTS
    ‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾
"""



#If -s and -c is not specified
if (not args.server and not args.client):
    print('Error: you must run either in server or client mode')
    sys.exit

#If both -c and -s is specified
elif (args.server and args.client):
    print('Error: you can only run server OR client, not both.')
    sys.exit

elif args.server:
        handleServer(args.bind, args.port)

else:
        handleClient(args.serverip, args.port)

