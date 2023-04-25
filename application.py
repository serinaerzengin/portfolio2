#important imports
import argparse
import sys
import ipaddress
from socket import*

##################################################################
##-------FUNCTIONS TO CHECK VALID DATA IN ARGUMENTS---------######
##################################################################

#Function to check if the address is a valid IPv4 address and in the correct format
#address holds the IP address of either the client or server
def check_ip(address):
    try:
        #we convert the address string to an IPv4 address object. if it was successful, we print that the address is valid
        val = ipaddress.ip_address(address)    
    #If the conversion failed, print that the address is not valid
    except ValueError:
        print(f"The IP adress is {address} not valid")
        sys.exit() #Exit the program if not valid
    return address #returns the address if it is in correct format

#Function to check if the port that the user has chosen is valid. 
#val holds the port number from either client or server
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
    return value #if the portnumer is valid we return it.


########################################################################
###########-----------ARGUMENTPARSER & ARGUMENTS-----------#############
########################################################################

#Create an ArgumentParser instance  
parser= argparse.ArgumentParser(description="A client/server transfer application")

#Create an argument group for server arguments
group1= parser.add_argument_group('Server argumentns')
# Creates an argument group for client arguments
group2 = parser.add_argument_group('Client arguments')

'''
The first argument is the short version of the argument, the second argument is the long version, the third argument 
tells argparse to set the value = true or to call a function to check for valid input. help gives the user a short 
explenation of what the argument does if the user runs the program  with -h or --help
'''

#-----------------------SERVER ARGUMENTS-----------------------#
group1.add_argument('-s', '--server', action='store_true', help='use this flag to run the program in server mode')
#bind argument with a check using the check_ip function implemented over
group1.add_argument('-b', '--bind', type=check_ip, default='127.0.0.1', help='IP-adress of the servers interface')

#-----------------------CLIENT ARGUMENTS-----------------------#
group2.add_argument('-c', '--client', action='store_true', help='use this flag to run the program in client mode')
#serverip argument with a check using the checkip function implemented over
group2.add_argument('-I', '--serverip', default='127.0.0.1',type=check_ip, help='allows the user to select the IP address of the server' )

#-----------ARGUMENTS THAT ARE ALLOWED TO USE ON BOTH SERVER AND CLIENT------------#
#port argument with a check using the check_port function implemented over
parser.add_argument('-p', '--port', default=8088, type=check_port)

#Parse the arguments
args = parser.parse_args()

"""
 further we check if the different arguments is true server/client, and have
 different code for client and server
"""

#Check if the user try to run as both server and client
if args.server and args.client:
    #prints error message if the application is invoked with both client and server
    print('Error: Cannot run as both client and server in the transfer application')

########################################################################
###########----------------SERVER CODE------------------################
########################################################################
elif args.server:
    
    #portnumber from the input argument
    serverport = args.port
    #ip argument
    serverip = args.bind

    #Create UDP socket
    #Standard function in python -AF_INET indicates that the underlying network is using IPv4. -SOCK_DGRAM indicates that it is a UDP socket
    serverSocket= socket(AF_INET, SOCK_DGRAM)

    #Tries to bind socket to port number
    try:
    #Python-code that binds a socket to a spesific IP-adress and port. Sets up the socket to listen to the IP-adress and ports set by the user
        serverSocket.bind((serverip, serverport)) 
    except:
        #if the bind failed we print error message
        print("Bind failed. Error : ")
        sys.exit() #exit the program

    #create message to tell that the server is ready to receive
    message='Server is ready to receive'
    top_bottom_line = "-" * len(message) #string multiplication is used to create a string with the same number of hyphens as the length of the message
    #Prints the message 
    print(f"{top_bottom_line}\n{message}\n{top_bottom_line}")

    #FLODHEST : MÅ VI HA WHILE? 
    #Read from UDP socket into message, getting client's address (client IP and port)
    message, clientAdress = serverSocket.recvfrom(2048)

    #FLODHEST : HER MÅ VI DECODE OG SJEKKE OM DET ER SYN MELDING BLA BLA BLA
    modifiedMessage = message.decode().upper()

    #FLODHEST : MÅ SENDE SYN:ACK TILBAKE BLA BLA BLA
    melding='blablabla'
    serverSocket.sendto(melding.encode(), clientAdress)

    #Server: receives a file from a sender over DRTP/UDP
   


########################################################################
###########----------------CLIENT CODE------------------################
########################################################################
elif args.client:
    
    #arguments we send when we run client
    clientport = args.port
    serverip = args.serverip

    #Create UDP socket
    #Standard function in python -AF_INET indicates that the underlying network is using IPv4. -SOCK_DGRAM indicates that it is a UDP socket
    clientSocket =  socket(AF_INET, SOCK_DGRAM)
    #FLODHEST : MÅ SENDE SYN
    message='SYN'

    #Attach server name, port to message; send into socket
    clientSocket.sendto(message.encode(), serverip, clientport)

    #read reply from socket
    #FLODHEST : MÅ SJEKKE OM VI FÅR ACK:SYN tilbake
    modifiedMessage, serverAddress = clientSocket.recvfrom(2048)

    clientSocket.close()

##Client: reliably sends a file over


#if no argument (nither -s or -c) where set
else:
    print('Error: you must run either in server or client mode')