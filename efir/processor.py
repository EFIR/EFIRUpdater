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

class Processor:

    '''
    A Processor is a module living in the repositories package and containing a
    process() function returning the ADMS graph.

    '''

    def __init__(self, name):
        self.name = name

    def process(self):
        logging.info("Processing repository %s.", self.name)
        module = importlib.import_module('..repos.' + self.name, __name__)
        g = module.process()
        filename = os.path.join(OUT_DIR, self.name + '.rdf')
        logging.debug("Serializing result to %s.", filename)
        os.makedirs(OUT_DIR, exist_ok=True)
        with open(filename, 'wb') as f:
            g.serialize(f)


processors = {}
for filename in os.listdir(os.path.join(os.path.dirname(__file__), 'repos')):
    if filename.endswith('.py') and not filename.startswith('__'):
        name = filename[:-3]
        processors[name] = Processor(name)

