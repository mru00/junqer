# junqer: watching series like a pro!
# mru, 2011-01

from xml.dom import minidom
from urllib import urlopen,quote

from BeautifulSoup import BeautifulSoup
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

def get_mirrors():
  # TODO: implement real mirror fetching
  mirrors_xml = urlopen("http://www.thetvdb.com/api/%s/mirrors.xml" % tvdb_key)
  tvdb_mirror = "http://thetvdb.com"
  return (tvdb_mirror, tvdb_mirror, tvdb_mirror)


def get_current_server_time():
  soup = BeautifulSoup(urlopen("http://www.thetvdb.com/api/Updates.php?type=none"))
  return soup.items.time.string
  

m_xml, m_banner, m_zip = get_mirrors()

previous = get_current_server_time()


def find_series(name):
  q = quote(name)
  return BeautifulSoup(urlopen("http://www.thetvdb.com/api/GetSeries.php?seriesname=%s" % q))



sopranos = find_series("the sopranos")
if sopranos.data.series:
  print sopranos.data.series.seriesname.string
else:
  print "series not found"

id = sopranos.data.series.seriesid.string

series = BeautifulSoup(urlopen("%s/api/%s/series/%s/all" %(m_zip,tvdb_key,id)))
print series.prettify()
