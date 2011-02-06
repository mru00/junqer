# mru, 2011-01


import gobject
import logging
from inspect import stack

log = logging.getLogger("player")

PLAYSTATE_NULL = 0
PLAYSTATE_PLAYING = 1
PLAYSTATE_PAUSED = 2


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
    log.critical("Player.%s should be overwritten!", stack[0][3])

  def get_state(self):
    """
    returns one of the PLAYSTATE constants
    """
    log.critical("Player.%s should be overwritten!", stack[0][3])

  def pause(self):
    """
    pause playback
    """
    log.critical("Player.%s should be overwritten!", stack[0][3])

  def seek(self, amount):
    """
    seeks to the specified position in percent
    """
    log.critical("Player.%s should be overwritten!", stack[0][3])


  

gobject.type_register(Player)
gobject.signal_new("playback_stopped", Player, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
gobject.signal_new("playback_paused", Player, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())
gobject.signal_new("playback_started", Player, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, ())

gobject.signal_new("set_position", Player, gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT,))


