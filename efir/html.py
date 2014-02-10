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

from urllib.parse import urljoin

class HTMLPage(bs4.BeautifulSoup):

    '''A specialized BeautifulSoup.'''

    def __init__(self, module, url):
        '''Load a web page located at url.'''
        bs4.BeautifulSoup.__init__(self, open_data(module, url, binary=True))


def get_real_children(tag):
    '''Yield the children of tag, omitting spaces.'''
    for child in tag.children:
        if isinstance(child, str):
            child = child.strip()
            if child:
                yield child
        else:
            yield child
