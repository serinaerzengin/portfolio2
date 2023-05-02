from socket import *
from struct import *
import argparse
import ipaddress
import sys
from PIL import Image
import random
from PIL import Image
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
#                                Handle file                                    #
# ------------------------------------------------------------------------------#

def file_splitting(file_sent):
    list = []
def file_splitting(file_sent):
    list = []
    with open(str(file_sent), 'rb') as file:
        while True:
            data = file.read(1460) # take only 1460 bytes from picture
            list.append(data) # add to an array
            if not data: # break if there is no more data
                break
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
#                                 GBN                                           #
# ------------------------------------------------------------------------------#



def GBN_client(window, filename, clientSocket, server_Address, test):
    data_list = file_splitting(filename)

    sequence_id = 0
    first_in_window = 0
    next_in_window = 0
    window=5
    print('Lengden av data listen: '+str(len(data_list)))
    
    data = data_list[sequence_id]
    seq_number = sequence_id
    acknowledgement_number = 0
    #window = 0 # sende med window = 0 eller window = window? Er det bare server som skal sende window?
    flags = 0
    
    
    while sequence_id < len(data_list):
        seq_number = sequence_id
        next_in_window=first_in_window
        packets_in_window = next_in_window - first_in_window

        #Tries to send the rest of the packets in the window, before getting ack from the first in window. 
        #print('Packets in window: '+str(packets_in_window)+' window: '+str(window)+'\n first in window: ' +str(first_in_window)+ ', next in window:'+ str(next_in_window)+'\nseq number: '+str(seq_number))
        
        while packets_in_window < window and seq_number < len(data_list):

            #The while arguments ^:
            #Can only send packets if there is room in the window
            #Cannot send data if there is no data left in the list
            if seq_number == 16 and test:
                print('\n\n Dropper pakke nr 16')
                seq_number+=1
                test = False
            else:    
                # Creating and sending packet
                data = data_list[seq_number] #getting packets to send in the right order
                packet = create_packet(seq_number,acknowledgement_number,flags,window,data) 
                clientSocket.sendto(packet,server_Address) 
                print('Sendt seq: '+str(seq_number))

                #After sending packet, we update:
                # whats nest posision in the window
                # how many packets in the window and 
                # the seq_number of the next packet
                next_in_window+=1
                
                packets_in_window =  next_in_window - first_in_window
                
                seq_number +=1

            # The window should be full - now we wait on ack to move the window
        
        print('TRYING TO GET ACK FROM SERVER')
        # Try to receive an ack for the sent packets
        clientSocket.settimeout(0.5)
        try:    
            while True: #Receiving ack from server
                #reveices packer from server
                ack_from_server, serverAddr = clientSocket.recvfrom(2048)

                # parsing the header since the ack packet should be with no data
                seq, ack, flagg, win = parse_header(ack_from_server)
                print('Fikk ack: '+str(ack))

                # Checks if the acknowledgement is for the right packet. 
                # The ack should be for the first packet in the window. 
                if  first_in_window == ack:
                    # parse flags
                    syn_flagg, ack_flagg, fin_flagg = parse_flags(flagg)

                    # Check if it has ack flagg marked
                    if ack_flagg == 4:
                        # sequence number oker for neste pakke
                        sequence_id += 1 #the next in sequence_id will be the next packet to be send
                        first_in_window+=1 # we move the window
                else:
                    print('Break, fordi '+str(first_in_window)+' er ikke det samme som '+ str(ack))
                    break
        except timeout:
            print("Error: Timeout")
    


    seq_number=0
    acknowledgement_number=0
    flagg=2
    emptydata=b''
    fin_packet = create_packet(seq_number,acknowledgement_number,flagg,window,emptydata)
    clientSocket.sendto(fin_packet,server_Address) 
    print('Sendt fin packet')

    #METHOD TO CLOSE CONNECTION??


