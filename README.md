# ORCON RF15 Protocol Decoder #
This repository provides an ORCON RF15 mechanical ventilation message decoder class. It can also use a Raspberry Pi + 
CC1101 transceiver to listen to traffic and decode it in real time. 

The protocol is based on the [Honeywell Evohome protocol](https://www.domoticaforum.eu/viewtopic.php?f=7&t=5806&sid=359183586915e40aa9497935a54331c0)

### Installation ###

1. Clone this repository
2. virtualenv env
3. Activate the virtualenv
4. pip install spidev RPi.GPIO numpy bitstring
5. python rx.py

### Network Settings
The CC1101 in the ORCON network is configured with the following settings
1. 868.299866 MHz carrier frequency 2-FSK
2. 38.385 kbaud bit rate
3. 50.781250 FSK frequency deviation
4. 325 kHz RX filter BW

### Command types
So far the following command types have been observed, further analysis is required.

| Command       | Purpose?      |
| ------------- |:-------------:|
| 0x0404        | Boot          |
| 0x1212        | CO2 PPM       |
| 0x2222        | Set Speed     |
| 0x3131        | Current Speed |

## Contributing
If you want to contribute, shoot me a message or create a pull-request.