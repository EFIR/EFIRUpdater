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

import os
import os.path
import logging
import importlib

from .files import *
from .model import *

class Processor:

    '''
    A Processor is a module living in the repositories package and containing a
    process() function returning the ADMS graph.

    '''

    def __init__(self, name):
        self.name = name

    def process(self, strict=False):
        logging.info("Processing repository %s.", self.name)
        with module_context(self.name):
            module = importlib.import_module('..repos.' + self.name, __name__)
            try:
                repo = module.process()
            except:
                logging.exception("Unable to process repository.")
                return
            logging.debug("Removing non top-level assets.")
            assets = repo.get_values('dataset')
            for asset in assets:
                for prop in ['related', 'included', 'last', 'next', 'prev',
                             'sample', 'translation']:
                    values = {value.uri if isinstance(value, Asset) and
                                           value not in assets
                                        else value
                              for value in asset.get_values(prop)}
                    setattr(asset, prop, values)
            if not strict:
                logging.debug("Cleaning and autocompleting repository.")
                repo.cleanup()
            logging.debug("Validating model.")
            if not isinstance(repo, Repository):
                logging.error("Result is not a Repository: %s.", repo)
                return
            repo.validate().log()
            logging.debug("Constructing graph")
            g = Graph(repo)
            filename = os.path.join(OUT_DIR, self.name + '.rdf')
            logging.debug("Serializing result to %s.", filename)
            try:
                os.makedirs(OUT_DIR, exist_ok=True)
                with open(filename, 'wb') as f:
                    g.serialize(f)
            except:
                logging.exception("Unable to serialize graph.")
                return
        assets = repo.get_values('dataset')
        distributions = set.union(*(a.get_values('distribution') for a in assets))
        licenses = set.union(*(d.get_values('license') for d in distributions))
        publishers = set.union(*(a.get_values('publisher') for a in assets)) | \
                     set.union(*(d.get_values('publisher') for d in distributions)) | \
                     repo.get_values('publisher')
        logging.info("Successfully processed %d assets, %d distributions, " +
                     "%d licenses, and %d publishers.",
                     len(assets), len(distributions), len(licenses),
                     len(publishers))
        CURRENT_MODULE = ""


processors = {}
for filename in os.listdir(os.path.join(os.path.dirname(__file__), 'repos')):
    if filename.endswith('.py') and not filename.startswith('__'):
        name = filename[:-3]
        processors[name] = Processor(name)

