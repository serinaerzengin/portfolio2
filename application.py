from socket import *
from struct import *
import argparse
import ipaddress
import sys
from PIL import Image
import ping3
import time


# ------------------------------------------------------------------------------#
#                                   Header handling                             #
# ------------------------------------------------------------------------------#

header_format = '!IIHH' # header size is always 12 bytes

def create_packet(seq, ack, flags, win, data): # parameters are sequence number, acknowledgment number, flags (4 bits), receiver window and application data
    header = pack(header_format, seq, ack, flags, win) # Create a header of 12

    packet = header + data # header is 12, and data is 1460. This packet should be 1472 bytes

    return packet

def parse_header(header): # take header of 12 bytes as an argument

    # unpack the message based on the specified header_format, and only take the header
    header_from_message = unpack(header_format, header)

    return header_from_message # this will return a tuple of values seq, ack, flags and win

def parse_flags(flags): # get the values of syn, ack and fin
    syn = flags & (1 << 3)
    ack = flags & (1 << 2)
    fin = flags & (1 << 1)
    return syn, ack, fin



# ------------------------------------------------------------------------------#
#                              Done header handling                             #
# ------------------------------------------------------------------------------#

# ------------------------------------------------------------------------------#
#                                BONUS AND OTHER                                #
# ------------------------------------------------------------------------------#

#Function to calculate round trip time in bonus task
def roundtriptime(bonus,IPaddress):
    #If -B flag is activated
    if bonus:
    #Calculate the rtt, multiplie it with 4 to get the optimized rtt
        rtt = ping3.ping(IPaddress) 
        rtt = rtt*4 

        #If not possible to calculate rtt
        if rtt is None:
            print(f"Failed to get round trip time from {IPaddress}")
            #Set default rtt
            rtt = 0.5
    
    #If not -B flag is activated
    else:
        rtt=0.5
        #Set default rtt


    return rtt

#Function to calculate throughput
def throughput(sizedata, totalduration):

    size_bit= sizedata*8 #From Byte -> bit
    size_Mb=size_bit/1000 #From bit -> Megabit
    
    throughput=size_Mb/totalduration #Calculating throughput
    throughput='{0:.2f}'.format(throughput) #only 2 decimals
    
    print('\n--------------------------------------')
    print(f'Throughput: {throughput} Mbps')
    print('--------------------------------------')

    print(f'size of data: {sizedata}')


#Class used in SR server for adding packet inn buffer
class One_Packet:
    #constructor
    def __init__(self,seq, data):
        self.seq = seq
        self.data = data
   
    

# ------------------------------------------------------------------------------#
#                              END OF BONUS AND OTHER                           #
# ------------------------------------------------------------------------------#

# ------------------------------------------------------------------------------#
#                                Handle file                                    #
# ------------------------------------------------------------------------------#

# Split files in to right size packet, and add them to a data array
def file_splitting(file_sent):
    list = []
    
    with open(str(file_sent), 'rb') as file:
        while True:
            data = file.read(1460) # take only 1460 bytes from picture
            if not data: # break if there is no more data
                break
            else: # if there is data
                list.append(data) # add to an array
    
    #Return list with all of the data packets in it. 
    return list


# Join all the packets received in to a file
def join_file(list, filename):
    with open(filename, 'wb') as f:
        for part in list:
            f.write(part)
    return filename

# ------------------------------------------------------------------------------#
#                            Done handle file                                   #
# ------------------------------------------------------------------------------#


# ------------------------------------------------------------------------------#
#                           Close connection                                    #
# ------------------------------------------------------------------------------#

