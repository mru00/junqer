# persitance manager for junqer
# mru, 2011-01


import pickle, os
from model import *
import logging

log = logging.getLogger("persistance")
log.setLevel(logging.DEBUG)

CURRENT_VERSION=1
DATADIR=os.path.expanduser("~/.junqer/")
SAVEFILENAME=os.path.join(DATADIR, 'database')

try:
  os.mkdir(DATADIR)
except OSError, e:
  # errno == 17: file exists
  if e.errno != 17:
    log.info(e)
    raise

def load():
    """
    loads the model and returns it
    """
    try:
        version,model = pickle.load(open(SAVEFILENAME, 'rb'))
        if version != CURRENT_VERSION:
            log.error("file saved with version %d, version %d needed" %(version, CURRENT_VERSION))

            # TODO: backward-compatibe loading should be implemented here
            return Model()

        else:
          log.debug("loaded model")
    except:
      log.error("failed to load data!")
      return Model()

    return model

def save(model):
    """
    saves the model
    """
    tmp = ( CURRENT_VERSION, model )
    try:
      pickle.dump(tmp, open(SAVEFILENAME, 'wb'))
      log.debug("saved data")
    except:
      log.error("failed to save data to %s", SAVEFILENAME)

