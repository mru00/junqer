# junqer: watching series like a pro!
# mru, 2011-01


# dialog programming model
#
# - each dialog is in its seperate .glade file
# - the name of the glade file matches the name of the dialog instance
#
#


import pygtk, gtk, gio
pygtk.require("2.0")
import gconf, gobject
import logging
import thetvdbapi
from persistance import DATADIR
import urllib2
import os

from junqerapp import tvdb_key

log = logging.getLogger("dialogs")

class DialogBase(object):
  """
  DialogBase: baseclass for dialogs.
  can be used stand-alone.


  implements indexed access to the glade resouces, e.g.:
  self['gladeObject'].show()
  """

  def __init__(self, gladepath):
    """
    gladepath: 
      - the name of the gladefile without path and without extension
      - the name of the toplevel dialog instance in the glade

    """

    builder = gtk.Builder()
    builder.add_from_file("glade/%s.glade" % gladepath)
    self.builder = builder
    self.dialog = builder.get_object(gladepath)
    self.run = self.dialog.run
    self.destroy = self.dialog.destroy


  def connect(self, signals):
    self.builder.connect_signals(signals)

  def __getitem__(self, index):
    o = self.builder.get_object(index)
    if not o:
      log.error("object %s not found", index)
    return o

  def run_busy(self, fun):
    """
    executes function 'fun', and shows busy mouse pointer while running
    TODO: add function parameter passing
    """

    win = self.dialog.window

    def idle_cb(gtk_window):
      try:
        fun()
      finally:
        win.set_cursor(None)

    watch = gtk.gdk.Cursor(gtk.gdk.WATCH)
    win.set_cursor(watch)
    gobject.idle_add(idle_cb, win)


class DialogSelectBanner(DialogBase):
  def __init__(self, bannerlist):
    DialogBase.__init__(self, 'dialogSelectBanner')
    self.connect({
      "on_dialogSelectBanner_response": self.on_dialogSelectBanner_response,
      "on_treeview1_cursor_changed": self.on_treeview1_cursor_changed
      })

    tv = self['treeview1']
    model = tv.get_model()

    c1 = gtk.TreeViewColumn('Banner', 
                                gtk.CellRendererPixbuf(), 
                                pixbuf=1)

    tv.append_column(c1)


    win = self.dialog.window
    def delayload(self, win):
      if len(bannerlist) == 0: return
      url,type = bannerlist.pop()

      log.info("loading image %s", url)
      resp = urllib2.urlopen(url)
      loader = gtk.gdk.PixbufLoader()
      loader.write(resp.read())
      loader.close()
      pb = loader.get_pixbuf()
      w = pb.get_width()
      h = pb.get_height()
      model.append((url, pb.scale_simple(200, 200*h/w, gtk.gdk.INTERP_BILINEAR)))

      # add idle again until all banners are loaded
      if self.keep_loading:
        gobject.idle_add(delayload, self, win)

    gobject.idle_add(delayload, self, win)

    self['buttonOk'].set_sensitive(False)
    self.fn = None
    self.keep_loading = True

  def on_dialogSelectBanner_response(self, w, response):

    print "response"

    if response == gtk.RESPONSE_OK:
      print "response ok"

      selection = self['treeview1'].get_selection()
      (m, _iter) = selection.get_selected()
      if not _iter: return

      url = m[_iter][0]
      fn = url.split('/')[-1]
      self.fn = os.path.join(DATADIR, fn)
      open(self.fn, "w").write(urllib2.urlopen(url).read())

    self.keep_loading = False
    
  def on_treeview1_cursor_changed(self, w):
    self['buttonOk'].set_sensitive(True)

class DialogSearchTvdb(DialogBase):
  """
  """
  def __init__(self, initial_title = ''):
    DialogBase.__init__(self, "dialogSearchTvdb")

    self.connect({
      "on_treeviewTvdbResults_cursor_changed": self.on_treeviewTvdbResults_cursor_changed,
      "on_actionSearchTvdb_activate": self.on_actionSearchTvdb_activate})

    t = self['treeviewTvdbResults']

    t.append_column(gtk.TreeViewColumn('Id', gtk.CellRendererText(), text=0))
    t.append_column(gtk.TreeViewColumn('Name', gtk.CellRendererText(), text=1))

    self.model = self['liststoreTvdbResults']

    self.tvdb = thetvdbapi.TheTVDB(tvdb_key)

    self['entrySearchTvdb'].set_text(initial_title)
    self['buttonOK'].set_sensitive(False)
    self.selection = None



  def on_treeviewTvdbResults_cursor_changed(self, w):
    self['buttonOK'].set_sensitive(True)
    selection = w.get_selection()
    (m, _iter) = selection.get_selected()
    if _iter:
      row = m[_iter]
      self.selection = (row[0], row[1])


  def on_actionSearchTvdb_activate(self, _):

    def action():
        self.model.clear()
  
        shows = self.tvdb.get_matching_shows(self['entrySearchTvdb'].get_text())
        for id, name in shows:
          print id, name, type(id), type(name)
          self.model.append( (id,name))

    self.run_busy(action)



class DialogEditShow(DialogBase):
  """
  """

  FIELDS = [ 'name', 'overview', 'network', 'first_aired', 'id' ]

  def __init__(self, meta={}):
    DialogBase.__init__(self, "dialogEditShow")
    self.connect({
      "on_actionSelectBanner_activate": self.on_actionSelectBanner_activate,
      "on_dialogEditShow_response": self.on_dialogEditShow_response,
      "on_actionDialogSearchTvdb_activate": self.on_actionDialogSearchTvdb_activate})

    self.tvdb = thetvdbapi.TheTVDB(tvdb_key)
    self.meta = meta
    
    for f in filter(lambda a: a in meta.keys(), self.FIELDS):
      e = self['entry_' + f]
      if e: e.set_text( str(meta[f]) )
    if 'banner' in meta:
      self['image1'].set_from_file(meta['banner'])


  def on_actionSelectBanner_activate(self, _):

    print "on button press!"

    bannerlist = self.tvdb.get_show_image_choices(self['entry_id'].get_text())
    dlg = DialogSelectBanner(bannerlist)
    try:
      if dlg.run() == gtk.RESPONSE_OK:
        if 'banner' not in self.meta or self.meta['banner'] != dlg.fn:
          self['image1'].set_from_file( dlg.fn )
          self.meta['banner'] = dlg.fn
    finally:
      dlg.destroy()



  def on_dialogEditShow_response(self, a, response):
    """
    when the dialog gets closed, copy the content from the edit-fields
    to self.meta
    """


    def get_text(e):
      if type(e) == gtk.TextBuffer:
        return e.get_text(e.get_start_iter(), e.get_end_iter())
      return e.get_text()

    if response == gtk.RESPONSE_OK:

      for f in self.FIELDS:
        self.meta[f] = get_text(self['entry_' + f])

  def on_actionDialogSearchTvdb_activate(self, _):

    dlg = DialogSearchTvdb()
    try:
      if dlg.run() == gtk.RESPONSE_OK and dlg.selection:
        id,name = dlg.selection
        show = self.tvdb.get_show(id)
        for f in self.FIELDS:
          value = getattr(show, f)
          self['entry_' + f].set_text( str(value) )
          self.meta[f] = value
    finally:
      dlg.destroy()