#Function to close connection from the client side, send fin-packet
def close_connection_client(clientSocket, server_Addr):
    # Variables to make fin-packet
    data = b''
    sequence_number = 0
    acknowledgement_number = 0
    window = 0
    flags = 2

    # Create and send fin-packet
    fin_packet = create_packet(sequence_number, acknowledgement_number, flags, window, data)
    clientSocket.sendto(fin_packet, server_Addr)

    #Try to receieve a fin-ack packet
    try:
        close_msg, serverAddr = clientSocket.recvfrom(2048) # Receive packet
        seq, ack, flagg, win = parse_header(close_msg) # Parse header to get flags
        syn_flagg, ack_flagg, fin_flagg = parse_flags(flagg) #Parse flags to get fin and ack flag

        if ack_flagg + fin_flagg == 6:  # check if this is FIN-ACK message 
            print("Close connection from client!!!")
    except error:
        print("Can not close at the moment!!!")


#Function to close connection server side
def close_connection_server(serverSocket, client_addr):
    # Variables to create FIN-ACK
    sequence_number = 0
    acknowledgment_number = 0
    window = 64000
    flagg = 6 # FIN and ACK is set to 1 

    # Create packet and send FIN-ACK back to client for confirmation
    ACK_packet = create_packet(sequence_number, acknowledgment_number, flagg, window, b'')
    serverSocket.sendto(ACK_packet, client_addr) # send SYN ACK to clie
    
    print("The transfer is done! Server close now!!!!")


# ------------------------------------------------------------------------------#
#                         Done close connection                                 #
# ------------------------------------------------------------------------------#






# ------------------------------------------------------------------------------#
#                                 STOP AND WAIT                                 #
# ------------------------------------------------------------------------------#

def SAW_Client(filename,clientSocket,serverAddr, test,rtt):
    #Data_list contains data packets
    data_list = file_splitting(filename)

    #starts at 0 
    sequence_id = 0

   
    #Send data as long as the data_list is not empty
    while sequence_id < len(data_list):
        
        #Variables when creating packet
        acknowledgement_number = 0
        window = 0 
        flags = 0

        #test - drop ack
        if sequence_id == 30 and "loss" in test:
                print('\n\n Drops packet nr 30\n\n')
                sequence_id+=1
                test = "something else"
                
        # Creating packet, and sending
        data = data_list[sequence_id]
        packet = create_packet(sequence_id,acknowledgement_number,flags,window,data)
        clientSocket.sendto(packet,serverAddr)
        print('sent packet ', str(sequence_id))

        #timeout
        clientSocket.settimeout(rtt)
        try:    
            #reveices packet from server
            ack_from_server, serverAddr = clientSocket.recvfrom(2048)

            # parsing the header since the ack packet should be with no data
            seq, ack, flagg, win = parse_header(ack_from_server)
            
                
            # Checks if the acknowledgement is for the right packet
            if  sequence_id == ack:
                # parse flags
                syn_flagg, ack_flagg, fin_flagg = parse_flags(flagg)
                print('Got ack: '+str(ack))

                # Check if it has ack flagg marked
                if ack_flagg == 4:
                    #Sequence increases whit 1 if we received the rigth packet
                    sequence_id+=1
            else:
                #if a packet is dropped, server sneds dupack, and we calculate which packet we send next.
                sequence_id=ack+1
                print('\n\nReceived dupack: ', str(ack) , '\n\n')
               
                
       
       #if timeout, the sequence number should not be changed. We send packet
        except timeout:
            
            print("Error: Timeout")

    #Sent all packets for the file, and therefore closing the connection         
    close_connection_client(clientSocket, serverAddr)
   



