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

########################################################################
###########----------------SERVER CODE------------------################
########################################################################

#Server: receives a file from a sender over DRTP/UDP


########################################################################
###########----------------CLIENT CODE------------------################
########################################################################



#Client: reliably sends a file over
