import sys, os
import pygtk, gtk, gobject
import pygst
pygst.require("0.10")
import gst
import logging


log = logging.getLogger("player.gstreamer")

import player


gobject.threads_init()

class gstreamerPlayer(player.Player):
  
  eofHandler, statusQuery = 0, 0
  paused = False
  
  def __init__(self, wid):
    super(gstreamerPlayer,self).__init__()
    
    self.wid = wid

    self.player = gst.element_factory_make("playbin2", "player")

    bus = self.player.get_bus()
    bus.add_signal_watch()
    bus.enable_sync_message_emission()
    bus.connect("message", self.on_message)
    bus.connect("sync-message::element", self.on_sync_message)
    log.debug("player created")



  def pause(self):

    log.debug("invoked pause!")

    if self.player.get_state() == gst.STATE_NULL:
      logging.error("cannot pause when nothing is playing")


    if gst.STATE_PLAYING in self.player.get_state():
      self.player.set_state(gst.STATE_PAUSED)
      self.emit("playback_paused")
    else:
      log.error("player in wrong state for pause: %s", str(self.player.get_state()))

  def get_state(self):
    s = { gst.STATE_NULL : player.PLAYSTATE_NULL,
        gst.STATE_PLAYING: player.PLAYSTATE_PLAYING, 
        gst.STATE_PAUSED: player.PLAYSTATE_PAUSED }
    
    return s.get(self.player.get_state(), player.PLAYSTATE_NULL)

  def _get_state(self):
    return filter( lambda a: type(a) == type(gst.STATE_NULL),self.player.get_state())

  def seek(self, pos):

    if gst.STATE_NULL in self._get_state():

      return False
    
    (dur,_) = self.player.query_duration(gst.FORMAT_TIME)
    pos = (pos /  100)*dur
    log.debug("pos: %d dur: %d", pos, dur)
    flags = gst.SEEK_FLAG_FLUSH | gst.SEEK_FLAG_KEY_UNIT
    flags = gst.SEEK_FLAG_FLUSH 
    self.player.seek_simple(gst.FORMAT_TIME, flags, pos)

  def play(self, target):
    """
    plays the target (=uri) if given, else continues from play
    """

    log.debug("invoked play, target= %s", target)

    if target:
      self.player.set_state(gst.STATE_NULL)
      self.player.set_property("uri", target.get_uri())

    self.player.set_state(gst.STATE_PLAYING)
    self.emit("playback_started")
    gobject.timeout_add(100, self.emit_position)

  def on_message(self, bus, message):
    t = message.type
    if t == gst.MESSAGE_EOS:
      self.player.set_state(gst.STATE_NULL)
      self.emit("playback_stopped")
    elif t == gst.MESSAGE_ERROR:
      self.player.set_state(gst.STATE_NULL)
      err, debug = message.parse_error()
      log.critical("Error: %s",err, debug)
                                    
  def on_sync_message(self, bus, message):
    if message.structure is None:
      return
    message_name = message.structure.get_name()
    log.debug("received sync message: %s", message)
    if message_name == "prepare-xwindow-id":
      imagesink = message.src
      imagesink.set_property("force-aspect-ratio", True)
      try:
        gtk.gdk.threads_enter()
        imagesink.set_xwindow_id(self.wid)
      finally:
        gtk.gdk.threads_leave()

  def emit_position(self):
    if gst.STATE_NULL in self._get_state():
      return False

    (pos,_) = self.player.query_position(gst.FORMAT_TIME)
    (dur,_) = self.player.query_duration(gst.FORMAT_TIME)

    self.emit("set_position", int(100 * pos / dur))
    return True







