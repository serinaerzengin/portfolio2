from socket import *
from struct import *
import argparse
import ipaddress
import sys
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


def stop_and_wait_client(file_sent):
    
    data_list = []
    file_splitting(data_list, file_sent)
    sequence_id = 0

    for i in range(len(data_list)):
        return
        
                    
        



def stop_and_wait_server():
    return 0



def GBN_client(window, filename, clientSocket, server_Address):
    data_list = file_splitting(filename)

    sequence_id = 0
    first_in_window = 0
    next_in_window = 0
    window=5

    while sequence_id < len(data_list):
        data = data_list[sequence_id]
        seq_number = sequence_id
        acknowledgement_number = 0
        window = 0 # sende med window = 0 eller window = window? Er det bare server som skal sende window?
        flags = 0

        packet = create_packet(seq_number,acknowledgement_number,flags,window,data)
        clientSocket.sendto(packet,server_Address)
        next_in_window+=1
        clientSocket.settimeout(0.5) #Vil denne gjelde receiving av pakke nede i den 2. whilen eller hvis den stoppe før?
        

        try:
            packets_in_window = first_in_window-next_in_window

            #Tries to send the rest of the packets in the window, before getting ack from the first in window. 
            while packets_in_window < window and seq_number < len(data_list):

                #Making the new packet to send
                data = data_list[seq_number]
                packet = create_packet(seq_number,acknowledgement_number,flags,window,data)
                clientSocket.sendto(packet,server_Address)

                #After sending packet, we update:
                # whats nest posision in the window
                # how many packets in the window and 
                # the seq_number of the next packet
                next_in_window+=1
                packets_in_window = first_in_window - next_in_window
                seq_number +=1
                
            while True: #Receiving ack from server

                #reveices packer from server
                syn_ack_from_server, serverAddr = clientSocket.recvfrom(2048)
                
                # since the SYN ACK packet from server contains no data, we can just extract the header right away
                seq, ack, flagg, win = parse_header(syn_ack_from_server)

                # Checks if the acknowledgement is for the right packet. 
                # The ack should be for the first packet in the window. 
                if  first_in_window == ack:
                    # parse flags
                    syn_flagg, ack_flagg, fin_flagg = parse_flags(flagg)

                    if ack_flagg == 4:
                        # sequence number oker for neste pakke
                        sequence_id += 1 #the next in sequence_id will be the next packet to be send
                        first_in_window+=1 # we move the window
                else:
                    break

        except TimeoutError:
            print("Error: Timeout")


        #Burde jeg heller kode med å kalle på metoder som sender pakker også ha en while som konstant lytter etter ack?
        # Og dersom acken aldri kommer blir det timeout? 
        
        





    


# ------------------------------------------------------------------------------#
#                                 Server side                                   #
# ------------------------------------------------------------------------------#

def connection_establishment_server(serverSocket):
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
            else:
                print("Error: ACK not received!")

        else:
            print("Error, Ack_number does not match")
    else:
        print("Error: SYN not received!")
    

    

def server_main(bind_IPadress, port):
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
    connection_establishment_server(serverSocket)
        

            

        



# ------------------------------------------------------------------------------#
#                               End of server side                              #
# ------------------------------------------------------------------------------#









# ------------------------------------------------------------------------------#
#                                  Client side                                  #
# ------------------------------------------------------------------------------#

def connection_establishment_client(clientSocket, server_IP_adress, server_port, modus):

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
                    print('Må kalle funksjon')
                else:
                    print('Må kalle funksjon')
               
                
        
            else:
                raise socket.timeout("Error: SYN-ACK not received.") # can delete this?
    except BaseException as e:
        print("Time out while waiting for SYN-ACK", e) 

def client_main(server_ip_adress, server_port, modus):
    serverName = server_ip_adress
    serverPort = server_port

    # establish a UDP socket
    clientSocket = socket(AF_INET, SOCK_DGRAM)

    # sending the arguements in this method to establish a connection with server
    connection_establishment_client(clientSocket, serverName, serverPort, modus)





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
        server_main(args.bind, args.port)
    else:
        client_main(args.serverip, args.port, args.modus)
