# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from gaiatest import GaiaTestCase
from gaiatest.apps.lockscreen.app import LockScreen
from gaiatest.apps.music.app import Music
from gaiatest.apps.videoplayer.app import VideoPlayer

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
        # Volume level adjust to 9 and turn on airplane mode
        self.data_layer.set_setting("screen.automatic-brightness", False)
        self.data_layer.set_setting("screen.brightness", 1.0)
        self.data_layer.set_setting("audio.volume.content", 9)
        self.data_layer.set_setting("airplaneMode.enabled", True)

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

    def test_background_music_playback(self):
        self.push_resource(os.path.abspath('source/MP3_Au4.mp3'))
        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()
        self.wait_for_condition(lambda m: self.apps.displayed_app.name == homescreen.name)

        music_app = Music(self.marionette)
        music_app.launch()
        music_app.wait_for_music_tiles_displayed()

        # switch to songs view
        list_view = music_app.tap_songs_tab()

        # check that songs (at least one) are available
        songs = list_view.media
        self.assertGreater(len(songs), 0, 'The file could not be found')

        player_view = songs[0].tap_first_song()

        play_time = time.strptime('00:03', '%M:%S')
        self.wait_for_condition(lambda m: player_view.player_elapsed_time >= play_time)

        # validate playback
        self.assertTrue(player_view.is_player_playing(), 'The player is not playing')

        self.marionette.switch_to_frame()
        self.device.turn_screen_off()
        print ""
        print "Running Music Test (screen off)"
        self.runPowerTest("background_music_playback", "Music", "music")

    def test_video_playback(self):
        self.push_resource(os.path.abspath('source/meetthecubs.webm'))
        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()
        self.wait_for_condition(lambda m: self.apps.displayed_app.name == homescreen.name)

        video_player = VideoPlayer(self.marionette)
        video_player.launch()
        video_player.wait_for_thumbnails_to_load(1, 'Video files found on device: %s' %self.data_layer.video_files)

        # Assert that there is at least one video available
        self.assertGreater(video_player.total_video_count, 0)

        first_video_name = video_player.first_video_name

        self.assertEqual('none', self.data_layer.current_audio_channel)
        self.apps.switch_to_displayed_app()

        # Click on the first video
        fullscreen_video = video_player.tap_first_video_item()

        # Video will play automatically
        # We'll wait for the controls to clear so we're 'safe' to proceed
        time.sleep(2)

        # We cannot tap the toolbar so let's just enable it with javascript
        fullscreen_video.show_controls()

        # The elapsed time > 0:00 denote the video is playing
        zero_time = time.strptime('00:00', '%M:%S')
        self.assertGreater(fullscreen_video.elapsed_time, zero_time)

        # Check the name too. This will only work if the toolbar is visible
        self.assertEqual(first_video_name, fullscreen_video.name)

        self.assertEqual('content', self.data_layer.current_audio_channel)

        print ""
        print "Running Video Test"
        self.runPowerTest("video_playback", "Video", "video")

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