def stop_and_wait_client(file_sent, clientSocket, server_IPadress, server_port, test):
    # Array contains data packet
    data_list = file_splitting(file_sent) # split file to smaller parts
    
    sequence_id = 0 # sequence id of packet
    last_ack_from_server = 0
    total_sent = 0 # testing purpose. Can delete
    while sequence_id < len(data_list): # while amount of sent packets is smaller than total packets

        if "Loss" in test and sequence_id == 4: # if Loss is defined in -t tag!
            print(f"Drop packet number {sequence_id}")
            sequence_id += 2
            test = "drop"

        # create new packet 
        data = data_list[sequence_id] # get packet with the corresponding seq number from array
        sequence_number = sequence_id
        acknowledgement_number = 0
        window = 0
        flags = 0

        clientSocket.settimeout(0.5) # set timeout for sending packet
        # Dealing with packet loss
        try:
            my_packet = create_packet(sequence_number, acknowledgement_number, flags, window, data)
            clientSocket.sendto(my_packet, (server_IPadress, server_port)) # send packets til server
            print(f"packet {sequence_id} sent!!!") 
        except timeout:
            sequence_id = sequence_number # resend packet


        
        clientSocket.settimeout(0.5) # set timeout for ACK message from server
        try:
            # wait for an ACK from server to confirm packet
            packet_from_Server, serverAddr = clientSocket.recvfrom(2048)

            seq, ack, flagg, win = parse_header(packet_from_Server)

            # check if sender receives the right message 
            if sequence_number == ack: # if sender1 gets receiver1 

                # parse flags
                syn_flagg, ack_flagg, fin_flagg = parse_flags(flagg)

                if ack_flagg == 4: # check if this is ACK message
                    # get ready for new packet
                    sequence_id += 1 # sequence number oker for neste pakke
                    last_ack_from_server = ack # store ack of the last received sequence
                    total_sent += len(data) # testing. CAN DELETE
                else: # if this is not an ACK message
                    print("This is not an ACK message!")

            elif sequence_number > ack: # if sender1, 2 and 3 have been sent -> sender4 should be sent
                # However, if sender6 sends instead because of wrong order --> server will send DUPACK of ack3
                
                # this is DUPACK by if ACK number of this new message is equal to ack of the last received sequence 
                print(ack)
                if last_ack_from_server == ack: # if this is DUPACK
                    sequence_id = ack + 1 # then sender4 will be sent instead.
                    # This is because if sender(6) is sent instead of sender(4) -> packets are not sent in the right order
                    # receiver will assign a DUPACK asking sender to resend the right packet. For more details, check SAW server
                    print(f"resend packet {sequence_id}")

            else: # test. Can remove this and change elif to else instead...
                print(f"Current sequence number from client: {sequence_number}")
                print(f"Current sequence number from server: {seq}")
                time.sleep(3)

        except timeout: # Dealing with packet loss (of ack)
            # if sender1 has not gotten its receiver1 (ack1) --> resend sender1 to receiver1
            print(f"Time out while waiting for ACK {sequence_number}")
            sequence_id = sequence_number # resend packet 
            print(f"Resend packet {sequence_id} now")
        clientSocket.settimeout(None) # reset timeout

        
        
    
    # transferring is done. Sent FIN-packet
    data = b''
    sequence_number = 0
    acknowledgement_number = 0
    window = 0
    flags = 2
    fin_packet = create_packet(sequence_number, acknowledgement_number, flags, window, data)
    clientSocket.sendto(fin_packet, (server_IPadress, server_port))
    
    try:
        close_msg, serverAddr = clientSocket.recvfrom(2048)
        seq, ack, flagg, win = parse_header(close_msg)
        syn_flagg, ack_flagg, fin_flagg = parse_flags(flagg)
        if ack_flagg == 4: # check if this is ACK message
            print("Close connection from client!!!")
            print(f"Total transferred: {total_sent}")
    except error:
        print("Can not close at the moment!!!")
        


