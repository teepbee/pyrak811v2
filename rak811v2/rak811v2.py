"""Interface with the RAK811 module.

Copyright 2021 Tim Brennan

Based on the work of Philippe Vanhaesendonck

See https://github.com/AmedeeBulle/pyrak811/tree/master/rak811



Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

SPDX-License-Identifier: Apache-2.0
"""
from binascii import hexlify
from enum import IntEnum
from time import sleep

from RPi import GPIO

from .exception import Rak811v2Error
from .serial import Rak811v2Serial, Rak811v2TimeoutError

RESET_BCM_PORT = 17
RESET_DELAY = 0.01
RESET_POST = 2
RESPONSE_OK = 'OK'
RESPONSE_ERROR = 'ERROR:'
RESPONSE_EVENT = 'at+recv='
RESPONSE_OK_INIT = 'Initialization OK'


# RAK811 error codes and associated messages

class ResponseCode(IntEnum):
    """AT commands event codes."""
    Unknown = -1 ##catch all
    BadATCmd = 1
    InvCmdParam = 2
    ErrRdWrFlash = 3
    ErrRdWrIIC = 4
    ErrSndUart = 5
    ErrBleInvState = 41
    LoRaBusy = 80
    LoRaSvcUnk = 81
    LoRaParamInv = 82
    LoRaFreqInv = 83
    LoRaDRInv = 84
    LoRaFreqDRInv = 85
    DevNotJoined = 86
    PktToLong = 87
    SvcClosed = 88
    UnsuppRegion = 89
    DutyCycleResticted = 90
    NoValidChanFnd = 91
    NoFreeChanFnd = 92
    StatusError = 93
    LoRaTxTimeOut = 94
    LoRaRx1TimeOut = 95
    LoRaRx2TimeOut = 96
    ErrRecvRx1 = 97
    ErrRecvRx2 = 98
    ErrLoRaJoinFailed = 99
    DwnLnkRepeated = 100
    ErrPayLoadSz = 101
    ErrMnyDwnLinkFrameLost = 102
    ErrAddrFail = 103
    ErrVerifyMIC = 104

RESPONSE_MESSAGE = {
    ResponseCode.Unknown: 'Unknown',
    ResponseCode.BadATCmd: 'BAD AT Command',
    ResponseCode.InvCmdParam: 'Invalid parameter in AT command',
    ResponseCode.ErrRdWrFlash: 'Error reading or writing flash',
    ResponseCode.ErrRdWrIIC: 'Error reading or wrting through IIC',
    ResponseCode.ErrSndUart: 'Error sending through UART',
    ResponseCode.ErrBleInvState: 'BLE in invalid state',
    ResponseCode.LoRaBusy: 'LoRa busy',
    ResponseCode.LoRaSvcUnk: 'LoRa service unknown',
    ResponseCode.LoRaParamInv: 'LoRa parameters invalid',
    ResponseCode.LoRaFreqInv: 'LoRa frequency invalid',
    ResponseCode.LoRaDRInv: 'LoRa datarate invalid',
    ResponseCode.LoRaFreqDRInv: 'LoRa frequency and datarate are invalid',
    ResponseCode.DevNotJoined: 'Device has not joined a LoRa network',
    ResponseCode.PktToLong: 'Packet too long to be sent',
    ResponseCode.SvcClosed: 'Service closed by server',
    ResponseCode.UnsuppRegion: 'Unsupported region',
    ResponseCode.DutyCycleResticted: 'Duty cycle restricted',
    ResponseCode.NoValidChanFnd: 'No valid channel can be found',
    ResponseCode.NoFreeChanFnd: 'No free channel found',
    ResponseCode.StatusError: 'Status is error',
    ResponseCode.LoRaTxTimeOut: 'LoRa transmit tiemout',
    ResponseCode.LoRaRx1TimeOut: 'LoRa RX1 timeout',
    ResponseCode.LoRaRx2TimeOut: 'LoRa RX2 timeout',
    ResponseCode.ErrRecvRx1: 'Error receving in RX1',
    ResponseCode.ErrRecvRx2: 'Error receiving in RX2',
    ResponseCode.ErrLoRaJoinFailed: ' LoRa join failed',
    ResponseCode.DwnLnkRepeated: 'Downlink repeated',
    ResponseCode.ErrPayLoadSz: 'Payload size error with transmit DR',
    ResponseCode.ErrMnyDwnLinkFrameLost: 'Too many downlink frames lost',
    ResponseCode.ErrAddrFail: 'Address fail',
    ResponseCode.ErrVerifyMIC: 'Error verifying MIC',
}   


