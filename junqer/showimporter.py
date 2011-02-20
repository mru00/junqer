# importer for junqer
# mru 2011-01

import gio
import os
from model import *
import logging

log = logging.getLogger("importer")


class ShowImporter(object):
  def get_show_from_urls(self, urls):
    pass

class GnomeShowImporter(ShowImporter):
  def get_show_from_urls(self, urls):
    """
    gnome delivers a newline-seperated list of uri's for drag-and-drop data.
    this function reads the directory contents of the dragged folders and adds
    them to the model.
    """

    shows = []
    for show_dir in filter(lambda s: len(s)>0, map(lambda s: s.rstrip() ,urls.split('\n'))):

      try:

        def get_last_path_item(path):
          return os.path.split(path.get_path())[-1]
        show_dir = gio.File(show_dir)
  
        show = Show()
        show.name = get_last_path_item(show_dir)
        show.name.replace('-', ' ')
        show.path = show_dir.get_uri()
        show.seasons = []
        show.meta['name'] = show.name
  
        is_dir = lambda e: e.get_file_type() == gio.FILE_TYPE_DIRECTORY
        is_file = lambda e: e.get_file_type() == gio.FILE_TYPE_REGULAR
        ENUM_DESC = 'standard::name,standard::type'
  
        
        show_infos = show_dir.enumerate_children(ENUM_DESC)
        for season_info in filter(is_dir, show_infos):
  
          season_dir = show_dir.get_child(season_info.get_name())
  
          season = Season()
          season.name = get_last_path_item(season_dir)
          season.path = season_dir.get_uri()
          season.episodes = []
  
          episode_infos = season_dir.enumerate_children(ENUM_DESC)
          for episode_info in filter(is_file, episode_infos):
  
            episode_file = season_dir.get_child(episode_info.get_name())
            episode = Episode()
            episode.name = get_last_path_item(episode_file)
            episode.uri = episode_file.get_uri()
            season.episodes.append(episode)
  
          season.episodes.sort(key=lambda e: e.name)
          show.seasons.append(season)
            
        show.seasons.sort(key=lambda s: s.name)
        shows.append(show)
      except Exception, e:
        log.error("Error scanning series: %s", str(e))

    return shows
