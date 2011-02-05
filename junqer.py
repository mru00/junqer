#!/usr/bin/env python

# junqer: watching series like a pro!
# mru, 2011-01



import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("main")



import pygtk, gtk, gio
pygtk.require("2.0")
import gconf

from player import Player
from mplayer import MPlayer
from gstreamer import gstreamerPlayer
from showimporter import GnomeShowImporter
from model import *
from suspend import *
from persistance import *
import thetvdbapi
from dialogs import *


tvdb_key = "BFE6162BAD99831B"

# very necessary -> else random hangups
gtk.gdk.threads_init()





class JunqerApp(object):       

  BGCOLOR_UNWATCHED="white"
  BGCOLOR_WATCHED="gray"
  BGCOLOR_SEASON="lightyellow"
  BGCOLOR_SUCCESSOR="green"

  TREECOL_URI=3
  TREECOL_BGCOLOR=2
  TREECOL_PLAYCOUNT=1
  TREECOL_TEXT=0

  GCONF_PATH='/apps/junqer'
  GCONF_BACKEND='/player_backend'

  DEFAULT_BACKEND='gstreamer'

  def __init__(self):
    """
    setup everything
    """


    builder = gtk.Builder()
    builder.add_from_file("glade/junqer.glade")

    builder.connect_signals({
      "on_window_destroy" : self.on_quit,
      "on_actionAbout_activate": self.on_actionAbout_activate,
      "on_actionSave_activate": self.on_actionSave_activate,
      "on_actionQuit_activate": self.on_quit,
      "on_actionPause_activate": self.on_actionPause_activate,
      "on_actionPlay_activate": self.on_actionPlay_activate,
      "on_actionEditShow_activate": self.on_actionEditShow_activate,
      "on_adjustmentPosition_value_changed": self.on_adjustmentPosition_value_changed,
      "on_iconviewShow_item_activated": self.on_show_activated, 
      "on_iconviewShow_selection_changed": self.on_show_selected,
      "on_iconviewShow_drag_data_received": self.on_iconviewShow_drag_data_received,
      "on_iconviewShow_button_press_event": self.on_iconviewShow_button_press_event,
      "on_drawingareaPlayer_key_release_event": self.on_drawingareaPlayer_key_release_event,
      "on_drawingareaPlayer_button_press_event": self.on_drawingareaPlayer_button_press_event,
      "on_drawingareaPlayer_expose_event": self.on_drawingareaPlayer_expose_event,
      "on_treeviewEpisodes_row_activated": self.on_treeviewEpisodes_row_activated,
      "on_treeviewEpisodes_button_press_event": self.on_treeviewEpisodes_button_press_event})

    self.window = builder.get_object("main_window")
    self.treeviewEpisodes = builder.get_object("treeviewEpisodes")
    self.iconviewShow = builder.get_object("iconviewShow")
    self.playWindow = builder.get_object("drawingareaPlayer")
    self.playmore = builder.get_object("adjustmentPlayMore")
    self.fswin = builder.get_object("windowFullScreen")
    self.vboxPlayer = builder.get_object("vboxPlayer")
    self.toolbarPlayer = builder.get_object("toolbarPlayer")
    self.buttonPlayPause = builder.get_object("button_play")
    
    self.builder = builder

    self.iconviewShow.set_text_column(1)
    self.iconviewShow.set_pixbuf_column(2)

    self.currentShow = ''

    self.model = load()
    self.model.dump()
    
    self.window.connect("destroy", self.on_quit)

    self.window.show()
    self.setup_treeview()

    TARGET_TYPE_TEXT=80
    targets = [ ("text/uri-list", 0, TARGET_TYPE_TEXT )]
    self.iconviewShow.enable_model_drag_dest(targets, gtk.gdk.ACTION_LINK)


    self.update_show_model()

    self.setup_player()
    self.tvdb = thetvdbapi.TheTVDB(tvdb_key)


  def focus_player(self):
    self.playWindow.grab_focus()


  def on_adjustmentPosition_value_changed(self,e):
    log.debug('onposition value changed: %s', str(e))
    self.player.seek(e.get_value())



  def on_actionEditShow_activate(self, _):
    showname = self.get_selected_show_name()
    showobj = self.model.get((showname,))
    dlg = DialogEditShow(showobj.meta)
    try:
      if dlg.run() == gtk.RESPONSE_OK:
        showobj.meta = dlg.meta
        showobj.name = dlg.meta['name']
      


    finally:
      dlg.destroy()
      self.update_show_model()

  def setup_player(self):
    """
    choose the player backend and instantiate it
    """


    self.player_xid = self.playWindow.window.xid
    log.debug("using xid %d for playWindow", self.player_xid)

    cclient = gconf.client_get_default()
    cclient.add_dir(self.GCONF_PATH, gconf.CLIENT_PRELOAD_NONE)
    pb= cclient.get_string(self.GCONF_PATH + self.GCONF_BACKEND)
    log.debug("using backend %s", pb)

    if pb and pb == 'gstreamer':
        self.player = gstreamerPlayer(self.player_xid)

    elif pb and pb == 'mplayer':
        self.player = MPlayer(self.player_xid)

    else:
      self.player = gstreamerPlayer(self.playWindow.window.xid)
      cclient.set_string(self.GCONF_PATH  + self.GCONF_BACKEND, self.DEFAULT_BACKEND)
      log.info('no backend configured, using default: %s', self.DEFAULT_BACKEND)


    self.player.connect("playback_stopped", self.on_playback_stopped)
    self.player.connect("playback_started", self.on_playback_started)
    self.player.connect("playback_paused", self.on_playback_paused)
    self.player.connect("set_position", self.on_playback_set_position)


  def on_actionPause_activate(self, _):
    log.debug('invoking pause')
    self.player.pause()

  def on_actionPlay_activate(self, _):
    log.debug('invoking play')
    self.player.play(None)

  def on_drawingareaPlayer_key_release_event(self, w, event):
    """
    TODO: shortcut handling should get here
    """
    k = gtk.gdk.keyval_name(event.keyval)
    log.debug("key pressed: %s", k)
    if k in ('F11', 'f'):
      self.toggle_fullscreen()
    elif k == 'q':
      self.on_quit(None)

  def on_treeviewEpisodes_button_press_event(self, w, event):
    if event.button == 3:
      x = int(event.x)
      y = int(event.y)
      time = event.time
      path = w.get_path_at_pos(x, y)
      if path:
        path, col, cellx, celly = path
        w.grab_focus()
        w.set_cursor(path, col, 0)
        self['menuSeries'].popup(None, None, None, event.button, time)
      return True

  def on_iconviewShow_button_press_event(self, w, event):
    """
    show context menu on show
    """
    if event.button == 3:
      x = int(event.x)
      y = int(event.y)
      time = event.time
      pathinfo = w.get_path_at_pos(x, y)
      if pathinfo:
        w.grab_focus()
        w.select_path(pathinfo)
        w.set_cursor(pathinfo, None, 0)
        self['menuSeries'].popup(None, None, None, event.button, time)
      return True

  def on_drawingareaPlayer_expose_event(self, w, event):
    """
    fill the playWindow with black color
    """
    log.debug("expose on playerwin")
    x , y, width, height = event.area
    w.window.draw_rectangle(w.get_style().black_gc,
        True, x, y, width, height)
    return False


  def on_drawingareaPlayer_button_press_event(self, w, event):
    """
    a double-click in the player window should switch fullscreen
    """

    self.focus_player()
    if event.type != gtk.gdk._2BUTTON_PRESS:
      return False

    self.toggle_fullscreen()
    return False

  def toggle_fullscreen(self):

    try:
