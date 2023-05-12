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
    #print (f'packet containing header + data of size {len(packet)}') # show the length of the packe

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

def roundtriptime(bonus,IPaddress):
    if bonus:
        rtt = ping3.ping(IPaddress)
        rtt = rtt*4
        if rtt is None:
            print(f"Failed to get round trip time from {IPaddress}")
            rtt = 0.5
        
    else:
        rtt=0.5

    return rtt

def throughput(sizedata, totalduration):
    size_bit= sizedata*8
    size_Mb=size_bit/1000
    
    throughput=size_Mb/totalduration
    throughput='{0:.2f}'.format(throughput)
    
    print('\n--------------------------------------')
    print(f'Throughput: {throughput} Mbps')
    print('--------------------------------------')

    print(f'size of data: {sizedata}')

class One_Packet:
    def __init__(self,seq, data):
        self.seq = seq
        self.data = data

    
    

# ------------------------------------------------------------------------------#
#                              END OF BONUS AND OTHER                           #
# ------------------------------------------------------------------------------#

# ------------------------------------------------------------------------------#
#                                Handle file                                    #
# ------------------------------------------------------------------------------#

def file_splitting(file_sent):
    list = []
    with open(str(file_sent), 'rb') as file:
        while True:
            data = file.read(1460) # take only 1460 bytes from picture
            if not data: # break if there is no more data
                break
            else:
                list.append(data) # add to an array
    return list

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

def close_connection_client(clientSocket, server_Addr):
    data = b''
    sequence_number = 0
    acknowledgement_number = 0
    window = 0
    flags = 2 # FIN flag are set to 1
    fin_packet = create_packet(sequence_number, acknowledgement_number, flags, window, data)
    clientSocket.sendto(fin_packet, server_Addr)

    try:
        close_msg, serverAddr = clientSocket.recvfrom(2048)
        seq, ack, flagg, win = parse_header(close_msg)
        syn_flagg, ack_flagg, fin_flagg = parse_flags(flagg)
        if ack_flagg + fin_flagg == 6: # check if this is ACK message #må endre her sånn at de forventer p fp fin-ack
            print("Close connection from client!!!")
    except error:
        print("Can not close at the moment!!!")

def close_connection_server(serverSocket, client_addr):
    # create ACK
    sequence_number = 0
    acknowledgment_number = 0
    window = 64000
    flagg = 6 # FIN and ack is set to 1 
    # and send FIN-ACK back to client for confirmation
    ACK_packet = create_packet(sequence_number, acknowledgment_number, flagg, window, b'')
    serverSocket.sendto(ACK_packet, client_addr) # send SYN ACK to client
    
    print("The transfer is done! Server close now!!!!")


# ------------------------------------------------------------------------------#
#                         Done close connection                                 #
# ------------------------------------------------------------------------------#




# ------------------------------------------------------------------------------#
#                                   GBN                                         #
# ------------------------------------------------------------------------------#



def GBN_client(window, filename, clientSocket, server_Address, test, rtt):
    data_list = file_splitting(filename)

    base = 0 #First i window and last ack to be recevied
    next_to_send = 0
    
    
    data = data_list[base]
    seq_number = next_to_send
    acknowledgement_number = 0
    flags = 0
    datasize=0

    while base < len(data_list): #MÅ HA NOE ANNET ENN TRUE?

         #If packet 44 its dropped and skip one round
        if next_to_send == 44 and "loss" in test: ##SJEKK OM DET GÅR MED str(test) og at den da ikke trenger å ha default i argumentet
            print('\n\nDropper pakke nr 44\n') #SØRG FOR AT DEN FORTSATT SENDER OG IKKE HOPPER OVER DENNE SENDINGEN
            next_to_send+=1
            test = "something else"
       
        #If not packet 44, we send normally
        else:
            
            #Sends packets until the window is full, as long as there is more packet to be sent 
            while next_to_send < base + window and next_to_send < len(data_list):

            
                #Ssend packet    
                
                seq_number=next_to_send
                # Creating and sending packet
                data = data_list[seq_number] #getting packets to send in the right order
                packet = create_packet(seq_number,acknowledgement_number,flags,window,data) 
                clientSocket.sendto(packet,server_Address) 
                print(f'Sendt seq: {seq_number}')

                datasize+=len(packet)
                #Updates next packet to send, and seq number
                next_to_send+=1

            # The window is full - now we wait on ack to move the window

            clientSocket.settimeout(rtt)
            
            try:
                #reveices ack from server
                ack_from_server, serverAddr = clientSocket.recvfrom(2048)
                
                # parsing the header since the ack packet should be with no data
                seq, ack, flagg, win = parse_header(ack_from_server)
                print(f'Fikk ack: {ack}\n')

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
    
    print('Lengden av data listen: '+str(len(data_list)))
    print('Lengden av datafilen: ',datasize)
    close_connection_client(clientSocket, server_Address)




