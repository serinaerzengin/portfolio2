# portfolio2

If I want to skip an ack to trigger retransmission at the sender-side:

python3 application.py -s -i <ip_address> -p <port_number> -r <reliable method> -t <test_case>

e.g., test_case = skip_ack, reliable method=gbn

-----------> skip_ack on server