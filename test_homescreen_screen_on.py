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

class TestLockScreen(GaiaTestCase):

    def setUp(self):
        GaiaTestCase.setUp(self)

        # this time we need it locked!
        self.device.lock()

	# Make sure USB charging is turned off
	cmd = []
	cmd.append("adb")
	cmd.append("shell")
	cmd.append("echo 0 > /sys/class/power_supply/battery/charging_enabled")
	subprocess.Popen(cmd)

        self.ammeterFields = ('current','voltage','time')
        serialPortName = "/dev/ttyACM0"
        self.ammeter = MozillaAmmeter(serialPortName, False)

        sample = self.ammeter.getSample(self.ammeterFields)
        sampleTimeAfterEpochOffset = time.time()
        firstSampleMsCounter = sample['time'].value
        self.sampleTimeEpochOffset = int(sampleTimeAfterEpochOffset * 1000.0) - firstSampleMsCounter;


    def test_unlock_to_homescreen(self):
        """https://moztrap.mozilla.org/manage/case/1296/"""

        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()

        self.wait_for_condition(lambda m: self.apps.displayed_app.name == homescreen.name)
	print "Waiting 30 seconds to stabilize"
	time.sleep(30)

        sampleLog = []
	print "Starting power test"
        stopTime = time.time() + 10
        done = False
	total = 0
        while not done:
            sample = self.ammeter.getSample(self.ammeterFields)
            if sample is not None:
                sampleObj = {}
                sampleObj['current'] = sample['current'].value
		total += sampleObj['current']
                sampleObj['voltage'] = sample['voltage'].value
                sampleObj['time'] = sample['time'].value + self.sampleTimeEpochOffset
                sampleLog.append(sampleObj)
            done = (time.time() > stopTime)

	averageCurrent = total / len(sampleLog)
        powerProfile = {}
        powerProfile['sampleTimeEpochOffset'] = self.sampleTimeEpochOffset
        powerProfile['samples'] = sampleLog
#        print json.dumps(powerProfile, sort_keys=True, indent=4, separators=(',', ': '))
        print "Sample count: ", len(sampleLog)
	print "Average current: ", averageCurrent
        self.ammeter.close()
