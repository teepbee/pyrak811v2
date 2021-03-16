# pyrak811v2
RAK811v2 Python 3 library for use with the Raspberry Pi LoRa pHAT.

The library exposes the AT commands as described in the RAK811 Lora AT Command User Guide V1.0 found in the DOCS folder of this repository. This applies to LoRa modules with firmware version V3.0.0.13.T3 or later.

The AT command structure is signifficantly different from that in previous versions of the firmware.

This library is based heavily on pyrak811 https://github.com/AmedeeBulle/pyrak811 but doesn't include the command line interface (CLI) functionality. 


Peripheral Requirements
A Raspberry Pi!
A RAK811 LoRa module (PiSupply IoT LoRa Node pHAT for Raspberry Pi )
On the Raspberry Pi the hardware serial port must be enabled and the serial console disabled (use raspi-config)
The user running the application must be in the dialout and gpio groups (this is the default for the pi user)

The Python script loraTest.py is an eaxmple of a script that when configured with appropriate identifiers will execute a number of AT commands including joining to the network (OTA or ABP) and sending some data and waiting for confirmaton.

You may use the Python logging module to control logging by the library. 
Currently setting the log level to DEBUG will display the AT commands sent to the module and the raw respnse received from the module. See loraTest.py for an example of enabling logging DEBUG level output to the console. For further information regards configuring Python logging see the online documentation for the logging library.

This represents my first foray into both git and Python so appologies in advance for anything missing etc that is normally provided. 


