# mru, 2011-01


import gobject

class Player(gobject.GObject):
  """
  baseclass for the player implementations and
  informal interface specification for the player classes
  """
  
  def __init__(self):
    """
    wid: x-window-id where the player should be embedded
    """
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

  def set_fullscreen(self, fs):
    pass

  

gobject.type_register(Player)
gobject.signal_new("playback_stopped", Player, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
gobject.signal_new("set_position", Player, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())


