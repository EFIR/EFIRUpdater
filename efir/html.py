# HTML scraping utilities
#
# Copyright 2014 PwC EU Services
#
# Licensed under the EUPL, Version 1.1 or - as soon they
# will be approved by the European Commission - subsequent
# versions of the EUPL (the "Licence");
# You may not use this work except in compliance with the
# Licence.
# You may obtain a copy of the Licence at:
# http://ec.europa.eu/idabc/eupl
#
# Unless required by applicable law or agreed to in
# writing, software distributed under the Licence is
# distributed on an "AS IS" basis,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
# express or implied.
# See the Licence for the specific language governing
# permissions and limitations under the Licence.

import bs4
from .files import *

from urllib.parse import urlparse, urljoin, unquote

class HTMLPage(bs4.BeautifulSoup):

    '''A specialized BeautifulSoup.'''

    def __init__(self, module, url):
        '''Load a web page located at url.'''
        self.url = url
        bs4.BeautifulSoup.__init__(self, open_data(module, url, binary=True))

    def get_child_links(self):
        '''Return a set of links that are descendants of this page.'''
        links = set()
        url = self.url
        if not url.endswith('/'):
            url += "/"
        parent = urlparse(url)
        for a in self.find_all('a'):
            url = urljoin(self.url, a['href'])
            child = urlparse(url)
            if child.scheme == parent.scheme and \
               child.netloc == parent.netloc and \
               child.path.startswith(parent.path) and \
               len(child.path) > len(parent.path):
                links.add(url)
        return links


def get_real_children(tag):
    '''Yield the children of tag, omitting spaces.'''
    for child in tag.children:
        if isinstance(child, str):
            child = child.strip()
            if child:
                yield child
        else:
            yield child
