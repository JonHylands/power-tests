# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from gaiatest import GaiaTestCase
from gaiatest.apps.lockscreen.app import LockScreen

from powertool.mozilla import MozillaAmmeter
import time
import json
import sys
import os
import subprocess

STABILIZATION_TIME = 10 # seconds
SAMPLE_TIME = 10 # seconds

class TestLockScreen(GaiaTestCase):

    def setUp(self):
        print "setUp - start"
        GaiaTestCase.setUp(self)

        print "setUp - about to lock"
        # Make sure the lock screen is up
        self.device.lock()

        # Make sure USB charging is turned off
        cmd = []
        cmd.append("adb")
        cmd.append("shell")
        cmd.append("echo 0 > /sys/class/power_supply/battery/charging_enabled")
        subprocess.Popen(cmd)

        # Set up the ammeter
        self.ammeterFields = ('current','voltage','time')
        serialPortName = "/dev/ttyACM0"
        self.ammeter = MozillaAmmeter(serialPortName, False)

        # Grab a sample, and calculate the timer offset from ammeter time to wall clock time
        sample = self.ammeter.getSample(self.ammeterFields)
        sampleTimeAfterEpochOffset = time.time()
        firstSampleMsCounter = sample['time'].value
        self.sampleTimeEpochOffset = int(sampleTimeAfterEpochOffset * 1000.0) - firstSampleMsCounter;
        print "setUp - done"


    def runPowerTest(self):
        print ""
        print "Waiting", STABILIZATION_TIME, "seconds to stabilize"
        time.sleep(STABILIZATION_TIME)

        sampleLog = []
        totalCurrent = 0
        done = False
        print "Starting power test, gathering results for", SAMPLE_TIME, "seconds"
        stopTime = time.time() + SAMPLE_TIME
        while not done:
            sample = self.ammeter.getSample(self.ammeterFields)
            if sample is not None:
                sampleObj = {}
                sampleObj['current'] = sample['current'].value
                sampleObj['voltage'] = sample['voltage'].value
                sampleObj['time'] = sample['time'].value + self.sampleTimeEpochOffset
                sampleLog.append(sampleObj)
                totalCurrent += sampleObj['current']
            done = (time.time() > stopTime)

        averageCurrent = totalCurrent / len(sampleLog)
        powerProfile = {}
        powerProfile['sampleTimeEpochOffset'] = self.sampleTimeEpochOffset
        powerProfile['samples'] = sampleLog
        print "Sample count:", len(sampleLog)
        print "Average current:", averageCurrent, "mA"


    def test_unlock_to_homescreen_off(self):
        """https://moztrap.mozilla.org/manage/case/1296/"""

        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()

        self.wait_for_condition(lambda m: self.apps.displayed_app.name == homescreen.name)
        self.device.turn_screen_off()
        print ""
        print "Running Idle Test (screen off)"
        self.runPowerTest()


    def test_unlock_to_homescreen_on(self):
        """https://moztrap.mozilla.org/manage/case/1296/"""

        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()

        self.wait_for_condition(lambda m: self.apps.displayed_app.name == homescreen.name)
        print ""
        print "Running Idle Test (screen on)"
        self.runPowerTest()


    def tearDown(self):
        GaiaTestCase.tearDown(self)

        # Disconnect from the ammeter
        self.ammeter.close()

        # Turn USB charging back on
        cmd = []
        cmd.append("adb")
        cmd.append("shell")
        cmd.append("echo 1 > /sys/class/power_supply/battery/charging_enabled")
        subprocess.Popen(cmd)
