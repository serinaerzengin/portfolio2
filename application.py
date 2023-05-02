from socket import *
from struct import *
import argparse
import ipaddress
import sys
from PIL import Image
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
                print("got ACK from client!")
                print("Connection established with ", client_Addr)
                if 'GBN' in modus:
                    GBN_server(window,filename,serverSocket, test)
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

def connection_establishment_client(clientSocket, server_IP_adress, server_port, modus, filename, test):

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
                print("got SYN ACK from server")

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
                    print('Må kalle funksjon')
                elif modus == "GBN":
                    GBN_client(window,filename,clientSocket,serverAddr, test)
                else:
                    print('Må kalle funksjon')
               
                
        
            else:
                raise socket.timeout("Error: SYN-ACK not received.") # can delete this?
    except BaseException as e:
        print("Time out while waiting for SYN-ACK", e) 

def client_main(server_ip_adress, server_port, modus, filename, test):
    serverName = server_ip_adress
    serverPort = server_port

    # establish a UDP socket
    clientSocket = socket(AF_INET, SOCK_DGRAM)

    # sending the arguements in this method to establish a connection with server
    connection_establishment_client(clientSocket, serverName, serverPort, modus, filename, test)





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
elif args.file is None:
    print("Error: you must choose file argument")

else: # Pass the conditions. This is when one of the modes is activated
    if args.server:
        server_main(args.bind, args.port, args.modus, args.file, args.test)
    else:
        client_main(args.serverip, args.port, args.modus, args.file, args.test)
