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
import re
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

    def get_section_text(self, title, stop=[]):
        '''Return the text under heading title.

        Arguments:
        title -- the text of the heading or a tag
        stop -- a list of heading texts that indicate a following section
        '''
        if not isinstance(title, bs4.element.PageElement):
            pattern = get_heading_pattern(title)
            for tag in self.find_all(text=pattern):
                result = self.get_section_text(tag, stop=stop)
                if result:
                    return result
            return None
        if isinstance(title, str):
            title = title.parent
        while title.name in {'span', 'b', 'i', 'font', 'a'}:
            if title.name == 'a' and 'href' in title.attrs:
                return None
            title = title.parent
        tag = get_next_real_sibling(title)
        tags = None
        titleclass = None
        if title.name == 'p':
            if 'class' not in title.attrs and tag.name == 'p':
                # <p>Abstract:</p>
                # <p>...</p>
                # <p>Status:</p>
                tags = tag.children
            elif 'class' in title.attrs and len(title['class']) == 1:
                # <p class="Titlepageinfo">Abstract:</p>
                # <p class="Abstract">...</p>
                # <p class="Abstract">...</p>
                # <p class="Titlepageinfo">Status:</p>
                titleclass = title['class'][0]
                if 'class' in tag.attrs and titleclass in tag['class']:
                    # <p class="MsoNormal">Abstract:</p>
                    # <p class="MsoNormal">...</p>
                    # <p class="MsoNormal">Status:</p>
                    titleclass = None
                    tags = tag.children
            else:
                return None
        elif title.name == 'div':
            if tag.name == 'div':
                # <div>Abstract:</div>
                # <div>...</div>
                tags = tag.children
            else:
                return None
        elif title.name == 'dt':
            if tag.name == 'dd':
                # <dt>Abstract:</dt>
                # <dd>...</dd>
                tags = tag.children
            else:
                return None
        elif is_heading(title):
            # <h2>Abstract</h2>
            # ...
            # <h2>Introduction</h2>
            pass
        else:
            return None
        if not tags:
            tags = gather_siblings(tag, stopclass=titleclass, stoptext=stop)
        return html_to_plain(tags)


def get_heading_pattern(title):
    '''Return the regular expression for matching the text corresponding to
    title.'''
    return re.compile(r"^\s*(?:\d[\d.]*\s)?\s*" + title + "\s*:?\s*$",
                      flags=re.I)


def get_next_real_sibling(tag):
    '''Return the next sibling of tag, omitting spaces.'''
    tag = tag.next_sibling
    while tag and ((isinstance(tag, str) and tag.strip() == "") or \
                   (isinstance(tag, bs4.element.Comment))):
        tag = tag.next_sibling
    return tag


def get_previous_real_sibling(tag):
    '''Return the previous sibling of tag, omitting spaces.'''
    tag = tag.previous_sibling
    while tag and ((isinstance(tag, str) and tag.strip() == "") or \
                   (isinstance(tag, bs4.element.Comment))):
        tag = tag.previous_sibling
    return tag


def is_heading(tag):
    '''Return True if tag is a heading.'''
    return isinstance(tag, bs4.element.Tag) and \
           tag.name in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}


def gather_siblings(tag, stopclass=None, stoptext=None):
    '''Yield tag and its siblings until a stop condition is met.

    Arguments:
    tag -- the first tag
    stopclass -- a class or list of classes
    stoptext -- a text or list of texts
    '''
    if not stopclass:
        stopclass = []
    elif isinstance(stopclass, str):
        stopclass = [stopclass]
    if not stoptext:
        stoptext = []
    elif isinstance(stoptext, str):
        stoptext = [get_heading_pattern(stoptext)]
    else:
        stoptext = [get_heading_pattern(text) for text in stoptext]
    while tag:
        if isinstance(tag, str):
            if any(exp.match(tag) for exp in stoptext):
                return
        else:
            if is_heading(tag):
                return
            if 'class' in tag.attrs and \
               any(cls in tag['class'] for cls in stopclass):
                return
            if any(exp.match(tag.text) for exp in stoptext):
                return
        yield tag
        tag = get_next_real_sibling(tag)


def clean_text(text, oneline=False):
    '''Clean text, removing spurious whitespaces.

    Arguments:
    text -- the text to clean
    oneline -- if True, remove all newlines
    '''
    text = text.strip().replace("\r\n", "\n")
    if oneline:
        text = re.sub(r"\s+", r" ", text)
    else:
        text = re.sub(r"[ \t\r\f\v]+", r" ", text)
        text = re.sub(r"\n{2,}", r"\n\n", text)
    text = re.sub(r"^ +| +$", r"", text, flags=re.M)
    return text


def html_to_plain(tags):
    '''Return the text contained in tags.'''
    if isinstance(tags, str) or isinstance(tags, bs4.element.Tag):
        tags = [tags]
    result = ""
    for tag in tags:
        if isinstance(tag, str):
            result += re.sub(r"\s", " ", tag)
        elif tag.name in {'p', 'div'}:
            result += "\n\n" + html_to_plain(tag.children) + "\n\n"
        elif tag.name == 'ul':
            result += "\n\n"
            for li in tag.find_all('li', recursive=False):
                result += "\n* " + html_to_plain(li.children)
            result += "\n\n"
        elif tag.name == 'ol':
            result += "\n\n"
            for i, li in enumerate(tag.find_all('li', recursive=False)):
                result += "\n" + str(i) + ". " + \
                          html_to_plain(li.children)
            result += "\n\n"
        elif tag.name == 'br':
            result += "\n"
        else:
            result += re.sub(r"\s", " ", tag.text)
    return clean_text(result)
