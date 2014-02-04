# RDF utilities
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
import rdflib
from .files import *

from rdflib.namespace import RDF, RDFS, XSD, DCTERMS, FOAF

ADMS = rdflib.Namespace("http://www.w3.org/ns/adms#")
RADION = rdflib.Namespace("http://www.w3.org/ns/radion#")

def load_rdf(name, format='xml'):
    '''Load RDF file or URL and return a rdflib.Graph object.'''
    logging.debug("Loading RDF graph %s.", name)
    # Load graph
    g = rdflib.Graph()
    with open_data(name, binary=True) as f:
        g.parse(f, format=format)
    # Add common ADMS bindings
    g.bind('adms', "http://www.w3.org/ns/adms#")
    g.bind('dcterms', "http://purl.org/dc/terms/")
    g.bind('rad', "http://www.w3.org/ns/radion#")
    g.bind('foaf', "http://xmlns.com/foaf/0.1/")
    return g
