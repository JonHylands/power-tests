#!/usr/bin/python
# -*- coding: utf-8 -*-

#
#  Get Temperature
#
#  used with extended ammeter, returns probe temperature in degrees C
#

import serial

serialPort = serial.Serial(port='/dev/ttyACM0', baudrate=1000000, timeout=1)

commandBytes = bytearray.fromhex("ff ff 01 02 1E DE") #SOFT_RESET
serialPort.write(commandBytes)
serialPort.flush()

serialPort.close()