#      gtk.gdk.threads_enter()
      if self.vboxPlayer.get_parent() == self.fswin:
        log.debug("unfullscreen")
  
  #      self.fswin.remove(self.vboxPlayer)
  #      self.fs_oparent.add(self.vboxPlayer)
  
        self.vboxPlayer.reparent(self.fs_oparent)
        self.fswin.hide()
        self.toolbarPlayer.show()
        self.playWindow.grab_focus()
        self.playWindow.show_all()
      else:
  
        log.debug("fullscreen!")
        self.fs_oparent = self.vboxPlayer.get_parent()
        self.fswin.show()
  
  #      self.fs_oparent.remove(self.vboxPlayer)
  #      self.fswin.add(self.vboxPlayer)
  
        self.vboxPlayer.reparent(self.fswin)
        self.toolbarPlayer.hide()
        self.fswin.fullscreen()
        self.fswin.show_all()
        self.playWindow.grab_focus()

    finally:
#      gtk.gdk.threads_leave()
      pass


  def suspend(self):
    """
    send computer to sleep
    """

    get_suspender().suspend()






  def on_playback_set_position(self,player,pos):
    """
    when the player reports new position
    """
    log.debug("position: %d", pos)
    adj = self['adjustmentPosition']
    try:
      adj.handler_block_by_func(self.on_adjustmentPosition_value_changed)
      adj.set_value(pos)
    finally:
      adj.handler_unblock_by_func(self.on_adjustmentPosition_value_changed)
    



  def on_playback_started(self, player):
    """
    """
    log.debug("playback started!")
    self['actionPause'].connect_proxy(self.buttonPlayPause)



  def on_playback_paused(self, player):
    """
    """
    log.debug("playback paused!")
    self['actionPlay'].connect_proxy(self.buttonPlayPause)

  def on_playback_stopped(self, player):
    """
    called from the player when the file is finished playing
    """

    log.debug("playback stopped!")
    self['actionPlay'].connect_proxy(self.buttonPlayPause)

    self.playWindow.queue_draw()
    value = int(self.playmore.get_value()) 
    if value > 0 or value == -1:
      self.advance()

    if value > 0:
      self.playmore.set_value(value -1)

  def on_actionSave_activate(self, sender):
    save(self.model)

  def get_successor(self, show_name, season_id, episode_id):
    """
    calulates the indices for the next file, 
    or returns null if no successor
    """

    show = self.model.get((show_name, ))
    season = self.model.get((show_name, season_id))
    
    episodeidx = episode_id + 1

    if episodeidx < len(season.episodes):
      return season_id, episodeidx
    seasonidx = season_id + 1
    if seasonidx < len(show.seasons):
      return seasonidx, 0
    return None


  def advance(self):
    """
    start playing the next file, stop if no more files to play
    """

    successor = self.model.get((self.currentShow,)).successor

    if not successor:
      log.error("no more episodes available!")
      return

    self.play((self.currentShow,) + successor)

  def play(self, path):
    """
    play the given file
    """

    xid = self.playWindow.window.xid
    log.debug("using xid %d for playWindow, was %s", xid, self.player_xid)

    show_name, season_id, episode_id = path
    mshow = self.model.get((show_name,))

    self.currentShow = show_name
    lastsuccessor = mshow.successor
    mshow.successor = self.get_successor(show_name, season_id, episode_id)

    self.update_tree_row((show_name,)+ lastsuccessor)
    self.update_tree_row((show_name,)+ mshow.successor)

    mepisode = self.model.get((show_name, season_id, episode_id))
    mepisode.play_count += 1

    if self.get_selected_show_name() == show_name:
      self.update_tree_row((show_name, season_id))
      self.update_tree_row((show_name, season_id,episode_id))

    f = gio.File(mepisode.uri) 

    log.info("playing file %s", f.get_path())

    self.player.play(f)


  def update_show_model(self):
    """
    updates the icon view for new data in the internal model
    """

    showModel = self.iconviewShow.get_model()
    showModel.clear()

    pixbuf = self.iconviewShow.render_icon(gtk.STOCK_NEW, 
                                           size=gtk.ICON_SIZE_BUTTON, 
                                           detail=None)

    for name, show in self.model.shows.items():
      desc = show.meta.get('overview', '')
      if 'banner' in show.meta and show.meta['banner']:
        pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(show.meta['banner'], 200, 200)
      showModel.append( (name, show.name, pixbuf, desc)) 


  def on_treeviewEpisodes_row_activated(self, treeview, path, view_column):
    """
    double click on file
    """

    episodeModel = self.treeviewEpisodes.get_model()
    if len(path) != 2:
      return

    show = self.get_selected_show_name()
    self.play((show,) + path)

  def get_selected_show_name(self):
    """
    returns the name of the currently selected show-icon
    """

    s0 = self.iconviewShow.get_selected_items()

    if not s0 or len(s0) < 1: 
      # nothing selected, or something unselected
      return None
    
    showSelection = s0[0]

    showModel = self.iconviewShow.get_model()
    show = showModel[showSelection][0]

    return show
       

  def __getitem__(self, index):
    return self.builder.get_object(index)


  def on_iconviewShow_drag_data_received(self, widget, context, x, y, 
                                         selection, targetType, time):
    """ 
    d'n'd - handler
    see get_show_from_urls for details
    """

    importer = GnomeShowImporter()
    shows= importer.get_show_from_urls(selection.data)
    for show in shows:
      self.model.shows[show.name] = show

    self.update_show_model()

    context.finish(True, True, time)

  def on_show_activated(self, path, u):    
    show = self.get_selected_show_name()
    successor = self.model.get((show,)).successor

    if not successor:
      log.info("no more episodes available!")
      return

    self.play((show,) + successor)

  def on_show_selected(self, path):
    """
    show icon selected -> generate the treeview, treeview-model
    """
    episodeModel = self.treeviewEpisodes.get_model()
    episodeModel.clear()

    show_name = self.get_selected_show_name()
    if not show_name:
      return

    sid = 0
    for season in self.model.get((show_name,)).seasons:
      season_iter = episodeModel.append(None, 
                                        (season.name,
                                         0, 
                                         self.BGCOLOR_SEASON, ''))
      
      eid = 0
      for episode in season.episodes:
        episode_iter = episodeModel.append(season_iter, 
                                           (episode.name, 
                                            episode.play_count, 
                                            '', episode.uri))

        self.update_tree_row((show_name, sid, eid))
        eid += 1

      sid += 1

    currentSeason, _ = self.model.get((show_name,)).successor

    self.treeviewEpisodes.expand_row((currentSeason,), False)


  def update_tree_row(self, path):
    """
    set background, ... for the given treeview item according to its state
    """

    # this may happen when no successor is found, 
    # e.g. when the series has no more episodes
    if not path:
      return

    episodeModel = self.treeviewEpisodes.get_model()

    def set_bgcolor(path,color):
      episodeModel[path][self.TREECOL_BGCOLOR] = color
    def set_text(path,text):
      pass
    def set_playcount(path,pc):
      episodeModel[path][self.TREECOL_PLAYCOUNT] = pc

    if len(path) == 2:
      " it's a season header "
      set_bgcolor(path[1:],self.BGCOLOR_SEASON)
      set_playcount(path[1:], sum ([e.play_count for e in self.model.get(path).episodes]))
    else:
      " it's an episode "

      episode = self.model.get(path) 
      if self.model.get((path[0],)).successor == path[1:]:
        color = self.BGCOLOR_SUCCESSOR
      elif episode.play_count >0:
        color = self.BGCOLOR_WATCHED 
      else:
        color = self.BGCOLOR_UNWATCHED

      set_playcount(path[1:], episode.play_count)
      set_bgcolor(path[1:], color)


  def on_quit(self, _):
    """
    a good chance to save the model
    """
    save(self.model)
    gtk.main_quit()


  def setup_treeview(self):

    c1 = gtk.TreeViewColumn('Show', 
                                gtk.CellRendererText(), 
                                text=self.TREECOL_TEXT, 
                                background=self.TREECOL_BGCOLOR)
    
    c2 = gtk.TreeViewColumn('Times watched', 
                                gtk.CellRendererText(), 
                                text=self.TREECOL_PLAYCOUNT, 
                                background=self.TREECOL_BGCOLOR)

    self.treeviewEpisodes.append_column(c1)
    self.treeviewEpisodes.append_column(c2)



  def on_actionAbout_activate(self, _):
    dlg = DialogBase('dialogAbout')
    dlg.run()
    dlg.destroy()


if __name__ == "__main__":
  app = JunqerApp()
  gtk.main()

