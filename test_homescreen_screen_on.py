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
PICTURE_TIME = 5 # seconds between photos

class TestPower(GaiaTestCase):

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


    def runPowerTestLoopSimple(self, testName, appName, context):
        sampleLog = []
        samples = []
        totalCurrent = 0
        done = False
        stopTime = time.time() + SAMPLE_TIME
        while not done:
            current = self.getSample(sampleLog, samples)
            if current is not None:
                totalCurrent += current
            done = (time.time() > stopTime)

        averageCurrent = int(totalCurrent / len(sampleLog))
        return (sampleLog, samples, averageCurrent)


    def runPowerTestCameraPictures(self, testName, appName, context):
        sampleLog = []
        samples = []
        totalCurrent = 0
        done = False
        stopTime = time.time() + SAMPLE_TIME
        nextPictureTime = time.time() + PICTURE_TIME
        while not done:
            current = self.getSample(sampleLog, samples)
            if current is not None:
                totalCurrent += current
            timeNow = time.time()
            if timeNow > nextPictureTime:
                self.camera.take_photo()
                nextPictureTime = timeNow + PICTURE_TIME
            done = (timeNow > stopTime)

        averageCurrent = int(totalCurrent / len(sampleLog))
        return (sampleLog, samples, averageCurrent)


    def runPowerTest(self, testName, appName, context):
        print ""
        print "Waiting", STABILIZATION_TIME, "seconds to stabilize"
        time.sleep(STABILIZATION_TIME)

        print "Starting power test, gathering results for", SAMPLE_TIME, "seconds"
        if testName == "camera_picture":
            (sampleLog, samples, averageCurrent) = self.runPowerTestCameraPictures(testName, appName, context)
        else:
            (sampleLog, samples, averageCurrent) = self.runPowerTestLoopSimple(testName, appName, context)
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


    def writeTestResults(self, powerProfile):
        summaryName = '%s_%s_summary.log' % (powerProfile['testName'], powerProfile['testTime'])
        summaryFile = open(summaryName, 'w')
        summaryFile.write("name: power.%s.current\n" % powerProfile["testName"])
        summaryFile.write("time: %s\n" % powerProfile["epoch"])
        summaryFile.write("value: %s\n" % powerProfile["average"])
        summaryFile.write("context: %s\n" % powerProfile["context"])
        summaryFile.write("app_name: %s\n" % powerProfile["app"])
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
        self.runPowerTest("idle_screen_off", "Homescreen", "verticalhome")


    def test_unlock_to_homescreen_on(self):
        """https://moztrap.mozilla.org/manage/case/1296/"""

        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()

        self.wait_for_condition(lambda m: self.apps.displayed_app.name == homescreen.name)
        print ""
        print "Running Idle Test (screen on)"
        self.runPowerTest("idle_screen_on", "Homescreen", "verticalhome")


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
        self.runPowerTest("camera_preview", "Camera", "camera")


    def test_camera_video(self):
        """https://moztrap.mozilla.org/manage/case/1296/"""

        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()

        self.wait_for_condition(lambda m: self.apps.displayed_app.name == homescreen.name)

        # Turn off the geolocation prompt, and then launch the camera app
        self.apps.set_permission('Camera', 'geolocation', 'deny')
        self.camera = Camera(self.marionette)
        self.camera.launch()
        time.sleep(10)
        self.camera.tap_switch_source()
        time.sleep(5)
        self.camera.record_video(10)

        print ""
        print "Running Camera Video Test"
        self.runPowerTest("camera_video", "Camera", "camera")


    def test_camera_picture(self):
        """https://moztrap.mozilla.org/manage/case/1296/"""

        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()

        self.wait_for_condition(lambda m: self.apps.displayed_app.name == homescreen.name)

        # Turn off the geolocation prompt, and then launch the camera app
        self.apps.set_permission('Camera', 'geolocation', 'deny')
        self.camera = Camera(self.marionette)
        self.camera.launch()

        print ""
        print "Running Camera Picture Test"
        self.runPowerTest("camera_picture", "Camera", "camera")


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
