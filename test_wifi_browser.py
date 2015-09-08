# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from gaiatest import GaiaTestCase
from gaiatest.apps.lockscreen.app import LockScreen
from powertests import TestPower
from marionette_driver import expected, By, Wait


class TestWifiBrowserPower(TestPower):

    name = 'Browser'
    manifest_url = "app://search.gaiamobile.org/manifest.webapp"

    #_url_bar_locator = (By.CSS_SELECTOR, 'div.search-app .urlbar .title')
    _url_bar_locator = (By.ID, 'search-input')
    #_history_item_locator = (By.CSS_SELECTOR, '#history .result')
    #_private_window_locator = (By.ID, 'private-window')


    def setUp(self):
        TestPower.setUp(self)
        self.data_layer.set_setting("airplaneMode.enabled", False)


    def go_to_url(self, homescreen, url):
        self.marionette.find_element(*self._url_bar_locator).tap()
        search_panel = homescreen.tap_search_bar()
        return search_panel.go_to_url(url)


    def test_wifi_browser_yahoo(self):
        """https://moztrap.mozilla.org/manage/case/1296/"""

        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()

        self.data_layer.connect_to_wifi()
        print "Connected to wifi"

        self.apps.switch_to_displayed_app()
        self.go_to_url(homescreen, "http://www.yahoo.com")
        print ""
        print "Running Wifi Browser Test (Yahoo)"
        self.runPowerTest("wifi_browser_yahoo", "Browser", "browser")


    def tearDown(self):
        TestPower.tearDown(self)

