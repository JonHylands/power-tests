# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from gaiatest import GaiaTestCase
from gaiatest.apps.lockscreen.app import LockScreen
from powertests import TestPower


class TestWifiHomescreenPower(TestPower):

    def setUp(self):
        TestPower.setUp(self)
        self.data_layer.set_setting("airplaneMode.enabled", False)


    def test_wifi_homescreen_off(self):
        """https://moztrap.mozilla.org/manage/case/1296/"""

        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()

        self.data_layer.disable_wifi() # make sure it starts out disabled
        self.data_layer.connect_to_wifi()
        print "Connected to wifi"

        self.wait_for_condition(lambda m: self.apps.displayed_app.name == homescreen.name)
        self.device.turn_screen_off()
        print ""
        print "Running Wifi Idle Test (screen off)"
        self.runPowerTest("idle_wifi_screen_off", "Homescreen", "verticalhome")


    def test_wifi_homescreen_on(self):
        """https://moztrap.mozilla.org/manage/case/1296/"""

        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()

        self.data_layer.disable_wifi() # make sure it starts out disabled
        self.data_layer.connect_to_wifi()
        print "Connected to wifi"

        self.wait_for_condition(lambda m: self.apps.displayed_app.name == homescreen.name)
        print ""
        print "Running Wifi Idle Test (screen on)"
        self.runPowerTest("idle_wifi_screen_on", "Homescreen", "verticalhome")


    def tearDown(self):
        TestPower.tearDown(self)

