# persitance manager for junqer

import pickle
from model import *


CURRENT_VERSION=1
SAVEFILENAME='/home/mru/.junqer.dat'


def load():
    """
    loads the model and returns it
    """
    try:
        version,model = pickle.load(open(SAVEFILENAME, 'rb'))
        if version != CURRENT_VERSION:
            print "file saved with version %d, version %d needed" %(version, CURRENT_VERSION)

            # TODO: backward-compatibe loading should be implemented here
            return Model()

    except:
      print "failed to load data!"
      return Model()

    return model

def save(model):
    """
    saves the model
    """
    tmp = ( CURRENT_VERSION, model )
    pickle.dump(tmp, open(SAVEFILENAME, 'wb'))
