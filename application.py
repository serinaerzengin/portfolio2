from socket import *
from struct import *
import argparse
import ipaddress
import sys
# ------------------------------------------------------------------------------#
#                                   Header handling                             #
# ------------------------------------------------------------------------------#

header_format = '!IIHH' # header size is always 12 bytes
print (f'size of the header = {calcsize(header_format)}') # check header size

def create_packet(seq, ack, flags, win, data): # parameters are sequence number, acknowledgment number, flags (4 bits), receiver window and application data
    header = pack(header_format, seq, ack, flags, win) # Create a header of 12

    packet = header + data # header is 12, and data is 1460. This packet should be 1472 bytes
    print (f'packet containing header + data of size {len(packet)}') # show the length of the packet

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
#                                 Server side                                   #
# ------------------------------------------------------------------------------#

def connection_establishment_server(serverSocket):
    SYN_from_client, client_Addr = serverSocket.recvfrom(2048) # check SYN packet from client
    SYN_seq, SYN_ack, SYN_flagg, SYN_win = parse_header(SYN_from_client.decode())

    # check flags
    syn_flagg, ack_flagg, fin_flagg = parse_flags(SYN_flagg)
    if syn_flagg == 8: # if this is a SYN packet
        # create SYN ACK message
        data = b''
        sequence_number = 0
        acknowledgment_number = 0
        window = 0
        flags = 12 # SYN and ACK flags set here, and the decimal is 12
        # and send SYN-ACK back to client for confirmation
        SYN_ACK_packet = create_packet(sequence_number, acknowledgment_number, flags, window, data)
        serverSocket.sendto(SYN_ACK_packet.encode(), client_Addr) # send SYN ACK to client
        # receive that last ACK from client to establish a connection
        ACK_from_client, client_Addr = serverSocket.recvfrom(2048)
        ACK_flagg = parse_header(ACK_from_client.decode())[2] # only checking flagg
        ACK_syn_flagg, ACK_ack_flagg, ACK_fin_flagg = parse_flags(ACK_flagg)
        # check if this is a ACK message
        if ACK_ack_flagg == 4:
            print("Connection established with ", client_Addr)
        else:
            print("Error: ACK not received!")
    else:
        print("Error: SYN not received!")
    return client_Addr

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
    print("server is ready to receive!!!")
    
    while True:
        client_addr = connection_establishment_server(serverSocket)

            

        



# ------------------------------------------------------------------------------#
#                               End of server side                              #
# ------------------------------------------------------------------------------#









# ------------------------------------------------------------------------------#
#                                  Client side                                  #
# ------------------------------------------------------------------------------#

def connection_establishment_client(server_ip_adress, server_port):
    serverName = server_ip_adress
    serverPort = server_port
    clientSocket = socket(AF_INET, SOCK_DGRAM)

    # Create a empty packet with SYN flag
    data = b''
    sequence_number = 0
    acknowledgment_number = 0
    window = 0
    flags = 8 # SYN flag set here, and the decimal is 8
    say_hi_to_server = create_packet(sequence_number, acknowledgment_number, flags, window, data)
    # done creating packet here

    """ send a SYN packet to the server
    s.sendto(b'SYN', (serverName, serverPort))"""

    clientSocket.sendto(say_hi_to_server.encode(), (serverName, serverPort))
    
    # set timeout
    clientSocket.settimeout(0.5)

    # wait for a response from the server
    try:
        syn_ack_from_server, serverAddr = clientSocket.recvfrom(2048)
        
        # since the SYN ACK packet from server contains no data, we can just extract the header right away
        seq, ack, flagg, win = parse_header(syn_ack_from_server.decode())
        print(f'seq={seq}, ack={ack}, flags={flagg}, receiver-window={win}')

        # parse flagg part
        syn_flagg, ack_flagg, fin_flagg = parse_flags(flagg)
        
        # check if SYN ACK packet from server has come. If yes, send ACK packet and confirm connection establishment
        if syn_flagg == 8 and ack_flagg == 4:
            print("got SYN ACK from server")
            flags = 4

            # Send ACK packet to server
            ack_packet = create_packet(sequence_number, acknowledgment_number, flags, window, data)
            clientSocket.sendto(ack_packet.encode(), (serverName, serverPort))
            print("Connection establish!")
        else:
            print("Error: SYN-ACK not received.")
    except socket.timeout:
        print("Time out while waiting for SYN-ACK") 


    #clientSocket.connect((serverName, serverPort))



# ------------------------------------------------------------------------------#
#                               Done client side                                #
# ------------------------------------------------------------------------------#


