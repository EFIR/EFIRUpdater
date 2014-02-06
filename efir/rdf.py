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
XHV = rdflib.Namespace("http://www.w3.org/1999/xhtml/vocab#")

# Global dictionary of registered ADMSResources, indexed by type uri.
ADMS_RESOURCES = {}


class Graph(rdflib.Graph):

    '''An RDF graph somewhat specialized for ADMS.'''

    def __init__(self, data=None):
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
        self.bind('xhv', str(XHV))
        if data is not None:
            self.add(data)

    @classmethod
    def load(cls, name, format='xml'):
        '''Load RDF file or URL and return a Graph object.'''
        logging.debug("Loading RDF graph %s.", name)
        g = cls()
        with open_data(name, binary=True) as f:
            g.parse(f, format=format)
        return g

    def add(self, item, memo=None):
        if memo is None:
            memo = set()
        if isinstance(item, list):
            for it in item:
                self.add(it, memo)
        elif isinstance(item, ADMSResource):
            item._add_to_graph(self, memo)
        else:
            super().add(item)

    def update(self, query):
        query = "".join("PREFIX " + name + ": <" + str(uri) + ">\n"
                        for name, uri in self.namespaces()) + query
        super().update(query)

    def extract(self, uri, known={}):
        '''Extract resource uri from the graph. The triples found are removed.
        The extraction is recursive. Known (i.e., already extracted) objects
        are fetched from and put into the known dictionary.
        Uri may also be a literal, in which case it is returned as is.
        '''
        if isinstance(uri, Literal):
            return uri
        if uri in known:
            return known[uri]
        type_uris = self.objects(uri, RDF.type)
        cls = None
        for type_uri in self.objects(uri, RDF.type):
            if type_uri in ADMS_RESOURCES:
                newcls = ADMS_RESOURCES[type_uri]
                if cls is not None and newcls != cls:
                    logging.warning("Type conflict for uri %s, pretend %s, but already %s.",
                                    uri, newcls.__name__, cls.__name__)
                else:
                    cls = newcls
        if cls is None:
            return uri
        resource = cls(uri)
        known[uri] = resource
        for type_uri in resource.PARSE_URIS:
            self.remove((uri, RDF.type, type_uri))
        for name, prop in resource.properties():
            values = set()
            for prop_uri in prop.parse_uris:
                values.update(self.extract(obj, known)
                              for obj in self.objects(uri, prop_uri))
                self.remove((uri, prop_uri, None))
            for prop_uri in prop.parse_inv:
                values.update(self.extract(subj, known)
                              for subj in self.subjects(prop_uri, uri))
                self.remove((None, prop_uri, uri))
            if len(values) == 0:
                continue
            if len(values) == 1:
                values = values.pop()
            setattr(resource, name, values)
        return resource

    def extract_all(self, cls):
        '''Extract all resources of type cls (must be a subclass of
        ADMSResource). The triples found are removed from the graph.
        The extraction is recursive.'''
        assert issubclass(cls, ADMSResource)
        known = {}
        result = []
        for type_uri in cls.PARSE_URIS:
            for uri in list(self.subjects(RDF.type, type_uri)):
                result.append(self.extract(uri, known))
        return result


