# Portfolio2
This application is a simple transport protocol that provides reliable data delivery on top of UDP.

<br />

## Instructions to run application -  available options
<br />

### Available options to invoke the server:
`-s` or `--server` = enable the **server mode**. \
`-b` or `--bind` = Allows to select **ip address** of the server's interface. \
`-p` or `--port` = Allows to select **port number** (Range: [1024-65535]).\
`-r` or `--modus` =  Allows to choose the **reliable method** (SAW, GBN, SR).\
`-t` or `--test` =  Allows to choose the **test mode** (skipack).

<br />


### Available options to invoke the client:
`-c` or `--client` = enable the **client mode**. \
`-I` or `--serverip` = Selects the **ip address** of the server. \
`-p` or `--port` = Allows to select the server's **port number** (Range: [1024-65535]).\
`-r` or `--modus` =  Allows to choose the **reliable method** (SAW, GBN, SR).\
`-t` or `--test` =  Allows to choose the **test mode** (loss).\
`-w` or `--window` =  Allows to choose the **window size** .
<br />



<br />

###  Example to run with flag/options SAW
**NOTE: The arguments do not need to be in a spesific order.**

1. `server`
```
python3 application.py -s -b 127.0.0.1 -p 8088 -r SAW -t skipack -f blabla.JPG
```

2. `client`
```
python3 application.py -c -I 127.0.0.1 -p 8088 -r SAW -t loss -f hei.JPG
```
<br />

###  Example to run with flag/options GBN
**NOTE: The arguments do not need to be in a spesific order.**

1. `server`
```
python3 application.py -s -b 127.0.0.1 -p 8088 -r GBN -t skipack -f blabla.JPG
```

2. `client`
```
python3 application.py -c -I 127.0.0.1 -p 8088 -r GBN -w 10 -t loss -f hei.JPG
```
<br />

###  Example to run with flag/options SR
**NOTE: The arguments do not need to be in a spesific order.**

1. `server`
```
python3 application.py -s -b 127.0.0.1 -p 8088 -r SR -t skipack -f blabla.JPG
```

2. `client`
```
python3 application.py -c -I 127.0.0.1 -p 8088 -r SR -w 10 -t loss -f hei.JPG
```
<br />

---

## BONUS


## Install
To be able to run out application.py you need to have the following installed:
- Pillow
- ping3

# Install Pillow
Pillow is installed to be able to open a image. \
After installing Pillow, we imort Image from PIL, wich makes it possible to open a Image file
`python3 -m pip install Pillow`


# Install ping3
Ping3 is Imported into the project so that the roundtrip time can be calculated.\
If you run the client side and add the flag -B, then the application will use the ping command from ping 3 to calucate the roundtrip time, and use rtt*4 as the socket timeout. If you dont use -B the timeout will be set to default 0.5ms.
`sudo python3 -m pip install ping3`


For å skrive ut bilde: python3 -m pip install Pillow  
sudo python3 -m pip install ping3
import i toppen: from PIL import Image
tok et par sekunder fra det ble lasta ned til den import linja begynte å funke (ikke lyse rødt)
