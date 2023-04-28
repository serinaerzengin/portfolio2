# portfolio2

Endret file_split til å ikke ta inn en liste, men lage den selv fordi den er jo tom.
Også at den returnerer lista tilbake. Hvis ikke hvordan får man tak i dem da? Den er jo ikke en global variabel?

Må pakken være decoded når vi tar den i join? eller kan den være encoded også decoder man den etter man har satt sammen hele filen.

For å skrive ut bilde: python3 -m pip install Pillow  
import i toppen: from PIL import Image
tok et par sekunder fra det ble lasta ned til den import linja begynte å funke (ikke lyse rødt)

For å kjøre koden:
serverside: python3 application.py -s -r GBN -f hei.jpg  
clientside: python3 application.py -c -r GBN -f serina.jpg