def SAW_Server(filename,serverSocket, test):
    #list with the data
    data_list = [] 

     #Variables for creating packet
    emptydata=b''
    sequence_number = 0
    ack_number = 0
    window = 0
    flagg = 0

    #To help get packets in the right ordedr
    last_ack_number = -1

    #Marking start time
    starttime=time.time()

    #varibale for amount data received
    sizedata=0

    while True:
        #waits for packets
        packet, client_address = serverSocket.recvfrom(2048)

        # Extracting the header
        header = packet[:12]

        # parsing the header
        seq, ack, flagg, win = parse_header(header)

        #parsing the flags
        syn_flagg, ack_flagg, fin_flagg = parse_flags(flagg)

        # check if this is a fin message
        if fin_flagg == 2:
            close_connection_server(serverSocket, client_address)
            break

        #checks to see if packets come in the right order.
        if seq == (last_ack_number+1): 
            # extract the data from the header
            data = packet[12:]
            print('Received packet nr: ', str(seq))

           

            # If at packet nr. 13, we skip sending the ack (the ack got lost).
            if seq == 13 and "skipack" in test:
                print('\n\nDroppet ack nr 13\n\n')
                # set to false so that the skip only happens once.
                test = "something else"
                
            
            else:
               
                #Puts the data in the list
                data_list.append(data)
                #adding the size of the packet to the total data
                sizedata+=len(packet)
                ack_number=seq
                flagg = 4 # sets the ack flag
                #creates and send ACK-msg to server
                ack_packet = create_packet(sequence_number,ack_number,flagg,window,emptydata)
                serverSocket.sendto(ack_packet, client_address)
                last_ack_number+=1
                sequence_number+=1
                print('Sent ack packet: ', str(ack_number))

        else:
            ack_number=last_ack_number
            flagg = 4 # sets the ack flag
            #send ack  med lastacknumber
            #creates and send ACK-msg to server
            ack_packet = create_packet(sequence_number,ack_number,flagg,window,emptydata)
            serverSocket.sendto(ack_packet, client_address)
    
    #Calculating the time
    endtime = time.time()
    totalduration=endtime-starttime
    
    #Sends to method that calcultates and prints througput
    throughput(sizedata,totalduration)

     
    # Takes all the packets in the list and makes the file
    filename = join_file(data_list,filename)


# ------------------------------------------------------------------------------#
#                           End of stop and wait                                #
# ------------------------------------------------------------------------------#







# ------------------------------------------------------------------------------#
#                                   GBN                                         #
# ------------------------------------------------------------------------------#



def GBN_client(window, filename, clientSocket, server_Address, test, rtt):
    
    #Splitting the file into packets for 1460 bytes
    data_list = file_splitting(filename)

    #Variables to help window
    base = 0 #First i window and last ack to be recevied
    next_to_send = 0
    
    #Variables to make packet
    data = data_list[base]
    seq_number = next_to_send
    acknowledgement_number = 0
    flags = 0

    #Loop until received ack for all packets in the list
    while base < len(data_list):

        #If its packet 44 -> dropped
        if next_to_send == 44 and "loss" in test: 
            print('\n\nDrop packet nr 44\n') 
            next_to_send+=1 #To skip packet

            # set to false so that the skip only happens once.
            test = " "
       
        #If not packet 44, we send normally
        else:
            
            #Sends packets until the window is full, as long as there is more packet to be sent 
            while next_to_send < base + window and next_to_send < len(data_list):    
                
                #Updates seq_number of the packet we are sending
                seq_number=next_to_send

                # Creating and sending packet
                data = data_list[seq_number] #getting packets to send in the right order
                packet = create_packet(seq_number,acknowledgement_number,flags,window,data) 
                clientSocket.sendto(packet,server_Address) 
                print(f'Sendt seq: {seq_number}')

                #Updates next packet to send, and seq number
                next_to_send+=1

            # The window is full - now we wait on ack to move the window

            clientSocket.settimeout(rtt)
            
            try:
                #reveices ack from server
                ack_from_server, serverAddr = clientSocket.recvfrom(2048)
                
                # parsing the header since the ack packet should be with no data
                seq, ack, flagg, win = parse_header(ack_from_server)
                print(f'Got ack: {ack}\n')

                # Checks if the acknowledgement is for the right packet. 
                # The ack should be for the first packet in the window (base)
                if  base == ack:
                    # parse flags
                    syn_flagg, ack_flagg, fin_flagg = parse_flags(flagg)

                    # Check if it has ack flagg marked
                    if ack_flagg == 4:
                        base+=1 # we move the window

            
            except timeout:
                print(f"\nError: Timeout because never got ack of {base}\nStarting to send from packet {base}.\n\n")
                next_to_send=base
    
    
    #Sent all packets for the file, and therefore closing the connection
    close_connection_client(clientSocket, server_Address)




