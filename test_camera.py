# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from gaiatest import GaiaTestCase
from gaiatest.apps.lockscreen.app import LockScreen
from gaiatest.apps.camera.app import Camera
from marionette_driver.marionette import Actions
from marionette_driver.by import By

from power_test_support import TestPower

from powertool.mozilla import MozillaAmmeter
from datetime import datetime

import time
import json
import sys
import os
import subprocess


class TestCameraPower(TestPower):
    _camera_frame_locator = (By.CSS_SELECTOR, 'iframe[src*="camera"][src*="/index.html"]')

    def setUp(self):
        TestPower.setUp(self)


    def test_camera_preview(self):
        """https://moztrap.mozilla.org/manage/case/1296/"""

        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()

        self.wait_for_condition(lambda m: self.apps.displayed_app.name == homescreen.name)

        # Turn off the geolocation prompt, and then launch the camera app
        self.apps.set_permission('Camera', 'geolocation', 'deny')
        self.camera = Camera(self.marionette)
        self.camera.launch()
        self.marionette.switch_to_frame()
        self.wait_for_element_present(*self._camera_frame_locator)
        camera_frame = self.marionette.find_element(*self._camera_frame_locator)
        camera_frame.tap()
        self.marionette.switch_to_frame(camera_frame)

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
        time.sleep(5)
        self.camera.tap_switch_source()
        time.sleep(5)
        self.marionette.switch_to_frame()
        self.wait_for_element_present(*self._camera_frame_locator)
        camera_frame = self.marionette.find_element(*self._camera_frame_locator)
        camera_frame.tap()
        self.marionette.switch_to_frame(camera_frame)
        self.camera.tap_capture()

        print ""
        print "Running Camera Video Test"
        self.runPowerTest("camera_video", "Camera", "camera")
        self.camera.tap_capture()


    def test_camera_picture(self):
        """https://moztrap.mozilla.org/manage/case/1296/"""

        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()

        self.wait_for_condition(lambda m: self.apps.displayed_app.name == homescreen.name)

        # Turn off the geolocation prompt, and then launch the camera app
        self.apps.set_permission('Camera', 'geolocation', 'deny')
        self.camera = Camera(self.marionette)
        self.camera.launch()
        self.marionette.switch_to_frame()
        self.wait_for_element_present(*self._camera_frame_locator)
        camera_frame = self.marionette.find_element(*self._camera_frame_locator)
        camera_frame.tap()
        self.marionette.switch_to_frame(camera_frame)

        print ""
        print "Running Camera Picture Test"
        self.runPowerTest("camera_picture", "Camera", "camera")


    def tearDown(self):
        TestPower.tearDown(self)

