# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from gaiatest import GaiaTestCase
from gaiatest.apps.homescreen.regions.permission_dialog import PermissionDialog
from gaiatest.apps.lockscreen.app import LockScreen

from powertests import TestPower
import time
from marionette_driver import expected, By, Wait
from gaiatest.apps.search.app import Search


class TestPostIdlePower(TestPower):

    _geoloc_start_button_locator = (By.ID, 'permission-yes')


    def setUp(self):
        TestPower.setUp(self)
        self.data_layer.set_setting("airplaneMode.enabled", False)


    def test_post_wifi_disable(self):

        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()

        #homescreen.wait_to_be_displayed()
        self.data_layer.disable_wifi() # make sure it starts out disabled
        self.data_layer.connect_to_wifi()
        print "Connected to wifi"
        time.sleep(30)
        self.data_layer.disable_wifi()
        print "Disabled wifi"

        self.device.turn_screen_off()
        print ""
        print "Running Post Wifi Test (screen off)"
        self.runPowerTest("post_idle_wifi", "Homescreen", "verticalhome")


    def go_to_url(self, homescreen, url):
        search = Search(self.marionette)
        search.launch()
        browser = search.go_to_url(url)


    def post_idle_wifi_browser_run_test(self, url, test_name, permissionFlag = False):

        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()

        self.data_layer.disable_wifi() # make sure it starts out disabled
        self.data_layer.connect_to_wifi()
        print "Connected to wifi"

        self.apps.switch_to_displayed_app()
        self.go_to_url(homescreen, url)
        print "Opened URL"
        if permissionFlag:
            time.sleep(2)
            print "Looking for Permission Dialog"
            permission = PermissionDialog(self.marionette)
            permission.wait_for_permission_dialog_displayed()
            print "Pressing Share Button"
            permission.tap_to_confirm_permission()

        print "Waiting 30 seconds for URL to load"
        time.sleep(30)
        self.device.touch_home_button()
        #homescreen.wait_to_be_displayed()
        self.data_layer.disable_wifi()
        print "Disabled wifi"
        self.device.turn_screen_off()
        print ""
        print "Running Test (", test_name, ")"
        self.runPowerTest(test_name, "Browser", "browser")


    def test_post_maps(self):

        url = "https://maps.google.com"
        self.post_idle_wifi_browser_run_test(url, "post_idle_maps", True)


    def tearDown(self):
        TestPower.tearDown(self)