def GBN_server(filename, serverSocket, test): 

    #Creating list receieved data will be added into
    data_list = []

    #Variables for creating packet
    emptydata=b''
    sequence_number = 0
    ack_number = 0
    window = 64000
    flagg = 0

    #Variables to help get packets in the right ordedr
    last_packet_added = -1
    last_ack_sent = -1

    #Marking start time for calculating througput
    starttime=time.time()

    #varibale for amount data received for calculating througput 
    sizedata=0

    while True:

        #Receive packet
        packet, client_address = serverSocket.recvfrom(2048)

        # Extracting the header
        header = packet[:12]

        # parsing the header
        seq, ack, flagg, win = parse_header(header)
        print('\nReceived a packet with seq: '+str(seq))

        #parsing the flags
        syn_flagg, ack_flagg, fin_flagg = parse_flags(flagg)

        # check if this is a fin message
        if fin_flagg == 2:
            close_connection_server(serverSocket, client_address)
            break

       
        
        # this if checks:    
        #   1. if packets come in the right order
        #   2. if the packet has been added before
        # This if also makes sure each packet in the list has sent an ack before another packet gets added
        if seq == last_packet_added+1 and last_packet_added == last_ack_sent: 
            
            # extract the data from the header
            data = packet[12:]
        

            # Puts the data in the list
            data_list.append(data)
            print('Added packet nr '+str(seq)+' to the list')
            #adding the size of the packet to the total data
            sizedata+=len(packet)

            #update last packet added to the list
            last_packet_added+=1

        #Else we discard the packet
        else:
            print(f"Throws packet {seq} away") 
        
        #If packet 21, we skip ack ("Ack got lost")
        if seq == 21 and "skipack" in test:
            print('\n\nDroppet ack nr 21\n\n')
            
            # set to false so that the skip only happens once.
            test = " "
            
        else:
            # If check:
            #       -> If the packet ha been added to the list
            # If so an ack is sent to inform client that the packet is received
            if seq <= last_ack_sent+1:
                
                # Arguments in ack packet.
                ack_number = seq
                flagg = 4 # sets the ack flag

                #creates and send ACK-msg to server
                ack_packet = create_packet(sequence_number,ack_number,flagg,window,emptydata)
                serverSocket.sendto(ack_packet, client_address)
                sequence_number+=1

                last_ack_sent=ack_number
                
                print('Sent ack packet: ',ack_number,'\n')
                
            
            #sets test to false so packet number 5 does not get skipped. 
            
    #Stops the time
    endtime = time.time()
    #Calculating the totalt time
    totalduration=endtime-starttime
    
    #Sends to method that calcultates and prints througput
    throughput(sizedata,totalduration)

    
    # Takes all the packets in the list and makes the file
    filename = join_file(data_list,filename)
    

# ------------------------------------------------------------------------------#
#                                 End of GBN                                    #
# ------------------------------------------------------------------------------#








# ------------------------------------------------------------------------------#
#                                   SR                                          #
# ------------------------------------------------------------------------------#
 

