#!/usr/bin/env python

# based on pymp -> http://jdolan.dyndns.org/trac/wiki/Pymp
# /me thanks a lot


# TODO:
# check if mplayer is installed at all
#   -> issue a warning


import sys, os, fcntl, gobject, time

STATUS_TIMEOUT = 1000

#
#  Provides simple piped I/O to an mplayer process.
#
class Player(gobject.GObject):
  
  paused = False
  
  def __init__(self):
    self.__gobject_init__()

  def play(self, target):
    """
    plays the given target where target is the url or path to the file
    """

    pass

  def pause(self):
    """
    pause playback
    """
    pass

  def seek(self, amount, mode=0):
    """
    Seeks the amount using the specified mode.  See mplayer docs.
    """
    #self.pymp.mplayer.cmd("seek " + str(amount) + " " + str(mode))
    #self.pymp.mplayer.queryStatus()
    pass
  

gobject.type_register(Player)
gobject.signal_new("playback_stopped", Player, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
gobject.signal_new("set_position", Player, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())


