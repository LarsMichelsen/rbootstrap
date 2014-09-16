import urllib2
import re
import gzip
from StringIO import StringIO

def fetch(url):
    response = urllib2.urlopen(url)
    if url.endswith('.gz'):
        # Would be better to be able to stream this, but it is not possible with python 2
        fh = StringIO(response.read())
        return gzip.GzipFile(fileobj = fh)
    return response
