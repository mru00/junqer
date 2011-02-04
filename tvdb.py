# junqer: watching series like a pro!
# mru, 2011-01

from xml.dom import minidom
from urllib import urlopen,quote

import BeautifulSoup as bs
import logging

log = logging.getLogger("tvdb")

tvdb_mirror = ""

tvdb_key = "BFE6162BAD99831B"

def getText(nodelist):
  rc = []
  for node in nodelist:
    if node.nodeType == node.TEXT_NODE:
      rc.append(node.data)
  return ''.join(rc)




def dump_file(f, name = ""):
  print "FILE---------------- %s" % name
  for l in f.readlines():
    print l,
  print "--------------------"

def dump_url(url):

  print "URL----------------- %s" % url
  for l in urlopen(url).readlines():
    print l,
  print "--------------------"

def soup(url):
  return bs.BeautifulStoneSoup(urlopen(url))

get_tag_childs = lambda soup: filter(lambda a:type(a)!=bs.NavigableString, soup)


def get_mirrors():
  # TODO: implement real mirror fetching
  mi = soup("http://www.thetvdb.com/api/%s/mirrors.xml" % tvdb_key)
  print mi
  for child in get_tag_childs(mi.mirrors):
    print child
  tvdb_mirror = "http://thetvdb.com"
  return (tvdb_mirror, tvdb_mirror, tvdb_mirror)


def get_current_server_time():
  xml = soup("http://www.thetvdb.com/api/Updates.php?type=none")
  return xml.items.time.string
  


m_xml, m_banner, m_zip = get_mirrors()

exit (0)
previous = get_current_server_time()


def find_series(name):
  q = quote(name)
  return soup("http://www.thetvdb.com/api/GetSeries.php?seriesname=%s" % q)

def get_series(id):
  return soup("%s/api/%s/series/%s/all" %(m_zip,tvdb_key,id))

def list_series(soup):
  for series in filter(lambda a:type(a)!=bs.NavigableString, soup.data):
    print series.seriesname.string

some = find_series("a")
list_series(some)
exit(0)


sopranos = find_series("the sopranos")
if sopranos.data.series:
  print sopranos.data.series.seriesname.string
else:
  print "series not found"


series = get_series(sopranos.data.series.seriesid.string)
print series.prettify()
