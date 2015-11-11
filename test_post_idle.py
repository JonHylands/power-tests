# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from gaiatest import GaiaTestCase
from gaiatest.apps.homescreen.regions.permission_dialog import PermissionDialog
from gaiatest.apps.lockscreen.app import LockScreen

from powertests import TestPower
import time
from marionette_driver import expected, By, Wait
from gaiatest.apps.camera.app import Camera
from gaiatest.apps.search.app import Search
from gaiatest.apps.settings.app import Settings
from gaiatest.apps.keyboard.app import Keyboard

import pdb


class TestPostIdlePower(TestPower):

    _geoloc_start_button_locator = (By.ID, 'permission-yes')
    _camera_frame_locator = (By.CSS_SELECTOR, 'iframe[src*="camera"][src*="/index.html"]')


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


    def test_post_camera_preview(self):

        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()

        # Turn off the geolocation prompt, and then launch the camera app
        self.apps.set_permission('Camera', 'geolocation', 'deny')
        self.camera = Camera(self.marionette)
        self.camera.launch()
        while (self.camera.current_flash_mode != 'off'):
            self.camera.tap_toggle_flash_button();
        time.sleep(2)
        self.marionette.switch_to_frame()        
        camera_frame = Wait(self.marionette, timeout=120).until(
            expected.element_present(*self._camera_frame_locator))
        camera_frame.tap()
        self.marionette.switch_to_frame(camera_frame)
        time.sleep(20)
        self.device.touch_home_button()
        time.sleep(10)
        self.device.turn_screen_off()

        print ""
        print "Running Post Camera Preview Test"
        self.runPowerTest("post_idle_camera_preview", "Camera", "camera")


    def test_post_bluetooth(self):

        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()

        settings = Settings(self.marionette)
        settings.launch()
        bluetooth_settings = settings.open_bluetooth()

        self.data_layer.bluetooth_disable() # make sure it starts out disabled
        self.data_layer.bluetooth_enable()
        print "Enabled bluetooth"
        time.sleep(20)
        # Sometimes the BT device doesn't show up in the list right off. Try and click it, 
        # if we can't then do an actual search and then try to click it again
        if not bluetooth_settings.tap_device('HC-06'):
            print "About to search for devices"
            bluetooth_settings.tap_search_for_devices()
            print "Tapped search for devices"
            time.sleep(15)
            if not bluetooth_settings.tap_device('HC-06'):
                assert False, "Unable to find bluetooth device 'HC-06'..."
        keyboard = Keyboard(self.marionette)
        #time.sleep(1)
        keyboard.send("1234")
        keyboard.tap_enter()
        time.sleep(35)
        print "Done sleep, disabling bluetooth"
        self.data_layer.bluetooth_disable()
        print "Disabled bluetooth"

        self.device.turn_screen_off()
        print ""
        print "Running Post Bluetooth Test"
        self.runPowerTest("post_idle_bluetooth", "Settings", "settings")


    def tearDown(self):
        TestPower.tearDown(self)

