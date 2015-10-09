# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from gaiatest import GaiaTestCase
from gaiatest.apps.lockscreen.app import LockScreen
from gaiatest.apps.music.app import Music
from gaiatest.apps.videoplayer.app import VideoPlayer

from powertests import TestPower
import os
import time

class TestMediaPlaybackPower(TestPower):

    def setUp(self):
        TestPower.setUp(self)


    def music_playback(self, screen_flag):
        self.push_resource(os.path.abspath('source/MP3_Au4.mp3'))
        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()
        #self.wait_for_condition(lambda m: self.apps.displayed_app.name == homescreen.name)

        music_app = Music(self.marionette)
        music_app.launch()
        music_app.wait_for_music_tiles_displayed()

        # switch to songs view
        list_view = music_app.tap_songs_tab()

        # check that songs (at least one) are available
        songs = list_view.media
        self.assertGreater(len(songs), 0, 'The file could not be found')

        player_view = songs[0].tap_first_song()

        play_time = time.strptime('00:10', '%M:%S')
        self.wait_for_condition(lambda m: player_view.player_elapsed_time >= play_time)

        # validate playback
        # self.assertTrue(player_view.is_player_playing(), 'The player is not playing')

        self.marionette.switch_to_frame()
        print ""
        if screen_flag:
            print "Running Music Test (screen on)"
            test_name = "music_playback"
        else:
            self.device.turn_screen_off()
            print "Running Music Test (screen off)"
            test_name = "background_music_playback"
        self.runPowerTest(test_name, "Music", "music")


    def test_background_music_playback(self):
        self.music_playback(False)


    def test_music_playback(self):
        self.music_playback(True)


    def video_playback(self, screen_flag):
        self.push_resource(os.path.abspath('source/meetthecubs.webm'))
        lock_screen = LockScreen(self.marionette)
        homescreen = lock_screen.unlock()
        #self.wait_for_condition(lambda m: self.apps.displayed_app.name == homescreen.name)

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
        if screen_flag:
            print "Running Video Test (screen on)"
            test_name = "video_playback"
        else:
            self.device.turn_screen_off()
            print "Running Video Test (screen off)"
            test_name = "background_video_playback"
            time.sleep(2)
            fullscreen_video.tap_play() #when you turn off the screen, video playback pauses...
        self.runPowerTest(test_name, "Video", "video")


# Background Video Playback doesn't work - the video shuts off shortly after turning off the screen
#    def test_background_video_playback(self):
#        self.video_playback(False)


    def test_video_playback(self):
        self.video_playback(True)


    def tearDown(self):
        TestPower.tearDown(self)
