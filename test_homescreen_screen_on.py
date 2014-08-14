# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from gaiatest import GaiaTestCase
from gaiatest.apps.lockscreen.app import LockScreen
from gaiatest.apps.camera.app import Camera

from powertool.mozilla import MozillaAmmeter
from datetime import datetime

import time
import json
import sys
import os
import subprocess

STABILIZATION_TIME = 30 # seconds
SAMPLE_TIME = 30 # seconds

class TestLockScreen(GaiaTestCase):

    def setUp(self):
        print "setUp - start"
        GaiaTestCase.setUp(self)

        print "setUp - about to lock"
        # Make sure the lock screen is up
        self.device.lock()

        # Make sure the screen brightness is full on, with auto turned off
        self.data_layer.set_setting("screen.automatic-brightness", False)
        self.data_layer.set_setting("screen.brightness", 1.0)

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


    def runPowerTest(self, testName, appName):
        print ""
        print "Waiting", STABILIZATION_TIME, "seconds to stabilize"
        time.sleep(STABILIZATION_TIME)

        sampleLog = []
        samples = []
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
                samples.append(str(sample['current'].value))
                totalCurrent += sampleObj['current']
            done = (time.time() > stopTime)

        averageCurrent = int(totalCurrent / len(sampleLog))
        powerProfile = {}
        powerProfile['testTime'] = datetime.now().strftime("%Y%m%d%H%M%S")
        powerProfile['sampleLog'] = sampleLog
        powerProfile['samples'] = samples
        powerProfile['testName'] = testName
        powerProfile['average'] = averageCurrent
        powerProfile['app'] = appName
        print "Sample count:", len(sampleLog)
        print "Average current:", averageCurrent, "mA"
        self.writeTestResults(powerProfile)


    def writeTestResults(self, powerProfile):
        summaryName = '%s_%s_summary.log' % (powerProfile['testName'], powerProfile['testTime'])
        summaryFile = open(summaryName, 'w')
        summaryFile.write("test_name: %s\n" % powerProfile["testName"])
        summaryFile.write("completed: %s\n" % powerProfile["testTime"])
        summaryFile.write("test_runtime: %d\n" % SAMPLE_TIME)
        summaryFile.write("average: %d\n" % powerProfile["average"])
        summaryFile.write("app_under_test: %s\n" % powerProfile["app"])
        #summaryFile.write("samples: ")
        #summaryFile.write(", ".join(powerProfile['samples']))
        summaryFile.write("\n")
        summaryFile.close()


    def test_unlock_to_homescreen_off(self):
        """https://moztrap.mozilla.org/manage/case/1296/"""

        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()

        self.wait_for_condition(lambda m: self.apps.displayed_app.name == homescreen.name)
        self.device.turn_screen_off()
        print ""
        print "Running Idle Test (screen off)"
        self.runPowerTest("idle_screen_off", "homescreen")


    def test_unlock_to_homescreen_on(self):
        """https://moztrap.mozilla.org/manage/case/1296/"""

        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()

        self.wait_for_condition(lambda m: self.apps.displayed_app.name == homescreen.name)
        print ""
        print "Running Idle Test (screen on)"
        self.runPowerTest("idle_screen_on", "homescreen")


    def test_camera_preview(self):
        """https://moztrap.mozilla.org/manage/case/1296/"""

        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()

        self.wait_for_condition(lambda m: self.apps.displayed_app.name == homescreen.name)

        # Turn off the geolocation prompt, and then launch the camera app
        self.apps.set_permission('Camera', 'geolocation', 'deny')
        self.camera = Camera(self.marionette)
        self.camera.launch()

        print ""
        print "Running Camera Preview Test"
        self.runPowerTest("camera_preview", "camera")


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
        time.sleep(1)
