#!/usr/bin/env python

# based on pymp -> http://jdolan.dyndns.org/trac/wiki/Pymp
# /me thanks a lot


# TODO:
# check if mplayer is installed at all
#   -> issue a warning

from player import Player
import sys, os, fcntl, gobject, time

STATUS_TIMEOUT = 1000

#
#  Provides simple piped I/O to an mplayer process.
#
class MPlayer(Player):
  
  eofHandler, statusQuery = 0, 0
  paused = False
  MPLAYER_VO='vdpau'
  MPLAYER_FS=True
  
  #
  #  Initializes this Mplayer with the specified Pymp.
  #
  def __init__(self,wid):
    super(MPlayer,self).__init__()
    self.mplayerIn = None
    self.mplayerOut = None
    self.wid = wid
  #
  #   Plays the specified target.
  #
  def play(self, (path,uri)):
    
    if self.MPLAYER_FS:
      fs = " -fs"
    else:
      fs = ""
    mpc = "mplayer -wid %d -slave -vo %s -quiet %s '%s' 2>/dev/null" % (self.wid, 
        self.MPLAYER_VO, 
        fs, 
        path)
    
    self.mplayerIn, self.mplayerOut = os.popen2(mpc)  #open pipe
    fcntl.fcntl(self.mplayerOut, fcntl.F_SETFL, os.O_NONBLOCK)
    
    self.startEofHandler()
    self.startStatusQuery()
    
  #
  #  Issues command to mplayer.
  #
  def cmd(self, command):
    
    if not self.mplayerIn:
      return
    
    try:
      self.mplayerIn.write(command + "\n")
      self.mplayerIn.flush()  #flush pipe
    except StandardError:
      return
    
  #
  #  Toggles pausing of the current mplayer job and status query.
  #
  def pause(self):
    
    if not self.mplayerIn:
      return
      
    if self.paused:  #unpause
      self.startStatusQuery()
      self.paused = False
      
    else:  #pause
      self.stopStatusQuery()
      self.paused = True
      
    self.cmd("pause")
    
  #
  #  Seeks the amount using the specified mode.  See mplayer docs.
  #
  def seek(self, amount, mode=0):
    #self.pymp.mplayer.cmd("seek " + str(amount) + " " + str(mode))
    #self.pymp.mplayer.queryStatus()
    pass
  
  #
  #  Cleanly closes any IPC resources to mplayer.
  #
  def close(self):
    
    if self.paused:  #untoggle pause to cleanly quit
      self.pause()
    
    self.stopStatusQuery()  #cancel query
    self.stopEofHandler()  #cancel eof monitor
    
    self.cmd("quit")  #ask mplayer to quit
    
    try:      
      self.mplayerIn.close()   #close pipes
      self.mplayerOut.close()
    except StandardError:
      pass
      
    self.mplayerIn, self.mplayerOut = None, None
    #self.pymp.control.setProgress(-1)  #reset bar
    
  #
  #  Triggered when mplayer's stdout reaches EOF.
  #
  def handleEof(self, source, condition):
    
    self.stopStatusQuery()  #cancel query
    while True: 
      try:  #attempt to fetch last line of output
        line = self.mplayerOut.readline()
        print "mplayer:" , line
        if not line: break
      except StandardError:
        break
    self.mplayerIn, self.mplayerOut = None, None
    
    self.emit("playback_stopped")
      
    return False
    
  #
  #  Queries mplayer's playback status and upates the progress bar.
  #
  def queryStatus(self):
    
    self.cmd("get_percent_pos")  #submit status query
    self.cmd("get_time_pos")
    
    time.sleep(0.05)  #allow time for output
    
    line, percent, seconds = None, -1, -1
    
    while True:
      try:  #attempt to fetch last line of output
        line = self.mplayerOut.readline()
        print "mplayer:" , line
      except StandardError:
        break
        
      if not line: break
      
      if line.startswith("ANS_PERCENT_POSITION"):
        percent = int(line.replace("ANS_PERCENT_POSITION=", ""))
      
      if line.startswith("ANS_TIME_POSITION"):
        seconds = float(line.replace("ANS_TIME_POSITION=", ""))
    
    #self.pymp.control.setProgress(percent, seconds)
    return True
    
  #
  #  Inserts the status query monitor.
  #
  def startStatusQuery(self):
    self.statusQuery = gobject.timeout_add(STATUS_TIMEOUT, self.queryStatus)
    
  #
  #  Removes the status query monitor.
  #
  def stopStatusQuery(self):
    if self.eofHandler:
      gobject.source_remove(self.statusQuery)
    self.statusQuery = 0
    
  #
  #  Inserts the EOF monitor.
  #
  def startEofHandler(self):
    self.eofHandler = gobject.io_add_watch(self.mplayerOut, gobject.IO_HUP, self.handleEof)
  
  #
  #  Removes the EOF monitor.
  #
  def stopEofHandler(self):
    if self.eofHandler:
      gobject.source_remove(self.eofHandler)
    self.eofHandler = 0
    


