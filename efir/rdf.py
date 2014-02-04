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

from rdflib import URIRef, Literal
from rdflib.namespace import RDF, RDFS, XSD, OWL, SKOS, DCTERMS, FOAF

ADMS = rdflib.Namespace("http://www.w3.org/ns/adms#")
ADMSSW = rdflib.Namespace("http://purl.org/adms/sw/")
RADION = rdflib.Namespace("http://www.w3.org/ns/radion#")
DCAT = rdflib.Namespace("http://www.w3.org/ns/dcat#")
WRDS = rdflib.Namespace("http://www.w3.org/2007/05/powder-s#")
SCHEMA = rdflib.Namespace("http://schema.org/")
SPDX = rdflib.Namespace("http://spdx.org/rdf/terms#")


class Graph(rdflib.Graph):

    '''An RDF graph somewhat specialized for ADMS.'''

    def __init__(self):
        rdflib.Graph.__init__(self)
        self.bind('rdf', str(RDF))
        self.bind('rdfs', str(RDFS))
        self.bind('xsd', str(XSD))
        self.bind('owl', str(OWL))
        self.bind('skos', str(SKOS))
        self.bind('dcterms', str(DCTERMS))
        self.bind('foaf', str(FOAF))
        self.bind('adms', str(ADMS))
        self.bind('admssw', str(ADMSSW))
        self.bind('radion', str(RADION))
        self.bind('dcat', str(DCAT))
        self.bind('wrds', str(WRDS))
        self.bind('schema', str(SCHEMA))
        self.bind('spdx', str(SPDX))

    @classmethod
    def load(cls, name, format='xml'):
        '''Load RDF file or URL and return a Graph object.'''
        logging.debug("Loading RDF graph %s.", name)
        g = cls()
        with open_data(name, binary=True) as f:
            g.parse(f, format=format)
        return g

    def add(self, item):
        if isinstance(item, ADMSResource):
            item._add_to_graph(self)
        else:
            super().add(item)


class ADMSProperty:

    '''Property of a domain model class.'''

    def __init__(self, uri, rng=None, min=0, max=-1):
        assert isinstance(uri, URIRef)
        self.uri = uri
        self.rng = rng
        self.min = min
        self.max = max

    def _warning(self, g, subject, msg, *values):
        msg = "Class %s, property %s for %s: " + msg
        values = [subject.__class__.__name__, g.qname(self.uri), subject.uri] + \
                 list(values)
        logging.warning(msg, *values)

    def _add_to_graph(self, g, subject, values, memo):
        if isinstance(values, list) or isinstance(values, set):
            values = [v for v in values if v is not None]
        elif values is not None:
            values = [values]
        else:
            values = []
        if len(values) < self.min:
            self._warning(g, subject, "missing values, got %d, need %d.",
                          len(values), self.min)
        elif self.max > 0 and len(values) > self.max:
            self._warning(g, subject, "too many values, got %d, max %d.",
                          len(values), self.max)
        for value in values:
            self._add_value(g, subject, value, memo)

    def _validate(self, value, obj, rng=None):
        if rng is None:
            rng = self.rng
        if rng is None:
            return True
        if isinstance(rng, list) or isinstance(rng, tuple):
            for r in rng:
                if self._validate(value, obj, r):
                    return True
            return False
        if isinstance(rng, rdflib.Namespace):
            return isinstance(obj, URIRef) and obj.startswith(self.rng)
        elif issubclass(self.rng, rdflib.term.Identifier):
            return isinstance(obj, self.rng)
        elif issubclass(self.rng, ADMSResource):
            return isinstance(value, self.rng)
        elif isinstance(obj, Literal):
            return isinstance(obj.toPython(), self.rng)
        else:
            return False

    def _add_value(self, g, subject, value, memo):
        # Transform value
        obj = value
        if isinstance(value, ADMSResource):
            value._add_to_graph(g, memo)
            obj = value.uri
        elif not isinstance(value, rdflib.term.Identifier):
            obj = Literal(value)
        # Validate
        if not self._validate(value, obj):
            self._warning(g, subject,
                          "invalid value %s of type %s, expected %s.",
                          value, type(value).__name__, self.rng)
        # Add to graph
        g.add((subject.uri, self.uri, obj))


class ADMSResource:

    '''Super-class for domain model classes.'''

    def __init__(self, uri):
        assert isinstance(uri, URIRef)
        self.uri = uri
        for name, prop in self.__class__.__dict__.items():
            if isinstance(prop, ADMSProperty):
                setattr(self, name, None)

    def __repr__(self):
        return '<' + self.__class__.__name__ + ' ' + self.uri + '>'

    def _add_to_graph(self, g, memo=None):
        '''Add this resource and all depending ones to the graph g.'''
        if memo is None:
            memo = set()
        if self.uri in memo:
            return
        memo.add(self.uri)
        g.add((self.uri, RDF.type, self.TYPE_URI))
        for name, prop in self.__class__.__dict__.items():
            if not isinstance(prop, ADMSProperty):
                continue
            value = getattr(self, name)
            if isinstance(value, list) or isinstance(value, set):
                for v in value:
                    prop._add_to_graph(g, self, v, memo)
            else:
                prop._add_to_graph(g, self, value, memo)
