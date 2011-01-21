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


shows = [ 'family guy', 'simpsons' ]

class TutorialApp(object):       

  def __init__(self):
    builder = gtk.Builder()
    builder.add_from_file("mainwin1.glade")

    builder.connect_signals({ "on_window_destroy" : gtk.main_quit })

    self.window = builder.get_object("window1")
    self.tree = builder.get_object("treeview1")

    builder.get_object("actionQuit").connect("activate", self.on_quit);

    self.window.show()
    self.setup_treeview()

  def on_quit(self, o):
    gtk.main_quit()

  def setup_treeview(self):
    treeView = self.tree
    renderer = gtk.CellRendererText()
    treeView.insert_column_with_attributes(-1, 'Editable String', renderer, text=0)

    model = gtk.TreeStore(str, int, bool)

    iter = model.append(None)
    model.set_value(iter, 0, 'foo')
    model.set_value(iter, 1, 34)
    model.set_value(iter, 2, True)

    self.tree.set_model(model)
    renderer = gtk.CellRendererText()
    column = gtk.TreeViewColumn('column 1', renderer, text=0, editable=2)
    treeView.append_column(column)
    
    renderer = gtk.CellRendererText()
    column = gtk.TreeViewColumn('column 2', renderer, text=1, editable=2)
    treeView.append_column(column)


if __name__ == "__main__":
  app = TutorialApp()
  gtk.main()