def stop_and_wait_server(serverSocket, file_name, test):
    data_received = []
    total_received = 0
    ack_number_of_server = 0
    last_ACK_msg = 0

    while True:
        try: 
            # Receives packet from client
            client_msg, client_Addr = serverSocket.recvfrom(2048)

            header_from_msg = client_msg[:12]

            # parse header
            seq, ack, flags, win = parse_header(header_from_msg)

            # if server got Fin-packet, the transfer is done
            syn_flagg, ack_flagg, fin_flagg = parse_flags(flags)
            
            if fin_flagg == 2:
                # send ack
                data = b''
                sequence_number = 0
                acknowledgment_number = 0
                window = 0
                flagg = 4 # ACK flag sets here, and the decimal is 4

                # and send ACK back to client for confirmation
                ACK_packet = create_packet(sequence_number, acknowledgment_number, flagg, window, data)
                serverSocket.sendto(ACK_packet, client_Addr) # send SYN ACK to client

                print(f"Total transferred: {total_received}")
                print("The transfer is done! Server close now!!!!")
                
                break

            data_from_msg = client_msg[12:]
            if "skip_ack" in test and ack_number_of_server == 35:
                print(f"drop ack {ack_number_of_server}")
                ack_number_of_server += 1 # testing. CAN DELETE
                
                test = "back"
            elif seq == ack_number_of_server: # if packet is ok
                
                total_received += len(data_from_msg) # testing only. CAN DELETE
                data_received.append(data_from_msg)
                
                print(f"fikk pakke {seq} from client") # CAN DELETE 

                # create ACK message
                data = b''
                sequence_number = 0
                acknowledgment_number = ack_number_of_server
                window = 0
                flagg = 4 # ACK flag sets here, and the decimal is 4
                last_ACK_msg = acknowledgment_number # store ACK of last message

                # and send ACK back to client for confirmation
                ACK_packet = create_packet(sequence_number, acknowledgment_number, flagg, window, data)
                serverSocket.sendto(ACK_packet, client_Addr) # send ACK to client
                print(f"return ack packet {acknowledgment_number} !!!") # CAN DELETE
                ack_number_of_server += 1 # get ready for the next message from client
            elif ack_number_of_server > seq: # if ACK message is dropped/skipped (seq of client is 35 and seq of ACK message from server is already 36) --> resend ACK 35 to sender
                total_received += len(data_from_msg) # testing only. CAN DELETE
                data_received.append(data_from_msg)
                
                print(f"fikk pakke {seq} from client") # CAN DELETE 

                # create ACK message
                data = b''
                sequence_number = 0
                acknowledgment_number = seq
                window = 0
                flagg = 4 # ACK flag sets here, and the decimal is 4
                last_ACK_msg = acknowledgment_number # store ACK of last message

                # and send ACK back to client for confirmation
                ACK_packet = create_packet(sequence_number, acknowledgment_number, flagg, window, data)
                
                serverSocket.sendto(ACK_packet, client_Addr) # send ACK 35 to client
                print(f"return ack packet {acknowledgment_number} !!!") # CAN DELETE
                ack_number_of_server = seq + 1 # ACK message 35 is now sent -> get ready for the next message from client (ACK message 36)
            else: # if packet is not OK (wrong order for instance a.k.a ack_server < seq_client) ---> Send DUPACK
                data = b''
                sequence_number = 0
                acknowledgment_number = last_ACK_msg
                window = 0
                flagg = 4 # ACK flag sets here, and the decimal is 4
                # and send ACK back to client for confirmation
                ACK_packet = create_packet(sequence_number, acknowledgment_number, flagg, window, data)
                serverSocket.sendto(ACK_packet, client_Addr) # send ACK to client
        except error:
            print("Have not received any packet from client")
    myfile = join_file(data_received, file_name)
    img = Image.open(myfile)
    img.show()
    
 
