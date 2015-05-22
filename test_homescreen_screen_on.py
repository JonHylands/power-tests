# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from gaiatest import GaiaTestCase
from gaiatest.apps.lockscreen.app import LockScreen

from powertests import TestPower

from datetime import datetime

import time
import json
import sys
import os
import subprocess

class TestHomescreenPower(TestPower):

    def setUp(self):
        TestPower.setUp(self)


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


    def tearDown(self):
        TestPower.tearDown(self)