def SR_client(clientSocket, server_Address, test, filename, window_size,rtt):
    
    #Splitting the file into packets for 1460 bytes
    data_list = file_splitting(filename)

     #Variables to help window
    base = 0 
    next_to_send = 0
    
    
    packets_sent = [] #Contians the packets in window which has been send and acked.

     #Variables to make packet
    seq_number = next_to_send
    acknowledgement_number = 0
    flags = 0

    

    # Loop to send packets to the server
    while base<len(data_list):

        # Fill the sliding window with packets up to the window size
        while next_to_send < base + window_size and len(packets_sent) < window_size and next_to_send<len(data_list):
            
            #Updating variables in packet we are sending
            data=data_list[next_to_send]
            seq_number=next_to_send

            #Creating and sending data
            packet = create_packet(seq_number,acknowledgement_number,flags,window_size,data)

            #Test - drop packet 10
            if next_to_send == 10 and "loss" in test:
                print("drop packet 10")
                # set to false so that the skip only happens once.
                test = " "
            
            #Else send packet    
            else:
                clientSocket.sendto(packet,server_Address) 
                print(f'Sendt seq: {seq_number}')


            #Updating the list of sent packets in winodw, and next seq number
            packets_sent.append(packet)
            next_to_send+=1
            
        
        #setting timeout
        clientSocket.settimeout(rtt)

        
        try:
            #reveices ack from server
            ack_from_server, serverAddr = clientSocket.recvfrom(2048)
            
            # parsing the header since the ack packet should be with no data
            seq, ack, flagg, win = parse_header(ack_from_server)

            # If Ack is for a packet in window
            if ack >= base and ack < base + window_size:
                print('Received ACK for packet:', ack)
                
                #How we keep track of acked packets in window:
                        #If packet = None in extra-list, then received Ack for it
                        #If packet != None in extralist, noe received Ack for it

                #Sets the packet to None in the extra list.
                packets_sent[ack - base] = None
                if ack == base:
                    # Move the sliding window and remove the ACKed packets from the packets list
                    while packets_sent and packets_sent[0] is None:
                        #As long as packet is acket (None in extra list):
                        #We remove it from the list
                        packets_sent.pop(0)
                        #And slide the window
                        base += 1
            
            #If noe packets in extra list, and base is at the last packet.
            if not packets_sent and base==len(data_list)-1:
                # All packets have been ACKed, so exit the loop
                break

        
        except timeout:
            # Handle a timeout by resending the unACKed packets in the sliding window
            print('Timeout: resending packet: ',base)
            
            #Looping through extra list
            for i in range(len(packets_sent)):
                pack=packets_sent[i]

                #If pack is None = Not received ack -> Resend
                if pack is not None:
                    clientSocket.sendto(pack,server_Address) 
                    print(f'Resent seq: {base+i} beacuse of UNacked.')
        
       

    #Sent all packets for the file, and therefore closing the connection
    close_connection_client(clientSocket, server_Address)
    
            


