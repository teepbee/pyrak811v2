"""RAK811 serial communication layer.

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
from re import match
from threading import Condition, Event, Thread
from time import sleep
from queue import SimpleQueue
from _queue import Empty
import logging

import ctypes

from rak811v2.exception import Rak811v2Error
from serial import Serial

# Default instance parameters. Can be overridden  at creation
# Serial port configuration
PORT = '/dev/serial0'
BAUDRATE = 115200
# Timeout for the reader thread. Any value will do, the only impact is the time
# needed to stop the thread when the instance is destroyed...
TIMEOUT = 2
# Timeout for response and events
# The RAK811 typically respond in less than 1.5 seconds
RESPONSE_TIMEOUT = 5
# Event wait time strongly depends on duty cycle, when sending often at high SF
# the module will wait to respect the duty cycle.
# In normal operation, 5 minutes should be more than enough.
EVENT_TIMEOUT = 5 * 60

# Constants
EOL = '\r\n'

RESPONSE_OK = 'OK'
RESPONSE_OK_INIT ='Initialization OK'
RESPONSE_ERROR = 'ERROR'
RESPONSE_EVENT = 'at+recv='



class Rak811v2TimeoutError(Rak811v2Error):
    """Read timeout exception."""

    pass


class Rak811v2Serial(object):
    """Handles serial communication between the RPi and the RAK811 module."""

    def __init__(self,
                 port=PORT,
                 baudrate=BAUDRATE,
                 timeout=TIMEOUT,
                 response_timeout=RESPONSE_TIMEOUT,
                 event_timeout=EVENT_TIMEOUT,
                 **kwargs):
        """Initialise class.

        The serial port is immediately opened and flushed.
        All parameters are optional and passed to Serial.
        """
        self._logger = logging.getLogger(__name__)
        self._read_buffer_timeout = response_timeout
#        self._event_timeout = event_timeout
        self._serial = Serial(port=port,
                              baudrate=baudrate,
                              timeout=timeout,
                              **kwargs)
        self._serial.reset_input_buffer()

        self._response_timeout = response_timeout
        self._event_timeout = event_timeout

        ##Create Q to hold data read
        self.Info_q = SimpleQueue()
        self.RecvEvents_q = SimpleQueue()
        self.Resp_q = SimpleQueue()
        # Read thread
        self._read_done = Event()
        ##self._resp_ready = Event()

        self._read_thread = Thread(target=self._read_loop, daemon=True)
        self._read_thread.start()

    def close(self):
        """Release resources."""
        self._read_done.set()
        self._read_thread.join()
        self._serial.close()

    def _clear_q(self, q):
        while not q.empty():
            try:
                q.get(False)
            except Empty:
                continue

    def _clear_all_qs(self):
        self._clear_q(self.Info_q)
        self._clear_q(self.RecvEvents_q)
        self._clear_q(self.Resp_q)

    def _read_loop(self):
        """Read thread.

        Continuously read serial. When data is available we want to read all of
        it and notify once:
            - We need to drain the input after a response. If we notify()
            too early the module will miss next command
            - We want to catch all events at the same time

        Modified from the original to use 3 queues.
        Resp_q - response q will be used for OK and Error responses 
        RecvEvents_q - Events q will be used for all 'at+recv' event responses
        Info_q - Informatioin q will be used for all other responses.
        """
        while not self._read_done.is_set():
            line = self._serial.readline()
            if line == b'':
                continue
            self._logger.debug('Recvd: %s', line)
            line = line.decode('ascii').rstrip(EOL)
            if line.startswith(RESPONSE_OK):
                self.Resp_q.put(line)
                self.Info_q.put(line)
            elif line.startswith(RESPONSE_ERROR):
                self.Resp_q.put(line)
            elif line.startswith(RESPONSE_EVENT):
                self.RecvEvents_q.put(line)
            elif line.startswith(RESPONSE_OK_INIT):
                self.Resp_q.put(line)
                self.Info_q.put(line)
            else:
                self.Info_q.put(line)
            continue


    def get_response(self, timeout=None):
        """Get response from module.

        This is a blocking call: it will return a response line or raise
        # Rak811v2TimeoutError if a response line is not received in time.
        # """
        if timeout is None:
            timeout = self._response_timeout

        try:
            response = self.Resp_q.get(True, timeout)
        except Empty:
                     raise Rak811v2TimeoutError(
                         'Timeout while waiting for response'
                     )
        
        return response

    def get_info(self, timeout=None):
        """Get response from module.

        This is a blocking call: it will return an information line or raise
        # Rak811v2TimeoutError if a response line is not received in time.
        # """
        if timeout is None:
            timeout = self._response_timeout

        try:
            info = self.Info_q.get(True, timeout)
        except Empty:
                     raise Rak811v2TimeoutError(
                         'Timeout while waiting for response'
                     )
        
        return info

    def get_event(self, timeout=None):
        """Get events from module.

        This is a blocking call: it will return a list of events or raise
        Rak811v2TimeoutError if no event line is received in time.
        """
        if timeout is None:
            timeout = self._event_timeout

        try:
            event = self.RecvEvents_q.get(True, timeout)
        except Empty:
            raise Rak811v2TimeoutError(
                'Timeout while waiting for events'
                )

        return event

    def send_string(self, string):
        """Send string to the module."""
        self._logger.debug("Send: %s", string)
        self._serial.write((bytes)(string, 'utf-8'))

    def send_command(self, command, clearq=True):
        """Send AT command to the module."""
        if clearq:
            self._clear_all_qs()
        self.send_string('at+{0}\r\n'.format(command))
