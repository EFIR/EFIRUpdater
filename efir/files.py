# Cache module
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

import logging
import os.path
import shutil
import urllib.request
import urllib.parse
import time
import email.utils

CACHE_DIR = "cache"
DATA_DIR = "data"
OUT_DIR = "output"

def is_url(name):
    '''Return True if name appears to be a URL.'''
    return name.startswith('http://') or name.startswith('https://')

def get_filename(name):
    '''Return the filename associated to name (a data file or URL).'''
    if is_url(name):
        return os.path.join(CACHE_DIR, urllib.parse.quote(name, safe=''))
    else:
        return os.path.join(DATA_DIR, name)

def urlopen_cache(url, binary=True):
    '''Download url, if not yet in cache, and return a file object.'''
    cname = get_filename(url)
    if not os.path.exists(cname):
        logging.debug("Downloading %s.", url)
        response = urllib.request.urlopen(url)
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cname, 'wb') as f:
            shutil.copyfileobj(response, f)
        if 'Last-Modified' in response.headers:
            mtime = response.headers['Last-Modified']
            with open(cname + '=modified', 'w') as f:
                f.write(mtime)
    logging.debug("Opening %s.", cname)
    return open(cname, 'rb' if binary else 'r')

def open_data(name, binary=True):
    '''Open a data file or URL (if it begins with http).'''
    if is_url(name):
        return urlopen_cache(name, binary)
    else:
        filename = get_filename(name)
        logging.debug("Opening %s.", filename)
        return open(filename, 'rb' if binary else 'r')

def get_modified(name):
    '''Return a datetime.datetime object with the last modification date of
    name (a data file or URL) or None if unknown.'''
    filename = get_filename(name) + '=modified'
    if not os.path.exists(filename):
        return None
    with open(filename, 'r') as f:
        return email.utils.parsedate_to_datetime(f.read().strip())