def SR_client(clientSocket, server_Addr, test, file_sent, window_size):
    # data list from file
    raw_datalist = file_splitting(file_sent) # array contains raw data

    total_sent = 0 # testing CAN DELETE

    formatted_packets_list = []

    for i in range(len(raw_datalist)): # create a new list containing different packets
        formatted_packets_list.append({ # each packet has seq_num, data and ack value
            "seq_num": i,
            "data": raw_datalist[i],
            "acked": False
        })


    WINDOW_SIZE = window_size # window size
    first_in_wd = 0 # base a.k.a "first" packet in window
    next_in_wd = 0 # next packet in window
    base = 0 # keep track of window
    clientSocket.settimeout(0.5)
    # loop through data list and send packets within WINDOW_SIZE
    while first_in_wd < len(raw_datalist):
        # send packets in window size
        print("\n\n")
        for packet in formatted_packets_list[first_in_wd:first_in_wd+WINDOW_SIZE]: # extract a slice of the data_list. F.eks if base = 0 --> extract packet 0,1,2,3,4
            
            if "Loss" in test and packet["seq_num"] == 8: # drop packet test
                next_in_wd += 1
                print("drop pakke 8")
                test = "hihi"
                
            # send all packets in this window
            if packet["seq_num"] >= next_in_wd: 
                # create packet
                data = packet["data"]
                sequence_number = packet["seq_num"]
                acknowledgement_number = 0
                window = 0
                flagg = 0
                my_packet = create_packet(sequence_number, acknowledgement_number, flagg, window, data)
                
                

                # should have a try catch here to handle packet loss
                clientSocket.sendto(my_packet, server_Addr)
                print(f"sent packet {sequence_number}")
                total_sent += len(data) # TESTING CAN DELETE
                next_in_wd += 1 # move to the next packet in window
        # done sending all packets in that specific window
        
        # wait for ACKs from all packets that has been sent
        try:
            print("\n\n")
            while True:                
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
                
                # after marking all packets that has been ACKed
                # we will update first_in_window to last ACKed packet
                while first_in_wd < len(formatted_packets_list) and formatted_packets_list[first_in_wd]["acked"]:
                    first_in_wd += 1 

        except timeout: # resend unACKed packets in window
            for packet in formatted_packets_list[base:base+WINDOW_SIZE]: # go through and handle the same list using base!!!
                if packet["seq_num"] < next_in_wd and not packet["acked"]: # resend packet that has not been ACKed
                    
                    # create packet
                    data = packet["data"]
                    sequence_number = packet["seq_num"]
                    acknowledgement_number = 0
                    window = 0
                    flagg = 0
                    my_packet = create_packet(sequence_number, acknowledgement_number, flagg, window, data)
                    clientSocket.sendto(my_packet, server_Addr)
                    print(f"resend packet {sequence_number} because of unACKed in window") # print out info
                    total_sent += len(data) # TESTING CAN DELETE
                    # while True: brukes naar man mister mange pakker?

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
                                break # continue to check other packets
                    while first_in_wd < len(formatted_packets_list) and formatted_packets_list[first_in_wd]["acked"]:
                        first_in_wd += 1 # update first in window since it has ignored the lost packet
            base = first_in_wd # update base to the next new window
    
    print("Done transferring")
    # transferring is done. Send FIN-packet
    data = b''
    sequence_number = 0
    acknowledgement_number = 0
    window = 0
    flags = 2
    fin_packet = create_packet(sequence_number, acknowledgement_number, flags, window, data)
    clientSocket.sendto(fin_packet, server_Addr)
    # Get ACK message and close connection
    try:
        close_msg, serverAddr = clientSocket.recvfrom(2048)
        seq, ack, flagg, win = parse_header(close_msg)
        syn_flagg, ack_flagg, fin_flagg = parse_flags(flagg)
        if ack_flagg == 4: # check if this is ACK message
            print("Close connection from client!!!")
            print(f"Total transferred: {total_sent}")
    except error:
        print("Can not close at the moment!!!")


def SR_server(serverSocket, file_name, test):
    data_list = []
    empty_data = b''
    total_received = 0
    last_ack_sent = -1
    seq_list = [] #TESTING, CAN DELETE
    
    while True:
        # get data packet from client
        try:
            packet, client_addr = serverSocket.recvfrom(2048)
            
            # extract header
            header = packet[:12]

            # extract data
            data_from_msg = packet[12:]

            # parsing header
            seq, ack, flags, win = parse_header(header)        
            # parse flags
            syn_flagg, ack_flagg, fin_flagg = parse_flags(flags)

            if fin_flagg == 2: # close signal from client
                
                # create ACK
                sequence_number = 0
                acknowledgment_number = 0
                window = 64000
                flagg = 4 # ACK flag sets here, and the decimal is 4

                # and send ACK back to client for confirmation
                ACK_packet = create_packet(sequence_number, acknowledgment_number, flagg, window, empty_data)
                serverSocket.sendto(ACK_packet, client_addr) # send SYN ACK to client

                print(f"Total transferred: {total_received}")
                print("The transfer is done! Server close now!!!!")
                
                break

            elif seq == 100 and "skip_ack" in test: # DROP ACK TESTING
                print("drop ack 100")
                test = "hihi"
                last_ack_sent += 1 # Skip to the next ACK message
            
            elif seq >= last_ack_sent + 1: # Rather than throwing away packets that arrive in the wrong order, still put the packets in the list
                print(f"receive packet with seq: {seq}")

                # send ack
                sequence_number = 0
                acknowledgment_number = seq
                window = 64000
                flagg = 4
                total_received += len(data_from_msg) # TESTING. CAN DELETE
                
                ACK_packet = create_packet(sequence_number, acknowledgment_number, flagg, window, empty_data)
                serverSocket.sendto(ACK_packet, client_addr)
                last_ack_sent += 1 # confirm that packet has been sent

                
                # add packet to list
                data_list.append(data_from_msg)
                seq_list.append(acknowledgment_number) # TESTING, CAN DELETE

                print(f"Current seq list: {seq_list}") # TESTING, CAN DELETE
                print("\n\n") # TESTING, CAN DELETE
            else: # if seq from client is 4 (resend since it is dropped) while last_ack_sent is 5 
                # --> server has received packets 5 and 6 while 4 has not arrived yet
                # --> put seq 4 in correct order
                print(f"receive packet with seq: {seq}") # TESTING, CAN DELETE
                data_list.insert(seq, data_from_msg) 
                seq_list.insert(seq, seq) # TESTING, CAN DELETE
                print(f"Current seq list: {seq_list}") # TESTING, CAN DELETE
                print("\n\n") # TESTING, CAN DELETE

                # return ACK of that missing packet to client
                sequence_number = 0
                ack_number = seq
                window = 64000
                flagg = 4
                total_received += len(data_from_msg) # TESTING. CAN DELETE
                ACK_packet = create_packet(sequence_number, ack_number, flagg, window, empty_data)
                serverSocket.sendto(ACK_packet, client_addr)
                last_ack_sent += 1 # confirm that packet has been sent
        except error:
            print("have problem with receiving data")
    myfile = join_file(data_list, file_name)
    img = Image.open(myfile)
    img.show()

                
            

            


