# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from gaiatest import GaiaTestCase

from powertool.mozilla import MozillaAmmeter
from datetime import datetime

import time
import json
import sys
import os
import subprocess

STABILIZATION_TIME = 30 # seconds
SAMPLE_TIME = 30 # seconds
SAMPLE_ACTION_TIME = 5 # seconds between actions

class TestPower(GaiaTestCase):

    def setUp(self):
        print "setUp - start"
        GaiaTestCase.setUp(self)

        print "setUp - about to lock"
        # Make sure the lock screen is up
        self.device.lock()

        # Make sure the screen brightness is full on, with auto turned off
        # Volume level adjust to 9 and turn on airplane mode
        self.data_layer.set_setting("screen.automatic-brightness", False)
        self.data_layer.set_setting("screen.brightness", 1.0)
        self.data_layer.set_setting("audio.volume.content", 9)
        self.data_layer.set_setting("airplaneMode.enabled", True)

        # Make sure USB charging is turned off
        cmd = []
        cmd.append("adb")
        cmd.append("shell")
        cmd.append("echo 0 > /sys/class/power_supply/battery/charging_enabled")
        subprocess.Popen(cmd)
        
        # Set up the ammeter
        self.ammeterFields = ('current','voltage','time')
        serialPortName = None #we want powertool to figure out the port...
        self.ammeter = MozillaAmmeter(serialPortName, False)

        # Grab a sample, and calculate the timer offset from ammeter time to wall clock time
        sample = self.ammeter.getSample(self.ammeterFields)
        sampleTimeAfterEpochOffset = time.time()
        firstSampleMsCounter = sample['time'].value
        self.sampleTimeEpochOffset = int(sampleTimeAfterEpochOffset * 1000.0) - firstSampleMsCounter;

        print "setUp - done"


    def getSample(self, sampleLog, samples):
        sample = self.ammeter.getSample(self.ammeterFields)
        if sample is not None:
            sampleObj = {}
            sampleObj['current'] = sample['current'].value
            sampleObj['voltage'] = sample['voltage'].value
            sampleObj['time'] = sample['time'].value + self.sampleTimeEpochOffset
            sampleLog.append(sampleObj)
            samples.append(str(sample['current'].value))
            return sampleObj['current']
        else:
            return None


    def runPowerTestLoop(self, testName, appName, context, actionInterval, actionFunction):
        sampleLog = []
        samples = []
        totalCurrent = 0
        done = False
        stopTime = time.time() + SAMPLE_TIME
        nextActionTime = time.time() + actionInterval
        while not done:
            current = None
            current = self.getSample(sampleLog, samples)
            if current is not None:
                totalCurrent += current
            timeNow = time.time()
            if timeNow > nextActionTime:
                if actionFunction is not None:
                    actionFunction()
                nextActionTime = timeNow + actionInterval
            done = (timeNow > stopTime)

        if len(sampleLog) == 0:
            averageCurrent = 0.0
        else:
            averageCurrent = int(totalCurrent / len(sampleLog))
        return (sampleLog, samples, averageCurrent)


    def runPowerTest(self, testName, appName, context, actionInterval=SAMPLE_ACTION_TIME, actionFunction=None):
        # try using the extended ammeter's ability to cut off the USB
        print "Turning on debug mode"
        #self.ammeter.turnOnDebugMode()
        print "Turning off Aux USB on ammeter"
        self.ammeter.turnOffAuxUsb()
        print ""
        print "Waiting", STABILIZATION_TIME, "seconds to stabilize"
        time.sleep(STABILIZATION_TIME)

        print "Starting power test, gathering results for", SAMPLE_TIME, "seconds"
        (sampleLog, samples, averageCurrent) = self.runPowerTestLoop(testName, appName, context, actionInterval, actionFunction)
        powerProfile = {}
        powerProfile['testTime'] = datetime.now().strftime("%Y%m%d%H%M%S")
        powerProfile['epoch'] = int(time.time() * 1000)
        powerProfile['sampleLog'] = sampleLog
        powerProfile['samples'] = samples
        powerProfile['testName'] = testName
        powerProfile['average'] = averageCurrent
        powerProfile['app'] = appName
        powerProfile['context'] = context + ".gaiamobile.org"
        print "Sample count:", len(sampleLog)
        print "Average current:", averageCurrent, "mA"
        self.writeTestResults(powerProfile)
        print "Turning Aux USB back on"
        self.ammeter.turnOnAuxUsb()
        time.sleep(5)
        # Turn USB charging back on
        cmd = []
        cmd.append("adb")
        cmd.append("forward")
        cmd.append("tcp:2828")
        cmd.append("tcp:2828")
        print "Running adb forward tcp:2828 tcp:2828"
        subprocess.Popen(cmd)
        self.ammeter.softReset() # fix any USB issues that have crept in


    def writeTestResults(self, powerProfile):
        summaryName = '%s_%s_summary.log' % (powerProfile['testName'], powerProfile['testTime'])
        summaryFile = open(summaryName, 'w')
        summaryFile.write("name: power\n")
        summaryFile.write("test: %s\n" % powerProfile["testName"])
        summaryFile.write("time: %s\n" % powerProfile["epoch"])
        summaryFile.write("average: %s\n" % powerProfile["average"])
        summaryFile.write("context: %s\n" % powerProfile["context"])
        summaryFile.write("app_name: %s\n" % powerProfile["app"])
        summaryFile.write("\n")
        summaryFile.close()


    def tearDown(self):
        try:
            GaiaTestCase.tearDown(self)
        except IOError:
            print "Expected IOError in tearDown, supressing"

        # Disconnect from the ammeter
        self.ammeter.close()

        # Turn USB charging back on
        cmd = []
        cmd.append("adb")
        cmd.append("shell")
        cmd.append("echo 1 > /sys/class/power_supply/battery/charging_enabled")
        print "Turning charge flag back on"
        subprocess.Popen(cmd)

