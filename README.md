Junqer -- a new approach to massively junk series
=================================================

mru <mru@sisyphus.teil.cc>
2011-01



abstract
--------

Junqer is a simple python / pygtk application that targets a
series-junkie like myself.


uses
----

  * pygtk
  * glade
  * gio

limitations
-----------

  * currently only mplayer is available
  * almost everything is hardcoded
  * developed under/for? ubuntu 10.10
  * very messy code

TODO
----

  * player backends (gstreamer/totem/vlc)
    - currently gstreamer and mplayer in development
  * always on top
  * collapsed gui
  * gui upgrades 
  * icon design
  * smarter "successor" / currently playing markup
  * save time when an episode stopped -> restart/resume half-played episodes  
  * player configuration
  * play/pause/next/previous... actions
  * finish standby
  * some sort of testing / unit testing, whatever
  * make pychecker work correctly (lots of gtk-related errors)
  * implement updates on series (new episodes arrive, update model)
  * handle all types of error
    - file not found
    - player not found
    - player failed
  * develop a better model implementation
    - model versioning
  * save settings, gui size, player settings, ...
  * also load metadata from tvdb (episode release date, length!)
  * configurable key map

  * playmodes:
    - chronoscopic
    - random
    - play least watched

hf!