def SR_server(serverSocket, file_name, test):
    #list with the data and buffer
    data_list = [] 
    buffer = []


    #For sending ack packet
    emptydata=b''
    sequence_number = 0
    ack_number = 0
    window = 0
    flagg = 0
    

    

    #varibale for amount data received
    sizedata=0

    #helping variables
    next_expected_seq = 0
    last_packet_added = -1

    #Marking start time
    starttime=time.time()
    while True:
        packet, client_address = serverSocket.recvfrom(2048)

        # extract the data from the header
        data = packet[12:]
        
        # Extracting the header
        header = packet[:12]

        # parsing the header
        seq, ack, flagg, win = parse_header(header)
        print('\nReceived a packet with seq: '+str(seq))

        #parsing the flags
        syn_flagg, ack_flagg, fin_flagg = parse_flags(flagg)

        # check if this is a fin message
        if fin_flagg == 2:
            #If fin packet connection will be closed
            close_connection_server(serverSocket, client_address)
            break
        
        elif seq == 40 and "skipack" in test:
            print("-----------DROP ACK 40-------------\n\n")
            test = "something else"
            

        #If its the packet in the right order -> add to main list
        elif seq == last_packet_added+1:
            
            #Add to the MAIN list
            data_list.append(data)
            print(f'Packet {seq} added to the LIST')
            last_packet_added+=1

            #adding the size of the packet to the total data
            sizedata+=len(packet)


            # Arguments in ack packet.
            ack_number = seq
            flagg = 4 # sets the ack flag

            #creates and send ACK-msg to server
            ack_packet = create_packet(sequence_number,ack_number,flagg,window,emptydata)
            serverSocket.sendto(ack_packet, client_address)
            print(f'Sent ack {ack_number}')

            #Updating helping variables
            sequence_number+=1
            next_expected_seq+=1

            #If buffer has packets in it
            if len(buffer) > 0:
                
                #Loops through all elements in buffer
                i=0
                while i < len(buffer):
                    p = buffer[i]
                    #If the packet is the next in main list, its added
                    if p.seq == last_packet_added+1:
                        buffer.remove(p)
                        data_list.append(p.data)
                        print(f'Packet {p.seq} added to the LIST')
                        last_packet_added+=1
                    else:
                        i+=1  
            
        #If pakcet is out of order -> add to buffer
        elif seq > next_expected_seq:

            #Creates an packet object, which is added into the buffer
            pack=One_Packet(seq,data)
            buffer.append(pack)
            print(f'Packet {seq} added to the BUFFER')

            #adding the size of the packet to the total data
            sizedata+=len(packet)

            # Arguments in ack packet.
            ack_number = seq
            flagg = 4 # sets the ack flag

            #creates and send ACK-msg to server
            ack_packet = create_packet(sequence_number,ack_number,flagg,window,emptydata)
            serverSocket.sendto(ack_packet, client_address)
            sequence_number+=1
            
            print(f'Sent ack {ack_number}')


        # In case of duplicates: if the packet already has been added to the
        elif seq < last_packet_added:
            
            # Arguments in ack packet.
            ack_number = seq
            flagg = 4 # sets the ack flag

            #creates and send ACK-msg to server
            ack_packet = create_packet(sequence_number,ack_number,flagg,window,emptydata)
            serverSocket.sendto(ack_packet, client_address)
            sequence_number+=1
            
            print(f'Sent ack {ack_number}')

    #Calculating the time
    endtime = time.time()
    totalduration=endtime-starttime
    
    #Sends to method that calcultates and prints througput
    throughput(sizedata,totalduration)

    

    filename = join_file(data_list,file_name)
    return filename


     

# ------------------------------------------------------------------------------#
#                                END OF SR                                      #
# ------------------------------------------------------------------------------#              
            

            




# ------------------------------------------------------------------------------#
#                                 Server side                                   #
# ------------------------------------------------------------------------------#

def connection_establishment_server(serverSocket, modus, filename, test):

    #Receives SYN packet from client
    SYN_from_client, client_Addr = serverSocket.recvfrom(2048) #returns the msg and the address

    #parsing the header
    SYN_seq, SYN_ack, SYN_flagg, SYN_win = parse_header(SYN_from_client)

    # check flags
    syn_flagg, ack_flagg, fin_flagg = parse_flags(SYN_flagg)
    if syn_flagg == 8: # if this is a SYN packet

        # create SYN ACK message
        data = b''
        sequence_number = 0
        acknowledgment_number = SYN_seq
        window = 0
        flags = 12 # SYN and ACK flags set here, and the decimal is 12

        # and send SYN-ACK back to client for confirmation
        SYN_ACK_packet = create_packet(sequence_number, acknowledgment_number, flags, window, data)
        serverSocket.sendto(SYN_ACK_packet, client_Addr) # send SYN ACK to client


        # receive that last ACK from client to establish a connection
        ACK_from_client, client_Addr = serverSocket.recvfrom(2048)

        #parsing the header, only to get flags
        ACK_seq, ACK_ack, ACK_flagg, ACK_win = parse_header(ACK_from_client) # only getting flags

        #Checks if its acknowledgement form the right packet
        if(ACK_ack==sequence_number):

            #parsing the flags
            ACK_syn_flagg, ACK_ack_flagg, ACK_fin_flagg = parse_flags(ACK_flagg)

            # check if this is a ACK message
            if ACK_ack_flagg == 4:
                print("got ACK from client!") # CAN DELETE
                print("Connection established with ", client_Addr)
                if 'GBN' in modus:
                    GBN_server(filename,serverSocket, test)
                if "SAW" in modus:
                    SAW_Server(filename, serverSocket,  test)
                elif "SR" in modus:
                    SR_server(serverSocket, filename, test)
            else:
                print("Error: ACK not received!")

        else:
            print("Error, Ack_number does not match")
    else:
        print("Error: SYN not received!")

    

    

