# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from gaiatest import GaiaTestCase
from gaiatest.apps.lockscreen.app import LockScreen
from powertests import TestPower
from marionette_driver import expected, By, Wait
from gaiatest.apps.search.app import Search


class TestWifiBrowserPower(TestPower):


    def setUp(self):
        TestPower.setUp(self)
        self.data_layer.set_setting("airplaneMode.enabled", False)


    def go_to_url(self, homescreen, url):
        search = Search(self.marionette)
        search.launch()
        browser = search.go_to_url(url)


    def wifi_browser_run_test(self, url, test_name):
        """https://moztrap.mozilla.org/manage/case/1296/"""

        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()

        self.data_layer.disable_wifi() # make sure it starts out disabled
        self.data_layer.connect_to_wifi()
        print "Connected to wifi"

        self.apps.switch_to_displayed_app()
        self.go_to_url(homescreen, url)
        print ""
        print "Running Wifi Browser Test (", test_name, ")"
        self.runPowerTest(test_name, "Browser", "browser")


    def test_wifi_browser_download(self):
        """https://moztrap.mozilla.org/manage/case/1296/"""
        
        url = "https://queue.taskcluster.net/v1/task/HSMUuJewT6qQW7iJ_ohV-Q/artifacts/public/build/flame.blobfree-dist.zip"
        self.wifi_browser_run_test(url, "wifi_browser_download")


    def test_wifi_browser_node(self):
        """https://moztrap.mozilla.org/manage/case/1296/"""

        url = "http://192.168.1.177:5000"
        self.wifi_browser_run_test(url, "wifi_browser_node")


    def tearDown(self):
        TestPower.tearDown(self)

