#!/usr/bin/env python

# First run tutorial.glade through gtk-builder-convert with this command:
# gtk-builder-convert tutorial.glade tutorial.xml
# Then save this file as tutorial.py and make it executable using this command:
# chmod a+x tutorial.py
# And execute it:
# ./tutorial.py

import pygtk
pygtk.require("2.0")
import gtk
import os
import gio
import pickle
from mplayer import Mplayer


class Episode:
  def __init__(self):
    self.name = ''
    self.uri = ''
    self.play_count = 0

class Season:
  def __init__(self):
    self.number = 0
    self.episodes = []
    self.current_episode = 0

class Show:
  def __init__(self):
    self.name = ''
    self.path = ''
    self.seasons = []
    self.current_season = 0


class Model(object):
  def __init__(self):
    self.shows = {}
    self.current_show = ''
    print "model constructor"

class Player(object):
  pass

class MPlayer(Player):
  pass

class JunqerApp(object):       

  SAVEFILENAME='/home/mru/.junqer.dat'
  BGCOLOR_UNWATCHED="white"
  BGCOLOR_WATCHED="gray"
  BGCOLOR_SEASON="lightyellow"

  def __init__(self):
    builder = gtk.Builder()
    builder.add_from_file("junqer.glade")

    builder.connect_signals({
      "on_window_destroy" : self.on_quit,
      "on_actionAbout_activate": self.on_actionAbout_activate,
      "on_actionQuit_activate": self.on_quit,
      "on_iconviewShow_item_activated": self.on_show_activated, 
      "on_spinbuttonPlayMore_value_changed": self.on_spinbuttonPlayMore_value_changed,
      "on_iconviewShow_selection_changed": self.on_show_selected,
      "on_iconviewShow_drag_data_received": self.on_iconviewShow_drag_data_received,
      "on_treeviewEpisodes_row_activated": self.on_treeviewEpisodes_row_activated})

    self.window = builder.get_object("window1")
    self.treeviewEpisodes = builder.get_object("treeviewEpisodes")
    self.iconviewShow = builder.get_object("iconviewShow")
    self.aboutBox = builder.get_object("aboutdialog1")

    self.player = Mplayer()
    self.player.connect("playback_stopped", self.on_playback_stopped)
    
    self.currentShow = ''
    self.currentSeason = 0
    self.currentEpisode = 0

    try:
      self.model = pickle.load(open(self.SAVEFILENAME, 'rb'))
    except:
      print "failed to load data!"
      self.model = Model()


    self.playmore = gtk.Adjustment(value=0, lower=-1, upper=100, step_incr=1)

    builder.get_object("spinbuttonPlayMore").set_adjustment(self.playmore)
    
    self.playmore.connect('changed', self.on_spinbuttonPlayMore_value_changed)

    self.window.connect("destroy", self.on_quit)

    TARGET_TYPE_TEXT=80
    targets = [ ("text/uri-list", 0, TARGET_TYPE_TEXT )]

    self.window.show()
    self.setup_treeview()
    self.setup_showview()

    self.iconviewShow.enable_model_drag_dest(targets, gtk.gdk.ACTION_LINK)
    self.update_show_model()

  def on_playback_stopped(self, player):
    value = int(self.playmore.get_value()) 
    if value > 0 or value == -1:
      self.advance()

    if value > 0:
      self.playmore.set_value(value -1)


  def successor(self, show_name, season_id, episode_id):


    show = self.model.shows[show_name]
    season = show.seasons[season_id]
    
    episodeidx = self.currentEpisode + 1

    if episodeidx < len(season.episodes):
      return season_id, episodeidx
    seasonidx = season_id + 1
    if seasonidx < len(show.seasons):
      return seasonidx, 0
    return None


  def advance(self):
    successor = self.successor(self.currentShow, self.currentSeasons, self.currentEpisode)

    if not successor:
      print "no more episodes available!"
      return

    nextSeason, nextEpisode = successor
    self.play(self.currentShow, nextSeason, nextEpisode)

  def play(self, show_name, season_id, episode_id):
    self.currentShow = show_name
    self.currentSeason = season_id
    self.currentEpisode = episode_id


    mshow = self.model.shows[show_name]
    mshow.current_season = season_id
    mseason = mshow.seasons[season_id]
    mseason.current_episode = episode_id
    mepisode = mseason.episodes[episode_id]
    mepisode.play_count += 1


    if self.get_selected_show_name() == show_name:
      episodeModel = self.treeviewEpisodes.get_model()
      episodeModel[(season_id,episode_id) ][1] = mepisode.play_count
      episodeModel[(season_id,)][1] = sum( [ e.play_count for e in mseason.episodes] )
      episodeModel[(season_id,episode_id) ][3] = self.BGCOLOR_WATCHED

    f = gio.File(mepisode.uri) 

    print
    print "playing file", f.get_path()

    self.player.close()
    self.player.play(f.get_path())

  def get_show_from_urls(self, urls):

    shows = []
    for show_dir in filter(lambda s: len(s)>0, map(lambda s: s.rstrip() ,urls.split('\n'))):

      show_dir = gio.File(show_dir)

      show = Show()
      show.name = os.path.split(show_dir.get_path())[-1]
      show.name.replace('-', ' ')
      show.path = show_dir.get_uri()
      show.seasons = []


      is_dir = lambda e: e.get_file_type() == gio.FILE_TYPE_DIRECTORY
      is_file = lambda e: e.get_file_type() == gio.FILE_TYPE_REGULAR

      show_infos = show_dir.enumerate_children('standard::name,standard::type')
      for season_info in filter(is_dir, show_infos):

        season_dir = show_dir.get_child(season_info.get_name())

        season = Season()
        season.name = os.path.split(season_dir.get_path())[-1]
        season.path = season_dir.get_uri()
        season.episodes = []

        episode_infos = season_dir.enumerate_children('standard::name,standard::type')
        for episode_info in filter(is_file, episode_infos):

          episode_file = season_dir.get_child(episode_info.get_name())
          episode = Episode()
          episode.name = os.path.split(episode_file.get_path())[-1]
          episode.uri = episode_file.get_uri()
          season.episodes.append(episode)

        season.episodes.sort(key=lambda e: e.name)
        show.seasons.append(season)
          
      show.seasons.sort(key=lambda s: s.name)
      shows.append(show)

      self.model.shows[show.name] = show

  def dump_model(self, model):

    for show in model.shows:
      print "[show]", show.name
      for season in show.seasons:
        print "  [season]", season.name
        for episode in season.episodes:
          print "    [episode]", episode.name


  def update_show_model(self):

    showModel = self.iconviewShow.get_model()
    showModel.clear()

    pixbuf = self.iconviewShow.render_icon(gtk.STOCK_NEW, size=gtk.ICON_SIZE_BUTTON, detail=None)

    for name in self.model.shows:
      showModel.append( (name, pixbuf)) 


  def on_treeviewEpisodes_row_activated(self, treeview, path, view_column):

    episodeModel = self.treeviewEpisodes.get_model()
    if len(path) != 2:
      return

    show = self.get_selected_show_name()
    self.play(show, path[0], path[1])

  def get_selected_show_name(self):

    showSelection = self.iconviewShow.get_selected_items()[0]

    showModel = self.iconviewShow.get_model()
    show = showModel[showSelection][0]

    return show
       

  def on_spinbuttonPlayMore_value_changed(self, adjust):
    pass

  def on_iconviewShow_drag_data_received(self, widget, context, x, y, selection, targetType, time):

    self.get_show_from_urls(selection.data)
    self.update_show_model()

    context.finish(True, True, time)

  def on_show_activated(self, path, u):
    pass

  def on_show_selected(self, path):
    episodeModel = self.treeviewEpisodes.get_model()
    episodeModel.clear()

    show_name = self.get_selected_show_name()

    for season in self.model.shows[show_name].seasons:
      season_iter = episodeModel.append(None, (season.name,0, '', self.BGCOLOR_SEASON))

      n = 0
      for episode in season.episodes:
        if episode.play_count >0:
          color = self.BGCOLOR_WATCHED 
        else:
          color = self.BGCOLOR_UNWATCHED

        episodeModel.append(season_iter, (episode.name, episode.play_count, episode.uri, color))
        n += episode.play_count

      episodeModel[season_iter][1] = n

    self.treeviewEpisodes.expand_row((self.model.shows[show_name].current_season,), False)



  def on_quit(self, _):
    try:
      pickle.dump(self.model, open(self.SAVEFILENAME, 'wb'))
    except:
      print "failed to save"
    gtk.main_quit()


  def setup_treeview(self):

    model = gtk.TreeStore(str, int, str, str)
    self.treeviewEpisodes.set_model(model)

    renderer = gtk.CellRendererText()
    column = gtk.TreeViewColumn('Show', renderer, text=0, background=3)
    self.treeviewEpisodes.append_column(column)
    
    renderer = gtk.CellRendererText()
    column = gtk.TreeViewColumn('Times watched', renderer, text=1, background=3)
    self.treeviewEpisodes.append_column(column)


  def setup_showview(self):
    model = gtk.ListStore(str, gtk.gdk.Pixbuf)

    pixbuf = self.iconviewShow.render_icon(gtk.STOCK_NEW, size=gtk.ICON_SIZE_BUTTON, detail=None)

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