class Rak811v2ResponseError(Rak811v2Error):
    """Exception raised by response from the module.

    Attributes:
        errno -- as returned by the module
        strerror -- textual representation

    """

    def __init__(self, code):
        """Just assign return codes."""
        try:
            self.errno = int(code)
        except ValueError:
            self.errno = code

        if self.errno in RESPONSE_MESSAGE:
            self.strerror = RESPONSE_MESSAGE[self.errno]
        else:
            self.strerror = RESPONSE_MESSAGE[ResponseCode.Unknown]
        super().__init__(('[Errno {}] {}').format(self.errno, self.strerror))


class Rak811v2EventError(Rak811v2Error):
    """Exception raised by module events.

    Attributes:
        errno  -- as returned by the module
        strerror -- textual representation

    """

    def __init__(self, status):
        """Just assign return status."""
        try:
            self.errno = int(status)
        except ValueError:
            self.errno = status

        if self.errno in EVENT_MESSAGE:
            self.strerror = EVENT_MESSAGE[self.errno]
        else:
            self.strerror = EVENT_MESSAGE[EventCode.UNKNOWN]
        super().__init__(('[Errno {}] {}').format(self.errno, self.strerror))


class Rak811v2(object):
    """Main class."""

    def __init__(self, **kwargs):
        """Initialise class.

        The serial port is immediately opened and flushed.
        All parameters are optional and passed to RackSerial.
        """
        self._serial = Rak811v2Serial(**kwargs)


    def close(self):
        """Terminates session.

        Terminates read thread and close serial port.
        """
        self._serial.close()

    def hard_reset(self):
        """Hard reset of the RAK811 module.

        Hard reset should not be required in normal operation. It needs to be
        issued once after host boot, or module restart.
        Note that we do not cleanup() as the reset port should stay high (it is
        configured that way at boot time).
        """
        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(RESET_BCM_PORT, GPIO.OUT)
        GPIO.output(RESET_BCM_PORT, GPIO.LOW)
        sleep(RESET_DELAY)
        GPIO.output(RESET_BCM_PORT, GPIO.HIGH)
        sleep(RESET_POST)

    def _int(self, i):
        """Attempt int conversion."""
        try:
            i = int(i)
        except ValueError:
            pass
        return i

    def _send_string(self, string):
        """Send string to the RAK811 module."""
        self._serial.send_string(string)

    def _send_command(self, command, timeout=None):
        """Send AT command to the RAK811 module and return the response.

        Rak811ResponseError exception is raised if the command returns an
        error.
        This is a "blocking" call: if the module does not respond
        Rack811TimeoutError will be raised.
        """
        self._serial.send_command(command)
        #response = self._serial.get_response()
        response =""
        try:
            response = self._serial.get_response(timeout)

        except Rak811v2TimeoutError:
            if len(response) == 0:
                raise
        
                # Ignore events received while waiting on command feedback
        # while response.startswith(RESPONSE_EVENT):
        #     response = self._serial.get_response()

        if response.startswith(RESPONSE_OK):
            pass
#            response = response[len(RESPONSE_OK):]
        elif response.startswith(RESPONSE_OK_INIT):
            pass
