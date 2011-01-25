#!/usr/bin/env python

# junqer: watching series like a pro!
# mru, 2011-01

import pygtk, gtk, gio
pygtk.require("2.0")


from mplayer import Mplayer
from showimporter import GnomeShowImporter
from model import *
from suspend import *
from persistance import *

class Player(object):
  pass

class MPlayer(Player):
  pass

  

class JunqerApp(object):       

  BGCOLOR_UNWATCHED="white"
  BGCOLOR_WATCHED="gray"
  BGCOLOR_SEASON="lightyellow"
  BGCOLOR_SUCCESSOR="green"
  TREECOL_BGCOLOR=3
  TREECOL_PLAYCOUNT=2
  TREECOL_TEXT=0

  def __init__(self):
    """
    setup everything
    """


    builder = gtk.Builder()
    builder.add_from_file("junqer.glade")

    builder.connect_signals({
      "on_window_destroy" : self.on_quit,
      "on_actionAbout_activate": self.on_actionAbout_activate,
      "on_actionSave_activate": self.on_actionSave_activate,
      "on_actionQuit_activate": self.on_quit,
      "on_iconviewShow_item_activated": self.on_show_activated, 
      "on_iconviewShow_selection_changed": self.on_show_selected,
      "on_iconviewShow_drag_data_received": self.on_iconviewShow_drag_data_received,
      "on_treeviewEpisodes_row_activated": self.on_treeviewEpisodes_row_activated})

    self.window = builder.get_object("main_window")
    self.treeviewEpisodes = builder.get_object("treeviewEpisodes")
    self.iconviewShow = builder.get_object("iconviewShow")
    self.aboutBox = builder.get_object("aboutdialog1")

    self.player = Mplayer()
    self.player.connect("playback_stopped", self.on_playback_stopped)
    
    self.currentShow = ''

    self.model = load()

    self.playmore = gtk.Adjustment(value=0, lower=-1, upper=100, step_incr=1)

    builder.get_object("spinbuttonPlayMore").set_adjustment(self.playmore)
    
    self.window.connect("destroy", self.on_quit)

    TARGET_TYPE_TEXT=80
    targets = [ ("text/uri-list", 0, TARGET_TYPE_TEXT )]

    self.window.show()
    self.setup_treeview()
    self.setup_showview()

    self.iconviewShow.enable_model_drag_dest(targets, 
        gtk.gdk.ACTION_LINK)
    self.update_show_model()

  def suspend(self):
    """
    send computer to sleep
    """

    get_suspender().suspend()


  def on_playback_stopped(self, player):
    """
    called from the player when the file is finished playing
    """

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
      print "no more episodes available!"
      return

    self.play((self.currentShow,) + successor)

  def play(self, path):
    """
    play the given file
    """


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

    print
    print "playing file", f.get_path()

    self.player.close()
    self.player.play(f.get_path())



  def update_show_model(self):
    """
    updates the icon view for new data in the internal model
    """

    showModel = self.iconviewShow.get_model()
    showModel.clear()

    pixbuf = self.iconviewShow.render_icon(gtk.STOCK_NEW, 
                                           size=gtk.ICON_SIZE_BUTTON, 
                                           detail=None)

    for name in self.model.shows:
      showModel.append( (name, pixbuf)) 


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
    print show
    successor = self.model.get((show,)).successor

    if not successor:
      print "no more episodes available!"
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
                                         '', 
                                         self.BGCOLOR_SEASON))
      
      eid = 0
      for episode in season.episodes:
        episode_iter = episodeModel.append(season_iter, 
                                           (episode.name, 
                                            episode.play_count, 
                                            episode.uri, ''))

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

    model = gtk.TreeStore(str, int, str, str)
    self.treeviewEpisodes.set_model(model)

    column = gtk.TreeViewColumn('Show', 
                                gtk.CellRendererText(), 
                                text=self.TREECOL_TEXT, 
                                background=self.TREECOL_BGCOLOR)
    self.treeviewEpisodes.append_column(column)
    
    column = gtk.TreeViewColumn('Times watched', 
                                gtk.CellRendererText(), 
                                text=self.TREECOL_PLAYCOUNT, 
                                background=self.TREECOL_BGCOLOR)

    self.treeviewEpisodes.append_column(column)


  def setup_showview(self):
    model = gtk.ListStore(str, gtk.gdk.Pixbuf)

    self.iconviewShow.set_model(model)
    self.iconviewShow.set_text_column(0)
    self.iconviewShow.set_pixbuf_column(1)
    self.iconviewShow.set_reorderable(True)

  def on_actionAbout_activate(self, _):
    self.aboutBox.run()
    self.aboutBox.destroy()


if __name__ == "__main__":
  app = JunqerApp()
  gtk.main()