def server_main(bind_IPadress, port, modus, filename, test):
    # erver_main(args.bind, args.port, args.modus, args.file, args.test, args.modus, args.file, args.test)
    server_host = bind_IPadress
    server_port = port
    serverSocket = socket(AF_INET, SOCK_DGRAM)
    
    # Handling binding process
    try:
        serverSocket.bind((server_host, server_port))
    except error:
        print("Bind failed. Error!!!")
        sys.exit()
    print("Server is ready to receive!!!")
    
    #sending socket to method thats establishing connection with client.
    connection_establishment_server(serverSocket, modus, filename, test)
        

            

        



# ------------------------------------------------------------------------------#
#                               End of server side                              #
# ------------------------------------------------------------------------------#









# ------------------------------------------------------------------------------#
#                                  Client side                                  #
# ------------------------------------------------------------------------------#

def connection_establishment_client(clientSocket, server_IP_adress, server_port, modus, filename, test, window_size, bonus):

    # Create a empty packet with SYN flag
    data = b''
    sequence_number = 0
    acknowledgment_number = 0
    window = 0
    flags = 8 # SYN flag set here, and the decimal is 8
    say_hi_to_server = create_packet(sequence_number, acknowledgment_number, flags, window, data)
    # done creating packet here

    #Sends packet to server
    clientSocket.sendto(say_hi_to_server, (server_IP_adress, server_port))
    
    rtt=roundtriptime(bonus, server_IP_adress)
    #set timeout
    clientSocket.settimeout(rtt)

    # wait for a response from the server
    try:
        #reveices packer from server
        syn_ack_from_server, serverAddr = clientSocket.recvfrom(2048)
        
        # since the SYN ACK packet from server contains no data, we can just extract the header right away
        seq, ack, flagg, win = parse_header(syn_ack_from_server)

        # Checks if the acknowledgement is for the right packet. 
        if sequence_number == ack:

            # parse flags
            syn_flagg, ack_flagg, fin_flagg = parse_flags(flagg)
            
            # check if SYN ACK packet from server has arrived. If yes, send ACK packet and confirm connection establishment
            if syn_flagg == 8 and ack_flagg == 4:
                # Sets a new sequence number and replies with ack number
                sequence_number=int(sequence_number)+1
                acknowledgment_number=seq

                #set the flag to represent ack_flag on
                flags = 4

                #creates an ACK packet
                ack_packet = create_packet(sequence_number, acknowledgment_number, flags, window, data)
                
                # Send ACK packet to server
                clientSocket.sendto(ack_packet, (server_IP_adress, server_port))
                print("Connection established!")
            
                #which modus the user wants to run in
                if modus == "SAW":
                    SAW_Client(filename, clientSocket, serverAddr, test, rtt)
                elif modus == "GBN":
                    GBN_client(window_size,filename,clientSocket,serverAddr, test, rtt)
                else:
                    SR_client(clientSocket, serverAddr, test, filename, window_size, rtt)
               
                
        
            else:
                raise socket.timeout("Error: SYN-ACK not received.") # can delete this?
    except timeout:
        print("Time out while waiting for SYN-ACK") 

