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

class Episode:
  def __init__(self):
    self.name = ''
    self.path = ''
    self.num_played = 0

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
    print "model constructor"

class Player(object):
  pass

class MPlayer(Player):
  pass

class JunqerApp(object):       

  SAVEFILENAME='/home/mru/.junqer.dat'
  def __init__(self):
    builder = gtk.Builder()
    builder.add_from_file("mainwin1.glade")

    builder.connect_signals({
      "on_window_destroy" : self.on_quit,
      "on_actionAbout_activate": self.on_actionAbout_activate,
      "on_actionQuit_activate": self.on_quit,
      "on_iconviewShow_item_activated": self.on_show_activated, 
      "on_iconviewShow_selection_changed": self.on_show_selected,
      "on_iconviewShow_drag_data_received": self.on_iconviewShow_drag_data_received,
      "on_treeviewEpisodes_row_activated": self.on_treeviewEpisodes_row_activated})

    self.window = builder.get_object("window1")
    self.treeviewEpisodes = builder.get_object("treeviewEpisodes")
    self.iconviewShow = builder.get_object("iconviewShow")
    self.aboutBox = builder.get_object("aboutdialog1")

    try:
      self.model = pickle.load(open(self.SAVEFILENAME, 'rb'))
    except:
      print "failed to load data!"
      self.model = Model()



    self.window.connect("destroy", self.on_quit)

    TARGET_TYPE_TEXT=80
    targets = [ ("text/uri-list", 0, TARGET_TYPE_TEXT )]

    self.window.show()
    self.setup_treeview()
    self.setup_showview()

    self.iconviewShow.enable_model_drag_dest(targets, gtk.gdk.ACTION_LINK)
    self.update_show_model()

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
          episode.path = episode_file.get_uri()
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
    if len(path) == 2:
      selection = episodeModel[path]
      print "actived:", selection, 
    print "activaed!"



  def on_iconviewShow_drag_data_received(self, widget, context, x, y, selection, targetType, time):

    self.get_show_from_urls(selection.data)
    self.update_show_model()

    context.finish(True, True, time)

  def on_show_activated(self, path, u):
    print "show activated", path, u

  def on_show_selected(self, path):
    print "show selected", path
    episodeModel = self.treeviewEpisodes.get_model()
    episodeModel.clear()

    showModel = self.iconviewShow.get_model()

    selection = self.iconviewShow.get_selected_items()
    assert ( len(selection) < 2 )
    if len(selection) != 1:
      return
    show_name = showModel[selection[0]][0]

    for season in self.model.shows[show_name].seasons:
      season_iter = episodeModel.append(None, (season.name,0))

      for episode in season.episodes:
        episodeModel.append(season_iter, (episode.name,0))



  def on_quit(self, _):
    try:
      pickle.dump(self.model, open(self.SAVEFILENAME, 'wb'))
    except:
      print "failed to save"
    gtk.main_quit()


  def setup_treeview(self):

    model = gtk.TreeStore(str, int)
    self.treeviewEpisodes.set_model(model)

    renderer = gtk.CellRendererText()
    column = gtk.TreeViewColumn('Show', renderer, text=0)
    self.treeviewEpisodes.append_column(column)
    
    renderer = gtk.CellRendererText()
    column = gtk.TreeViewColumn('Times watched', renderer, text=1)
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

