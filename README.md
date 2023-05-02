# Portfolio2
This application is a simple transport protocol that provides reliable data delivery on top of UDP.

## Instructions to run application - with default options
1. Run the `server` first with:

```
python3 application.py -s
```
2. Run the `client` with:

```
python3 application.py -c
```
<br />

## Instructions to run application - with available options
<br />

### Available options to invoke the server:

`-b` or `--bind` = Allows to select **ip address** of the server's interface. \
`-p` or `--port` = Allows to select **port number** (Range: [1024-65535]).\
`-r` or `--modus` =  Allows to choose the **reliable method** (SAW, GBN, SR).\
`-t` or `--test` =  Allows to choose the **test mode** (dropack).
<br />


### Available options to invoke the client:
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
python3 application.py -s -b 127.0.0.1 -p 8088 -r SAW -t dropack -f blabla.JPG
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
python3 application.py -s -b 127.0.0.1 -p 8088 -r GBN -t dropack -f blabla.JPG
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
python3 application.py -s -b 127.0.0.1 -p 8088 -r SR -t dropack -f blabla.JPG
```

2. `client`
```
python3 application.py -c -I 127.0.0.1 -p 8088 -r SR -w 10 -t loss -f hei.JPG
```
<br />

---


## Install

For å skrive ut bilde: python3 -m pip install Pillow  
python3 -m pip install ping3
import i toppen: from PIL import Image
tok et par sekunder fra det ble lasta ned til den import linja begynte å funke (ikke lyse rødt)