class ADMSProperty:

    '''Property of a domain model class.

    Attributes:
    uris -- the set of URIRef of the property
    parse_uris -- the set of recognized URIRef of the property
    inv -- the set of URIRef of the inverse property
    parse_inv -- the set of recognized URIRef of the inverse property
    rng -- the range, a namespace, a tuple of namespaces, a class, or None
    min -- the minimum cardinality
    max -- the maximum cardinality or None if infinite
    '''

    def __init__(self, *uris, also=None, inv=None, also_inv=None,
                 rng=None, min=0, max=None):
        assert all(isinstance(uri, URIRef) for uri in uris)
        self.uris = set(uris)
        if also is None:
            self.parse_uris = self.uris
        elif isinstance(also, URIRef):
            self.parse_uris = self.uris | {also}
        else:
            assert all(isinstance(uri, URIRef) for uri in also)
            self.parse_uris = self.uris | set(also)
        if inv is None:
            self.inv = set()
        elif isinstance(inv, URIRef):
            self.inv = {inv}
        else:
            assert all(isinstance(uri, URIRef) for uri in inv)
            self.inv = set(inv)
        if also_inv is None:
            self.parse_inv = self.inv
        elif isinstance(also_inv, URIRef):
            self.parse_inv = self.inv | {also_inv}
        else:
            assert all(isinstance(uri, URIRef) for uri in also_inv)
            self.parse_inv = self.inv | set(also_inv)
        self.rng = rng
        self.min = min
        self.max = max

    def __repr__(self):
        return '<' + self.__class__.__name__ + ' ' + \
               ", ".join(str(uri) for uri in self.uris) + '>'

    def _warning(self, g, subject, msg, *values):
        msg = "Class %s, property %s for %s: " + msg
        values = [subject.__class__.__name__,
                  ", ".join(g.qname(uri) for uri in self.uris),
                  subject.uri] + \
                 list(values)
        logging.warning(msg, *values)

    def _add_to_graph(self, g, subject, values, memo):
        if values is None:
            values = {}
        elif not isinstance(values, set):
            values = {values}
        if len(values) < self.min:
            self._warning(g, subject, "missing values, got %d, need %d.",
                          len(values), self.min)
        elif self.max is not None and len(values) > self.max:
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
            return isinstance(value, self.rng) or isinstance(obj, URIRef)
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
        for uri in self.uris:
            g.add((subject.uri, uri, obj))
        if self.inv and isinstance(obj, Literal):
            self._warning(g, subject,
                          "cannot create inverse property for %s.", obj)
        else:
            for uri in self.inv:
                g.add((obj, uri, subject.uri))


class ADMSResource:

    '''Super-class for domain model classes.
    All subclasses shall have the @adms_type_uri(uri) decorator.

    Values for properties may be None, a single value, or a set of values.
    '''

    def __init__(self, uri):
        assert isinstance(uri, URIRef)
        self.uri = uri
        for name, prop in self.__class__.__dict__.items():
            if isinstance(prop, ADMSProperty):
                setattr(self, name, None)

    def __repr__(self):
        return '<' + self.__class__.__name__ + ' ' + str(self.uri) + '>'

    def __hash__(self):
        return hash(self.uri)

    def __eq__(self, obj):
        if obj is None or not isinstance(obj, self.__class__):
            return False
        return self.uri == obj.uri

    @classmethod
    def properties(cls):
        '''Yield all (name, properties) tuples of this resource.'''
        for name, prop in cls.__dict__.items():
            if isinstance(prop, ADMSProperty):
                yield (name, prop)

    def _add_to_graph(self, g, memo):
        '''Add this resource and all depending ones to the graph g.'''
        if self.uri in memo:
            return
        memo.add(self.uri)
        for type_uri in self.TYPE_URIS:
            g.add((self.uri, RDF.type, type_uri))
        for name, prop in self.__class__.__dict__.items():
            if not isinstance(prop, ADMSProperty):
                continue
            prop._add_to_graph(g, self, getattr(self, name), memo)


def adms_type_uri(*uris, also=None):
    '''Decorator for ADMSResource.

    Arguments:
    uris -- the type URIs of the resource
    also -- additional type URIs that are recognized (but not generated)
    '''
    assert len(uris) >= 1
    assert all(isinstance(uri, URIRef) for uri in uris)
    if also is None:
        parse_uris = uris
    elif isinstance(also, URIRef):
        parse_uris = uris + (also,)
    else:
        assert all(isinstance(uri, URIRef) for uri in also)
        parse_uris = uris + tuple(parse_uris)
    def f(cls):
        cls.TYPE_URIS = uris
        cls.PARSE_URIS = parse_uris
        for uri in parse_uris:
            assert uri not in ADMS_RESOURCES
            ADMS_RESOURCES[uri] = cls
        return cls
    return f