def GBN_server(filename, serverSocket, test): 
    data_list = []

    emptydata=b''
    sequence_number = 0
    ack_number = 0
    window = 64000
    flagg = 0
    last_packet_added = -1
    last_ack_sent = -1

    #Marking start time
    starttime=time.time()

    #varibale for amount data received
    sizedata=0

    while True:

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

       
        # A packet should not be added if the ack of the pacet before got sent.
        # therefore this if checks:    
        #   1. to se if packets come in the right order
        #   2. to se if the packet has been added before
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

         # If at packet nr. 13, we skip sending the ack (the ack got lost).
        else:
            print(f"Throws packet {seq} away")
        
        if seq == 21 and "skipack" in test:
            print('\n\nDroppet ack nr 21\n\n')
            
            # set to false so that the skip only happens once.
            test = "something else"
            
        else:
            # Check to make sure to send ack if:
                # If the packet already has been recv and added to the list
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
                
                print('Sent ack packet: '+str(ack_number))
                print('')
            
            #sets test to false so packet number 5 does not get skipped. 
            
    #Calculating the time
    endtime = time.time()
    totalduration=endtime-starttime
    
    #Sends to method that calcultates and prints througput
    throughput(sizedata,totalduration)

    filename = join_file(data_list,filename)
    """   
    #Tekst fil skrive ut
    
    f = open(filename, 'r')
    file_content = f.read()
    print(file_content)
    
    

    try:
        # Åpne bildet
        img = Image.open(filename)

        # Skriv ut bildet i terminalen
        img.show()

    except IOError:
        print("Kan ikke åpne bildefilen")

    """
        

    



# ------------------------------------------------------------------------------#
#                                 End of GBN                                    #
# ------------------------------------------------------------------------------#







# ------------------------------------------------------------------------------#
#                                 STOP AND WAIT                -                #
# ------------------------------------------------------------------------------#

def SAW_Client(filename,clientSocket,serverAddr, test,rtt):
    #Data_list contains data packets
    data_list = file_splitting(filename)

    #starts at 0 
    sequence_id = 0

   
    #Send data as long as the data_list is not empty
    while sequence_id < len(data_list):
        
        acknowledgement_number = 0
        window = 0 
        flags = 0

        #test - drop ack
        if sequence_id == 30 and "loss" in test:
                print('\n\n Dropper pakke nr 30\n\n')
                sequence_id+=1
                test = "something else"
                
        #else:
            #creating packet, and sending
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
                print('Fikk ack: '+str(ack))

                # Check if it has ack flagg marked
                if ack_flagg == 4:
                    #Sequence increases whit 1 if we received the rigth packet
                    sequence_id+=1
            else:
                #if a packet is dropped, server sneds dupack, and we calculate which packet we send next.
                sequence_id=ack+1
                print('\n\n received dupack: ', str(ack) , '\n\n')
               
                
       
       #if timeout, the sequence number should not be changed. We send packet
        except timeout:
            
            print("Error: Timeout")
                
    close_connection_client(clientSocket, serverAddr)

def SAW_Server(filename,serverSocket, test):
    #list with the data
    data_list = [] 

    emptydata=b''
    sequence_number = 0
    ack_number = 0
    window = 0
    flagg = 0
    last_ack_number = -1

    #Marking start time
    starttime=time.time()

    #varibale for amount data received
    sizedata=0

    while True:
        #waits for packets
        packet, client_address = serverSocket.recvfrom(2048)
        
        #adding the size of the packet to the total data
        sizedata+=len(packet)

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

    filename = join_file(data_list,filename)

    try:
        # Open picture
        img = Image.open(filename)

        # Skriv ut bildet i terminalen
        img.show()

    except IOError:
        print("Kan ikke åpne bildefilen")

# ------------------------------------------------------------------------------#
#                           End of stop and wait                                #
# ------------------------------------------------------------------------------#





# ------------------------------------------------------------------------------#
#                                   SR                                          #
# ------------------------------------------------------------------------------#
 
