# suspender for junqer
# mru 2011-01

import dbus

class Suspender(object):
  def suspend(self):
      pass


class UbuntuSuspender(Suspender):
  def suspend(self):

    """
    send computer to sleep - ubuntu 10.10
    """

    bus = dbus.SystemBus()
    proxy = bus.get_object('org.freedesktop.UPower', '/org/freedesktop/UPower')
    proxy.Suspend(dbus_interface="org.freedesktop.UPower")


def get_suspender():
    """
    suspender factory
    --
    this would be the right place to decide which suspender is suitable
    for the current computer
    """

    # TODO: implement smart suspender choice bases on availabilty of methods
    return UbuntuSuspender()
