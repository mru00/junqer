import sys, os
import pygtk, gtk, gobject
import pygst
pygst.require("0.10")
import gst


from player import Player


gobject.threads_init()

class gstreamerPlayer(Player):
  
  eofHandler, statusQuery = 0, 0
  paused = False
  
  #
  #  Initializes this Mplayer with the specified Pymp.
  #
  def __init__(self, wid):
    super(gstreamerPlayer,self).__init__()
    
    self.wid = wid

    self.player = gst.element_factory_make("playbin2", "player")

    bus = self.player.get_bus()
    bus.add_signal_watch()
    bus.enable_sync_message_emission()
    bus.connect("message", self.on_message)
    bus.connect("sync-message::element", self.on_sync_message)



  def play(self, (path,uri)):
    """
    plays the target (=uri)
    """

    self.player.set_property("uri", uri)
    self.player.set_state(gst.STATE_PLAYING)

  def on_message(self, bus, message):
    t = message.type
    if t == gst.MESSAGE_EOS:
      self.player.set_state(gst.STATE_NULL)
      self.emit("playback_stopped")
    elif t == gst.MESSAGE_ERROR:
      self.player.set_state(gst.STATE_NULL)
      err, debug = message.parse_error()
      print "Error: %s" % err, debug
                                    
  def on_sync_message(self, bus, message):
    if message.structure is None:
      return
    message_name = message.structure.get_name()
    if message_name == "prepare-xwindow-id":
      imagesink = message.src
      imagesink.set_property("force-aspect-ratio", True)
      try:
        gtk.gdk.threads_enter()
        imagesink.set_xwindow_id(self.wid)
      finally:
        gtk.gdk.threads_leave()



  def pause(self):
    self.player.set_state(gst.STATE_NULL)
    