def SR_client(clientSocket, server_Addr, test, file_sent, window_size,rtt):
    # data list from file
    raw_datalist = file_splitting(file_sent) # array contains raw data

    formatted_packets_list = []

    for i in range(len(raw_datalist)): # create a new list containing different packets
        formatted_packets_list.append({ # each packet has seq_num, data and ack value
            "seq_num": i,
            "data": raw_datalist[i],
            "acked": False
        })


    WINDOW_SIZE = window_size # window size
    base = 0 # base a.k.a "first" packet in window
    next_to_send = 0 # next packet in window

    clientSocket.settimeout(rtt)

    # loop through data list 
    while base < len(raw_datalist):
        
        # and send packets within WINDOW_SIZE
        while next_to_send < base + WINDOW_SIZE and next_to_send < len(formatted_packets_list): 
            
            if "loss" in test and next_to_send == 3: # drop packet test
                next_to_send += 1
                print("drop pakke 3")
                test = "something else"
                
            # send all packets in this window
            else:
                # create packet
                data = formatted_packets_list[next_to_send]["data"]
                sequence_number = formatted_packets_list[next_to_send]["seq_num"]
                acknowledgement_number = 0
                window = 0
                flagg = 0
                my_packet = create_packet(sequence_number, acknowledgement_number, flagg, window, data)
                
                clientSocket.sendto(my_packet, server_Addr) # send packet here
                print(f"sent packet {sequence_number}")
                next_to_send += 1 # move to the next packet in window after sending
        # done sending all packets in that specific window
        
        # wait for ACKs packets that has been sent
        try:
            print("\n\n")
            ack_from_server, server_address = clientSocket.recvfrom(2048)
            
            # parsing header
            seq, ack, flags, win = parse_header(ack_from_server)
            print(f"receive ack {ack} from server")
            for packet in formatted_packets_list: # go through all packets in list
                if packet["seq_num"] == ack: # if packet has received its own ACK
                    syn_flagg, ack_flagg, fin_flagg = parse_flags(flags)
                    
                    # check if this is ACK flagg
                    if ack_flagg == 4:    
                        packet["acked"] = True # mark packets as ACKed 
                        break # continue to check other packets 
            
            # After marking ACKed for packets, we update the base of window to next value
            while base < len(formatted_packets_list) and formatted_packets_list[base]["acked"]:
                base += 1
               

        except timeout: # resend unACKed packets in window
            for packet in formatted_packets_list[base:base+WINDOW_SIZE]: # Go through the slice of list where from the index of base --> base + WINDOW_SIZE
                if packet["seq_num"] < next_to_send and not packet["acked"]: # resend packets that have not been ACKed
                    
                    # create packet
                    data = packet["data"]
                    sequence_number = packet["seq_num"]
                    acknowledgement_number = 0
                    window = 0
                    flagg = 0
                    my_packet = create_packet(sequence_number, acknowledgement_number, flagg, window, data)
                    clientSocket.sendto(my_packet, server_Addr)
                    print(f"\nresend packet {sequence_number} because of unACKed in window") # print out info
                    

                    # ------------------------------------------------------------------------------------------------------------#

                    # After sending, we have to wait to get ACK message from the newly sent packet before moving to the next window              
                    ack_from_server, server_address = clientSocket.recvfrom(2048)

                    # parsing header
                    seq, ack, flags, win = parse_header(ack_from_server)
                    print(f"receive ack {ack} from server")
                    for packet in formatted_packets_list: # go through all packets in list
                        if packet["seq_num"] == ack: # if packet has received its own ACK
                            syn_flagg, ack_flagg, fin_flagg = parse_flags(flags)

                            # check if this is ACK flagg
                            if ack_flagg == 4:    
                                packet["acked"] = True # mark packets as ACKed
                                base += 1 # update base to the newest value since it has ignored the lost packet            
                                break # continue to check other packets
        
    close_connection_client(clientSocket, server_Addr)


def SR_server(serverSocket, file_name, test):
    #list with the data and buffer
    data_list = [] 
    buffer = []
    seq_list = []


    #For sending ack packet
    emptydata=b''
    sequence_number = 0
    ack_number = 0
    window = 0
    flagg = 0
    

    

    #varibale for amount data received
    sizedata=0

    #helping variable
    next_expected_seq = 0
    last_packet_added = -1
    last_ack_number = -1

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
            data_list.append(data)
            print(f'Packet {seq} added to the list')
            last_packet_added+=1

            #adding the size of the packet to the total data
            sizedata+=len(packet)


            seq_list.append(seq)

            # Arguments in ack packet.
            ack_number = seq
            flagg = 4 # sets the ack flag

            #creates and send ACK-msg to server
            ack_packet = create_packet(sequence_number,ack_number,flagg,window,emptydata)
            serverSocket.sendto(ack_packet, client_address)
            sequence_number+=1
            next_expected_seq+=1


            print(f'Sent ack {ack_number}')

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
                        seq_list.append(p.seq)
                        print(f'Packet {p.seq} added to the list')
                        last_packet_added+=1
                    else:
                        i+=1
                    print(f'Buffer has {len(buffer)} elements')
            #print(f"Current seq list: {seq_list}")
                    
            
            
        #If out of order -> add to buffer
        elif seq > next_expected_seq:

            pack=One_Packet(seq,data)
            buffer.append(pack)

            #adding the size of the packet to the total data
            sizedata+=len(packet)



            print(f'Packet {seq} added to the buffer')
            
            # Arguments in ack packet.
            ack_number = seq
            flagg = 4 # sets the ack flag

            #creates and send ACK-msg to server
            ack_packet = create_packet(sequence_number,ack_number,flagg,window,emptydata)
            serverSocket.sendto(ack_packet, client_address)
            sequence_number+=1
            
            print(f'Sent ack {ack_number}')


        #If the packet already has been added to the 
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

    print('Total data: ',sizedata)
    print('Total time: ',totalduration)

    filename = join_file(data_list,file_name)
    try:
        # Open picture
        img = Image.open(filename)

        # Skriv ut bildet i terminalen
        img.show()

    except IOError:
        print("Kan ikke åpne bildefilen")
    
    """
    try:
        # Open picture
        img = Image.open(filename)

        # Skriv ut bildet i terminalen
        img.show()

    except IOError:
        print("Kan ikke åpne bildefilen")
    
    """


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