#            response = response[len(RESPONSE_OK_INIT):]
        elif response.startswith(RESPONSE_ERROR):
            raise Rak811v2ResponseError(response[len(RESPONSE_ERROR):])
        else:
            raise Rak811v2ResponseError(response)

        return response

    def get_info(self, timeout=None):
        """Get info messages from the RAK811 module.

        This is a "blocking" call: it will either return a list of informational message or
        raise a Rack811TimeoutError.
        """
        self.x = []
        while True:
            try:
                self.x.append(self._serial.get_info(timeout))
            except Rak811v2TimeoutError:
                if len(self.x) != 0:
                    break
                raise

        return self.x

    def get_events(self, timeout=10):
        """Get events from the RAK811 module.

        This is a "blocking" call: it will either return a list of events or
        raise a Rack811TimeoutError.
        """

        self.events = []
        while True:
            try:
                self.events.append(self._serial.get_event(timeout))
            except Rak811v2TimeoutError:
                if len(self.events) != 0:
                    break
                raise

        return self.events
    
        # return [i[len(RESPONSE_EVENT):] for i in
        #         self._serial.get_events(timeout)]

    """System commands."""

    @property
    def version(self):
        """Get module version."""
        return(self._send_command('version'), self.get_info())
        #return(self._send_command('version'))

    def run(self):
        """Issue Run command"""
        return(self._send_command('run'))

    def join(self):
        """Issue Join command"""
        return(self._send_command('join', timeout=30))

    def help(self):
        """Issue Help command"""
        return(self._send_command('help'))
    
    def set_config(self, parameter):
        """Set configuration parameters by sending the AT command
                at+set_config 
            to the module.

        The following parameters are accepted by the module:
            device:boot                 
                    Force the device to enter BOOT mode.
            device:gpio:<pin_num>:<status>
                    Set level state of pin on device.
                    <pin_num>: pin index
                    <status>: 0 low or 1 high.
            device:restart
                    Used to restart the device
            device:sleep:<status>
                    Set current sleep status.
                    <status>: 0 wake up or 1 sleep
            device:uart:<index>:<baudrate>
                    Set baud rate for UART.
                    <index>: UART index.
                    <baudrate>: baud rate
            device:uart_mode:<index>:<mode>
                    Set UART operation mode.
                    <index>: UART index.
                    <mode>: 1 to set to data transmission mode
            lora:adr:<status>
                    Turn on or off the ADR of LoRa
                    <status>: 0: Turn off or 1: Turn On
            lora:app_eui:<app_eui>
                    Used to set the Application EUI parameter for LoRaWAN OTAA mode
            lora:app_key:<app_key>
                    Used to set the Application Key parameter for LoRaWAN OTAA mode
            lora:apps_key:<apps_key>
                    Used to set the Application Session Key parameter for LoRaWAN ABP mode.
            lora:ch_mask:<chan_num>:status>
                    Used to switch a channel on or off in the current region.
                    <chan_num>: channel number.
                    <status>: 0: off or 1: on
            lora:class:<class>
                    Used to set LoRaWan's Class to Class A, Class B, or Class C
                    <class>: 0: Class A, 1: Class B (not supported by module) or 2: Class C
            lora:confirm:<type>
                    Used to set the type of sending data to Confirm/Unconfirm
                    <type>: 0: Unconfimed, 1: Confirmed, 2: Multicast or 3: Proprietary
            lora:dev_addr:<dev_addr>
                    Used to set the Device Address parameter for LoRaWAN ABP mode
            lora:dev_eui:<dev_eui>
                    Used to set the Device EUI parameter for LoRaWAN OTAA mode
            lora:dr:<dr>
                    Used to set the data rate (DR) of LoRa
                    <dr>: Usually 0 to 5.
            lora:join_mode:<mode>
                    Used to switch the LoRaWAN's access mode to OTAA or ABP
                    <mode>: 0: OTAA or 1: ABP
            lora:nwks_key:<nwks_key>
                    Used to set the Network Session Key parameter for LoRaWAN ABP mode.
            lora:region:<region>
                    Set appropriate working frequency band. 
                    <region> is one of EU433, CN470, IN865, EU868, US915, AU915, KR920, AS923
            lora:send_interval:X:Y
            lora:tx_power:<tx_power>
                    Set the level of transmit power level of LoRa
                    <tx_power> Value dependent on frequency band and data rate.
            lora:work_mode:<mode>
                    Used to switch the LoRa's working mode to LoRaWan or LoRAP2p
                    <mode>: 0: LoRaWAN or 1: LoRaP2P
            lorap2p:transfer_mode:<mode>
                    Set the LoRaP2P mode to sender or receiver
                    <mode>: 1: Receiver or 2: Sender
            lorap2p:<frequency>:<spreadfact>:<bandwidth>:<codingrate>:<preamlen>:<power>
                    Set the relevant parameters of LoRAP2p
                    <frequency> Frequency Hz
                    <spreadfact>: spreading factor
                    <bandwidth>: 0: 125KHz, 1: 250KHz or 2: 500KHz
                    <codingrate>: 1: 4/5, 2: 4/6, 3 4/7 or 4: 4/8
                    <preamlen>: Preamble length: 5-65535
                    <power>: TX power 5-20 dbm

        """

        cmd = 'set_config={0}'.format(parameter)
        return (self._send_command(cmd))

    def get_config(self, parameter):
        """Get configuration information by sending the AT command
                at+get_config
            to the module.

            The parameter must be one of
                device:adc:<pin_num>
                        <pin_num>: pin number being queried
                device:gpio:<pin_num>
                        <pin_num>: pin number being queried
                device:status
                lora:channel
                lora:status

        Note: get_config returns always strings, no integer do avoid unwanted
        conversion for keys.
        """
        cmd = 'get_config={0}'.format(parameter)
        return (self._send_command(cmd))


    
    def _process_events(self, timeout=None):
        """Process module event queue.

        Process event queue looking for incoming (downlink) messages. Raise
        errors when unexpected events are encountered.

        Parameter:
            timeout: maximum time to wait for event

        """
        events = self.get_events(timeout)
        # Check for downlink
        for event in events:
            # Format: <status >,<port>[,<rssi>][,<snr>],<len>[,<data>]
            event_items = event.split(',')
            status = event_items.pop(0)
            status = self._int(status)
            if status == EventCode.RECV_DATA:
                self._add_downlink(event_items)
        # Check for errors
        for event in events:
            status = event.split(',')[0]
            status = self._int(status)
            if status not in (EventCode.RECV_DATA,
                              EventCode.TX_COMFIRMED,
                              EventCode.TX_UNCOMFIRMED):
                raise Rak811v2EventError(status)


    def send_lora(self, data, port=1):
        """This Command is used to send data through LoRa using
            at+send=lora:<port>:<data>

        Parameters:
            <data>: data to be sent. 
            If the datatype is bytes it will be sent as such. Strings will be converted to bytes.
            <port>: port number to use (1-223). If omitted default is 1

        """

        if type(data) is not bytes:
            data = (bytes)(data, 'utf-8')
        data = hexlify(data).decode('ascii')

        resp = self._send_command('send=lora:' + ':'.join((
            str(port),
            data
        )))

        return resp

    def send_uart(self, data, index=1):
        """This Command is used to send data through a UART using
            at+send=uart:<index>:<data>

        Parameters:
            <data>: data to be sent. 
            If the datatype is bytes it will be sent as such. Strings will be converted to bytes.
            <index>: UART index to use (1 or 3). If omitted default is 1

        """

        if type(data) is not bytes:
            data = (bytes)(data, 'utf-8')
        data = hexlify(data).decode('ascii')

        resp = self._send_command('send=uart:' + ':'.join((
            str(index),
            data
        )))

        return resp

    def send_lorap2p(self, data):
        """This Command is used to send data through LoRaP2P using
            at+send=lorap2p:<data>

        Parameters:
            <data>: data to be sent.
            If the datatype is bytes it will be sent as such. Strings will be converted to bytes.
        """

        if type(data) is not bytes:
            data = (bytes)(data, 'utf-8')
        data = hexlify(data).decode('ascii')

        resp = self._send_command('send=lorap2p:' + data)

        return resp
