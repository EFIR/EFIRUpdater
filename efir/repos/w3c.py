# W3C Standards and Technical Reports
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
import datetime

from .. import *

QUERIES = [
# Create distributions and update asset
"""
PREFIX adms: <http://www.w3.org/ns/adms#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX radion: <http://www.w3.org/ns/radion#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

INSERT {
  ?d a adms:SemanticAssetDistribution ;
     radion:distributionOf ?asset ;
     adms:accessURL ?asset ;
     rdfs:label ?name ;
     dcterms:license ?license ;
     dcterms:format <http://purl.org/NET/mediatypes/text/html> ;
     adms:status ?status .
  ?asset radion:distribution ?d .
} WHERE {
  ?asset rdf:type adms:SemanticAsset ;
         rdfs:label ?name ;
         dcterms:license ?license ;
         adms:status ?status .
  BIND(IRI(CONCAT(str(?asset), "?type=distribution")) AS ?d)
}
""",
# Delete unnecessary properties for semantic assets
"""
PREFIX adms: <http://www.w3.org/ns/adms#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX radion: <http://www.w3.org/ns/radion#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

DELETE {
  ?asset rdf:type adms:SemanticAssetDistribution ;
         radion:distribution ?asset ;
         dcterms:format ?format ;
         dcterms:license ?license ;
         dcterms:type ?type ;
         dcterms:title ?title ;
         adms:accessURL ?accessURL .
} WHERE {
  ?asset rdf:type adms:SemanticAsset ;
         dcterms:format ?format ;
         dcterms:license ?license ;
         dcterms:type ?type ;
         dcterms:title ?title ;
         adms:accessURL ?accessURL .
}
""",
# Add asset type to semantic assets
"""
PREFIX adms: <http://www.w3.org/ns/adms#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX radion: <http://www.w3.org/ns/radion#>
PREFIX rdf:<http://www.w3.org/1999/02/22-rdf-syntax-ns#>

INSERT {
  ?asset dcterms:type <http://purl.org/adms/assettype/Schema> .
} WHERE {
  ?asset rdf:type adms:SemanticAsset .
}
""",
# Delete empty description properties from semantic assets
"""
PREFIX adms: <http://www.w3.org/ns/adms#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX radion: <http://www.w3.org/ns/radion#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

DELETE {
  ?s dcterms:description ?desc
} WHERE {
  ?s dcterms:description ?desc
  FILTER(str(?desc) = "")
}
""",
# Add description for semantic assets without description
"""
PREFIX adms: <http://www.w3.org/ns/adms#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX radion: <http://www.w3.org/ns/radion#>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

INSERT {
  ?asset dcterms:description "The description of this asset is not available"@en
} WHERE {
  ?asset rdf:type adms:SemanticAsset
  FILTER NOT EXISTS { ?asset dcterms:description ?description }
}
"""
]


def process():
    g = load_rdf("http://www.w3.org/2012/06/tr2adms/adms", format='turtle')
    for query in QUERIES:
        logging.debug("Running update query %s", query)
        g.update(query)
    logging.debug("Transforming dcterms:created dates into xsd:dateTime.")
    for s, p, o in g.triples((None, DCTERMS.created, None)):
        d = rdflib.Literal(str(o), datatype=XSD.date).value
        newo = rdflib.Literal(datetime.datetime(d.year, d.month, d.day))
        g.remove((s,p,o))
        g.add((s,p,newo))
    return g