def client_main(server_ip_adress, server_port, modus, filename, test, window_size,bonus):
    serverName = server_ip_adress
    serverPort = server_port

    # establish a UDP socket
    clientSocket = socket(AF_INET, SOCK_DGRAM)

    # sending the arguements in this method to establish a connection with server
    connection_establishment_client(clientSocket, serverName, serverPort, modus, filename,test, window_size,bonus)





# ------------------------------------------------------------------------------#
#                               Done client side                                #
# ------------------------------------------------------------------------------#
def check_ip(address): # check if IP adress is correct
    try:
       val = ipaddress.ip_address(address)
    except ValueError:
       print(f"The IP address {address} is not valid")
    return address

#check if port is valid. 
def check_port(val):
    try:
        #we try to convert the input value to an integer
        value = int(val) 
    except ValueError:
        #If it's not possible to convert to integer, we raise an ArgumentTypeError with an error message
        raise argparse.ArgumentTypeError("String was input, but expected an integer")
    #also check if the portnumber is in the valid range. if not we print error message.
    if(value<1024 or value>65535):
        print('it is not a valid port - port must be an integer and in the range 1024-65535')
        sys.exit() #Exit the program if not valid
    return value #if the portnumer is valid we return.

#Create an ArgumentParser instance  
parser= argparse.ArgumentParser(description="A client/server transfer application")

#Create an argument group for server arguments
group1= parser.add_argument_group('Server argumentns')
#Creates an argument group for client arguments
group2 = parser.add_argument_group('Client arguments')

#------------------------------------------SERVER ARGUMENTS--------------------------------------------------------------------#
group1.add_argument('-s', '--server', action='store_true', help='use this flag to run the program in server mode')
#bind argument with a check using the check_ip function implemented over
group1.add_argument('-b', '--bind', type=check_ip, default='127.0.0.1', help='IP-adress of the servers interface')
# ------------------------------------ Done argument for server ---------------------------------------------------------------#


#----------------------------------------- CLIENT ARGUMENTS -------------------------------------------------------------------#
group2.add_argument('-c', '--client', action='store_true', help='use this flag to run the program in client mode')
#serverip argument with a check using the checkip function implemented over
group2.add_argument('-I', '--serverip', default='127.0.0.1',type=check_ip, help='allows the user to select the IP address of the server' )
group2.add_argument('-w','--window', type=int, default=5, help='Specify window size')
group2.add_argument('-B','--bonus', action='store_true', help='use this flag to acitvate the bonus task where RTT is timeout')
# ------------------------------------ Done argument for Client ---------------------------------------------------------------#


#------------------------------ARGUMENTS THAT ARE ALLOWED TO USE ON BOTH SERVER AND CLIENT-------------------------------------#
#port argument with a check using the check_port function implemented over
parser.add_argument('-p', '--port', default=8088, type=check_port, help="Port number the server should listen to in server mode/ select server's port number in client mode")
parser.add_argument("-r", "--modus", choices=['SAW', 'GBN', 'SR'], help="Choose one of the modus!")

parser.add_argument("-f", "--file", help="File name ")
parser.add_argument('-t','--test', type=str, default="", help='use this flag to run the program test mode. On client: loss - On server: skipack')
# --------------------------------------- Done argument for Client/server ------------------------------------------------------------#


#Parse the arguments
args = parser.parse_args()


if args.server is False and args.client is False: # if none of -c or -s is used
    print("Error: you must run either in server or client mode")
    sys.exit()
elif args.server and args.client: # if both modes are used
    print("Error: you must run either in server or client mode")
    sys.exit()
elif args.modus is None:
    print("Error: you must choose modus")
elif args.file is None: # 
    print("Error: you must choose file argument")

else: # Pass the conditions. This is when one of the moduses is activated
    if args.server:
        server_main(args.bind, args.port, args.modus, args.file, args.test)
    else:
        client_main(args.serverip, args.port, args.modus, args.file, args.test, args.window,args.bonus)
