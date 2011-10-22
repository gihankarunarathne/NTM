# -*- coding: UTF-8 -*-

#
# NKPlayer Ver. 0.2
#

#
# NKPlayer Copyright (C) 2009-2011 by Luigi Tullio <tluigi@gmail.com>.
#
#   NTM is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or (at your option)
# any later version.
#
#   NTM is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#


import pygst
pygst.require("0.10")
import gst
import os
#import thread
#import gobject


class NKPlayer():

    # filen_name : audio file to play
    def __init__(self, file_name):
        self.file_name = file_name
        self.state = -1
        self.player = gst.element_factory_make("playbin", "player")
        fakesink = gst.element_factory_make("fakesink", "fakesink")
        self.player.set_property("video-sink", fakesink)
        bus = self.player.get_bus()
        bus.add_signal_watch()
        bus.connect("message::eos", self.on_message)
        bus.connect("message::error", self.on_message)
        self.player.set_property("uri", "file://" + os.path.abspath(file_name))
        self.state = 0
        #mloop = gobject.MainLoop()
        #gobject.threads_init()
        #thread.start_new_thread(mloop.run, ())
    
    def play(self, loop=False):
        self.loop = loop
        self.state = 1
        self.player.set_state(gst.STATE_PLAYING)

    def stop(self):
        self.state = 0
        self.player.set_state(gst.STATE_NULL)

    def on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_EOS:
            self.player.set_state(gst.STATE_NULL)
            if (self.state == 1) and (self.loop):
                self.player.set_state(gst.STATE_PLAYING)
            else: self.state = 0
        elif t == gst.MESSAGE_ERROR:
            self.state = 0
            self.player.set_state(gst.STATE_NULL)
            err, debug = message.parse_error()
            print "Error: %s" % err, debug


