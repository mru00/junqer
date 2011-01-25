# model classes for junqer
# mru, 2011-01

class Episode:
  def __init__(self):
    self.name = ''
    self.uri = ''
    self.play_count = 0

class Season:
  def __init__(self):
    self.number = 0
    self.episodes = []

class Show:
  def __init__(self):
    self.name = ''
    self.path = ''
    self.seasons = []
    self.successor = (0,0)
  def get(self,path):
    if len(path) == 1:
      return self.seasons[path[0]]
    
    return self.seasons[path[0]].episodes[path[1]]


class Model(object):
  def __init__(self):
    self.shows = {}
    self.current_show = ''
  def get(self, path):
    if len(path)>1:
      return self.shows[path[0]].get(path[1:])
    else:
      return self.shows[path[0]]
