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

    def get_section_text(self, title):
        '''Return the text under heading title.'''
        if not isinstance(title, bs4.element.PageElement):
            pattern = re.compile(r"^\s*(?:\d[\d.]*\s)?\s*" + title + "\s*:?\s*$",
                                 flags=re.I)
            for tag in self.find_all(text=pattern):
                result = self.get_section_text(tag)
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
            tags = []
            while tag:
                if isinstance(tag, str):
                    tags.append(tag)
                elif is_heading(tag):
                    break
                elif titleclass and 'class' in tag.attrs and \
                     titleclass in tag['class']:
                    break
                else:
                    tags.append(tag)
                tag = get_next_real_sibling(tag)
        return html_to_plain(tags)


def get_real_children(tag):
    '''Yield the children of tag, omitting spaces.'''
    for child in tag.children:
        if isinstance(child, str):
            child = child.strip()
            if child:
                yield child
        else:
            yield child


def get_next_real_sibling(tag):
    '''Return the next sibling of tag, omitting spaces.'''
    tag = tag.next_sibling
    while tag and ((isinstance(tag, str) and tag.strip() == "") or \
                   (isinstance(tag, bs4.element.Comment))):
        tag = tag.next_sibling
    return tag


def is_heading(tag):
    '''Return True if tag is a heading.'''
    return isinstance(tag, bs4.element.Tag) and \
           tag.name in {'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}


def clean_text(text, foldnl=True):
    '''Clean text, removing spurious whitespaces.

    Arguments:
    foldnl -- whether to fold newlines
    '''
    text = text.strip().replace("\r\n", "\n")
    if foldnl:
        text = re.sub(r"\n(?!\n)", r" ", text)
        text = re.sub(r"\n+", r"\n\n", text)
    else:
        text = re.sub(r"\n{2,}", r"\n\n", text)
    text = re.sub(r"[ \t]+", r" ", text)
    text = re.sub(r"^ +| +$", r"", text, flags=re.M)
    return text


def html_to_plain(tags):
    '''Return the text contained in tags.'''
    if isinstance(tags, str) or isinstance(tags, bs4.element.Tag):
        tags = [tags]
    result = ""
    for tag in tags:
        if isinstance(tag, str):
            result += " " + clean_text(tag)
        elif tag.name == 'p':
            result += "\n\n" + html_to_plain(get_real_children(tag))
        elif tag.name == 'ul':
            result += "\n"
            for li in tag.find_all('li', recursive=False):
                result += "\n* " + html_to_plain(get_real_children(li))
        elif tag.name == 'ol':
            result += "\n"
            for i, li in enumerate(tag.find_all('li', recursive=False)):
                result += "\n" + str(i) + ". " + \
                          html_to_plain(get_real_children(li))
        elif tag.name == 'br':
            result += "\n"
        else:
            result += " " + clean_text(tag.text)
    return clean_text(result, foldnl=False)
