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
import urllib.error
import email.utils
import csv

CACHE_DIR = "cache"
DATA_DIR = "data"
OUT_DIR = "output"


def set_current_module(name):
    '''Set the currently executing module name to name.'''
    global CURRENT_MODULE
    if name:
        CURRENT_MODULE = name
    else:
        del CURRENT_MODULE

class module_context:

    '''Context manager to set the currently executing module.'''

    def __init__(self, name):
        self.name = name

    def __enter__(self):
        set_current_module(self.name)

    def __exit__(self, exc_type, exc_value, traceback):
        set_current_module(None)


def is_url(name):
    '''Return True if name appears to be a URL.'''
    return name.startswith('http://') or name.startswith('https://')

def get_filename(name):
    '''Return the filename associated to name (a data file or URL).'''
    global CURRENT_MODULE
    if is_url(name):
        return os.path.join(CACHE_DIR, CURRENT_MODULE,
                            urllib.parse.quote(name, safe=''))
    else:
        return os.path.join(DATA_DIR, CURRENT_MODULE, name)

def urlopen_cache(url, binary=True):
    '''Download url, if not yet in cache, and return a file object.'''
    cname = get_filename(url)
    if not os.path.exists(cname):
        logging.debug("Downloading %s.", url)
        response = urllib.request.urlopen(url)
        os.makedirs(os.path.dirname(cname), exist_ok=True)
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
        if is_url(name):
            logging.debug("Fetching headers of %s.", name)
            response = urllib.request.urlopen(urllib.request.Request(name, method='HEAD'))
            if 'Last-Modified' in response.headers:
                mtime = response.headers['Last-Modified']
                os.makedirs(os.path.dirname(filename), exist_ok=True)
                with open(filename, 'w') as f:
                    f.write(mtime)
            else:
                return None
        else:
            return None
    with open(filename, 'r') as f:
        return email.utils.parsedate_to_datetime(f.read().strip())

def is_alive(name):
    '''Return True if the data file name exists or the url name is alive.'''
    filename = get_filename(name)
    if is_url(name):
        if os.path.exists(filename + "=notfound"):
            return False
        if os.path.exists(filename) or \
           os.path.exists(filename + "=found") or \
           os.path.exists(filename + "=modified"):
            return True
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        try:
            get_modified(name)
            open(filename + "=found", 'w').close()
            return True
        except urllib.error.HTTPError as e:
            if e.code in {404, 403, 503}:
                open(filename + "=notfound", 'w').close()
                return False
            else:
                raise e
    else:
        return os.path.exists(filename)

def read_csv(name):
    '''Read a CSV file. The first row contains the column names. Yield the data
    rows as dictionaries with the column names as keys.'''
    with open_data(name, binary=False) as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            row.extend([""] * (len(header) - len(row)))
            yield {name:row[i] for i, name in enumerate(header)}
