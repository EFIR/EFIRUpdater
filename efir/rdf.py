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
        uri = name if is_url(name) else "http://localhost/"
        g = cls()
        with open_data(name, binary=True) as f:
            g.parse(f, format=format, publicID=uri)
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

    def query(self, *args, **kwargs):
        result = super().query(*args, **kwargs)
        if result.graph is not None:
            g = Graph()
            g += result.graph
            result.graph = g
        return result

    def update(self, query):
        query = "".join("PREFIX " + name + ": <" + str(uri) + ">\n"
                        for name, uri in self.namespaces()) + query
        super().update(query)

    def extract(self, uri, known={}):
        '''Extract resource uri from the graph.
        The extraction is recursive. Known (i.e., already extracted) objects
        are fetched from and put into the known dictionary.
        Uri may also be a literal, in which case it is returned as is.
        '''
        if isinstance(uri, Literal):
            return uri
        if uri in known:
            return known[uri]
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
        for name, prop in resource.properties():
            values = set()
            for prop_uri in prop.parse_uris:
                values.update(self.extract(obj, known)
                              for obj in self.objects(uri, prop_uri))
            for prop_uri in prop.parse_inv:
                values.update(self.extract(subj, known)
                              for subj in self.subjects(prop_uri, uri))
            if len(values) == 0:
                continue
            if len(values) == 1:
                values = values.pop()
            setattr(resource, name, values)
        return resource

    def extract_all(self, cls):
        '''Extract all resources of type cls (must be a subclass of
        ADMSResource). The extraction is recursive.'''
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
    name -- the name of the property (set by @adms_resource)
    resource_cls -- the containing resource class (set by @adms_resource)
    uris -- the set of URIRef of the property
    parse_uris -- the set of recognized URIRef of the property
    inv -- the set of URIRef of the inverse property
    parse_inv -- the set of recognized URIRef of the inverse property
    rng -- the range: a namespace, a class, a special value, or None; multiple
           options may be given in a tuple
    min -- the minimum cardinality
    max -- the maximum cardinality or None if infinite
    '''

    # Range of Literals with mandatory language tags
    TEXT = "text"

    # Range of Literals with mandatory unique language tags
    UNIQUETEXT = "unique text"

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

    def __str__(self):
        return self.resource_cls.__name__ + '.' + self.name

    def __repr__(self):
        return '<Property ' + str(self) + '>'

    def __hash__(self):
        return hash(self.resource_cls) | hash(self.name)

    def __eq__(self, obj):
        if obj is None or not isinstance(obj, self.__class__):
            return False
        return self.resource_cls == obj.resource_cls and self.name == obj.name

    def _to_rdf(self, value):
        '''Return the RDF value of value.'''
        if isinstance(value, rdflib.term.Identifier):
            return value
        elif isinstance(value, ADMSResource):
            return value.uri
        else:
            return Literal(value)

    def validate(self, resource, deep=True, result=None):
        '''Validate this property.

        Arguments:
        resource -- the subject (an ADMSResource's subclass instance)
        deep -- if True, validate values recursively
        result -- the ValidationResult object
        '''
        assert isinstance(resource, self.resource_cls)
        if result is None:
            result = ValidationResult()
        values = resource.get_values(self)
        # Check cardinality
        if len(values) < self.min:
            result.add(self, "Missing values", resource, len(values), self.min)
        elif self.max is not None and len(values) > self.max:
            result.add(self, "Too many values", resource, len(values), self.max)
        # Check individual values
        for value in values:
            # Recursive check
            if deep and isinstance(value, ADMSResource):
                value.validate(deep=deep, result=result)
            # Range check
            if self.rng is not None:
                ranges = self.rng
                if not isinstance(ranges, tuple):
                    ranges = (ranges,)
                obj = self._to_rdf(value)
                for rng in ranges:
                    if rng in (ADMSProperty.TEXT, ADMSProperty.UNIQUETEXT):
                        if isinstance(obj, Literal) and obj.language is not None:
                            break
                    elif isinstance(rng, rdflib.Namespace):
                        if isinstance(obj, URIRef) and obj.startswith(rng):
                            break
                    elif issubclass(rng, rdflib.term.Identifier):
                        if isinstance(obj, rng):
                            break
                    elif issubclass(rng, ADMSResource):
                        if isinstance(value, rng) or isinstance(obj, URIRef):
                            break
                    elif isinstance(obj, Literal):
                        if isinstance(obj.toPython(), rng):
                            break
                else:
                    result.add(self, "Wrong type", resource,
                               obj.n3(), self.rng)
            # Inverse property check
            if self.inv and isinstance(obj, Literal):
                result.add(self, "Literal subject in inverse property",
                           resource, obj.n3(), "resource")
        # Check for unique language tags
        if self.rng == ADMSProperty.UNIQUETEXT:
            languages = set()
            for value in values:
                if isinstance(value, Literal) and value.language is not None:
                    if value.language in languages:
                        result.add(self, "Multiple values for a language",
                                   resource, value.n3(), None)
                        break
                    languages.add(value.language)
        return result

    def _add_to_graph(self, resource, g, memo):
        for value in resource.get_values(self):
            if isinstance(value, ADMSResource):
                value._add_to_graph(g, memo)
            obj = self._to_rdf(value)
            for uri in self.uris:
                g.add((resource.uri, uri, obj))
            for uri in self.inv:
                g.add((obj, uri, resource.uri))


class ADMSResource:

    '''Super-class for domain model classes.
    All subclasses shall have the @adms_resource(uri) decorator.

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

    def get_values(self, prop):
        '''Return the set of values for property prop (a string or ADMSProperty
        instance.'''
        if isinstance(prop, ADMSProperty):
            prop = prop.name
        values = getattr(self, prop)
        if values is None:
            values = set()
        elif not isinstance(values, set):
            values = {values}
        return values

    def validate(self, deep=True, result=None):
        '''Validate this resource and all its values recursively.

        Arguments:
        deep -- if True, validate values recursively
        result -- the ValidationResult object
        '''
        if result is None:
            result = ValidationResult()
        if self in result.checked:
            return result
        result.checked.add(self)
        for name, prop in self.properties():
            prop.validate(self, deep=deep, result=result)
        if hasattr(self, '_validate'):
            self._validate(result)
        return result

    def _add_to_graph(self, g, memo):
        '''Add this resource and all depending ones to the graph g.'''
        if self.uri in memo:
            return
        memo.add(self.uri)
        for type_uri in self.TYPE_URIS:
            g.add((self.uri, RDF.type, type_uri))
        for name, prop in self.properties():
            prop._add_to_graph(self, g, memo)


def adms_resource(*uris, also=None):
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
        for name, prop in cls.properties():
            prop.name = name
            prop.resource_cls = cls
        return cls
    return f


class ValidationResult:

    '''The result of a validation.'''

    def __init__(self):
        self.errors = {}
        self.checked = set()  # set of checked resources

    def __bool__(self):
        return not self.errors

    def add(self, prop, message, resource, actual, expected):
        '''Add a validation error.'''
        key = (prop, message)
        value = (resource, actual, expected)
        if key not in self.errors:
            self.errors[key] = []
        self.errors[key].append(value)

    def log(self):
        '''Write the validation errors to the log.'''
        for (prop, message), instances in self.errors.items():
            instances = ["(" + str(resource.uri) + " has " + str(actual) +
                         (", expected " + str(expected) if expected else "") +
                         ")"
                         for resource, actual, expected in instances]
            line = str(prop) + ": " + message + " " + ", ".join(instances[:3])
            if len(instances) > 3:
                line += ", and %d more" % (len(instances) - 3)
            logging.warning(line)
            logging.debug("All errors: " + ", ".join(instances))


def validate(resources):
    '''Validate a list, tuple or set of resources.'''
    if isinstance(resources, ADMSResource):
        return resources.validate()
    else:
        result = ValidationResult()
        for resource in resources:
            resource.validate(result=result)
        return result