def GBN_server(window, filename, serverSocket, test): #do we need window?
    data_list = []

    emptydata=b''
    sequence_number = 0
    ack_number = 0
    window = window
    flagg = 0
    last_packet_added = -1
    last_ack_sent = -1

    

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
            print("Finished receivind packets")
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

            #update last packet added to the list
            last_packet_added+=1

         # If at packet nr. 13, we skip sending the ack (the ack got lost).
        if seq == 13 and test:
            print('\n\nDroppet ack nr 13\n\n')
            
            # set to false so that the skip only happens once.
            test = False
            
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
            


    filename = join_file(data_list,filename)
    """   
    #Tekst fil skrive ut
    
    f = open(filename, 'r')
    file_content = f.read()
    print(file_content)
    
    """

    try:
        # Åpne bildet
        img = Image.open(filename)

        # Skriv ut bildet i terminalen
        img.show()

    except IOError:
        print("Kan ikke åpne bildefilen")
        

    # METHOD TO CLOSE CONNECTION?



# ------------------------------------------------------------------------------#
#                                End of GBN                                     #
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
                    GBN_server(window,filename,serverSocket, test)
                if "SAW" in modus:
                    stop_and_wait_server(serverSocket, file_name, test)
                elif "SR" in modus:
                    SR_server(serverSocket, file_name, test)
            else:
                print("Error: ACK not received!")

        else:
            print("Error, Ack_number does not match")
    else:
        print("Error: SYN not received!")

    

    

def server_main(bind_IPadress, port, modus, filename, test):
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

def connection_establishment_client(clientSocket, server_IP_adress, server_port, modus, filename, test, window_size):

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
    
    #set timeout
    clientSocket.settimeout(0.5)

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
                    stop_and_wait_client(file_sent, clientSocket, server_IP_adress, server_port, test)
                elif modus == "GBN":
                    GBN_client(window,filename,clientSocket,serverAddr, test)
                else:
                    SR_client(clientSocket, serverAddr, test, file_sent, window_size)
               
                
        
            else:
                raise socket.timeout("Error: SYN-ACK not received.") # can delete this?
    except timeout:
        print("Time out while waiting for SYN-ACK") 

def client_main(server_ip_adress, server_port, modus, filename, test, window_size):
    serverName = server_ip_adress
    serverPort = server_port

    # establish a UDP socket
    clientSocket = socket(AF_INET, SOCK_DGRAM)

    # sending the arguements in this method to establish a connection with server
    connection_establishment_client(clientSocket, serverName, serverPort, modus, filename,test, window_size)





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
group2.add_argument('-w','--window', type=int, help='Specify window size')
# ------------------------------------ Done argument for Client ---------------------------------------------------------------#


#------------------------------ARGUMENTS THAT ARE ALLOWED TO USE ON BOTH SERVER AND CLIENT-------------------------------------#
#port argument with a check using the check_port function implemented over
parser.add_argument('-p', '--port', default=8088, type=check_port, help="Port number the server should listen to in server mode/ select server's port number in client mode")
parser.add_argument("-r", "--modus", choices=['SAW', 'GBN', 'SR'], help="Choose one of the modus!")

parser.add_argument("-f", "--file", help="File name ")
parser.add_argument('-t','--test', action='store_true', help='use this flag to run the program test mode which looses a packet')
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
        server_main(args.bind, args.port, args.modus, args.file, args.test, args.modus, args.file, args.test)
    else:
        client_main(args.serverip, args.port, args.modus, args.file, args.test, args.window)
