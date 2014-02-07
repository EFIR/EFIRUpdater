# Linked Open Vocabularies
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

from .. import *

NAME = 'lov'
URL = "http://lov.okfn.org/dataset/lov/lov.rdf"

CONSTRUCT = """
PREFIX voaf: <http://purl.org/vocommons/voaf#>
PREFIX bibo: <http://purl.org/ontology/bibo/>

CONSTRUCT {
  <http://lov.okfn.org/dataset/lov> a adms:AssetRepository ;
        dcat:accessURL <http://lov.okfn.org/dataset/lov/> ;
        dcterms:title "Linked Open Vocabularies"@en ;
        dcterms:description "LOV objective is to provide easy access methods to this ecosystem of vocabularies, and in particular by making explicit the ways they link to each other and providing metrics on how they are used in the linked data cloud, help to improve their understanding, visibility and usability, and overall quality."@en ;
        dcat:dataset ?asset .

  ?asset a adms:Asset .
  ?asset dcterms:title ?title .
  ?asset skos:altLabel ?shortTitle .
  ?asset adms:status <http://purl.org/adms/status/Completed> .
  ?asset dcterms:publisher ?publisher, ?creator .
  ?asset dcterms:description ?description .
  ?asset dcterms:issued ?issued .
  ?asset dcterms:modified ?modified .
  ?asset dcterms:type <http://purl.org/adms/assettype/Ontology> .
  ?asset radion:distribution ?d .
  ?asset dcterms:relation ?extends .
  ?asset dcterms:relation ?specializes .
  ?asset dcterms:relation ?reliesOn .
  ?asset dcterms:relation ?usedBy .
  ?asset dcterms:relation ?generalizes .
  ?asset dcterms:relation ?hasEquivalencesWith .
  ?asset dcterms:relation ?hasDisjunctionsWith .
  ?asset dcterms:relation ?similar .

  ?d a adms:AssetDistribution .
  ?d dcat:accessURL ?asset .
  ?d adms:status <http://purl.org/adms/status/Completed> .
  ?d dcterms:format <http://purl.org/NET/mediatypes/text/html> .
  ?d adms:representationTechnique <http://purl.org/adms/representationtechnique/HumanLanguage> .
  ?d dcterms:publisher ?publisher, ?creator .
  ?d dcterms:issued ?issued .
  ?d dcterms:modified ?modified .

  ?publisher a foaf:Agent .
  ?publisher foaf:name ?publishername .

  ?creator a foaf:Agent .
  ?creator foaf:name ?creatorname .
  ?creator dcterms:type <http://purl.org/adms/publishertype/PrivateIndividual(s)> .
} WHERE {
  ?asset rdf:type voaf:Vocabulary ;
         dcterms:title ?title .
  FILTER NOT EXISTS { ?asset dcterms:publisher <http://www.w3.org/data#W3C> }
  OPTIONAL { ?asset dcterms:description ?description }
  OPTIONAL { ?asset dcterms:modified ?modified }
  OPTIONAL { ?asset dcterms:issued ?issued }
  OPTIONAL {
    ?asset dcterms:publisher ?publisher
    OPTIONAL { ?publisher foaf:name ?publishername }
  }
  OPTIONAL {
    ?asset dcterms:creator ?creator
    FILTER NOT EXISTS { ?asset dcterms:publisher ?publisher }
    OPTIONAL { ?creator foaf:name ?creatorname }
  }
  OPTIONAL { ?asset bibo:shortTitle ?shortTitle }
  OPTIONAL { ?asset voaf:extends ?extends }
  OPTIONAL { ?asset voaf:specializes ?specializes }
  OPTIONAL { ?asset voaf:reliesOn ?reliesOn }
  OPTIONAL { ?asset voaf:usedBy ?usedBy }
  OPTIONAL { ?asset voaf:generalizes ?generalizes }
  OPTIONAL { ?asset voaf:hasEquivalencesWith ?hasEquivalencesWith }
  OPTIONAL { ?asset voaf:hasDisjunctionsWith ?hasDisjunctionsWith }
  OPTIONAL { ?asset voaf:similar ?similar }
  BIND(IRI(CONCAT(str(?asset), "?type=distribution")) AS ?d)
}
"""

QUERIES = [
# Ensure all text fields have a language tag
"""
DELETE {
  ?s ?p ?o
} INSERT {
  ?s ?p ?olang
} WHERE {
  ?s ?p ?o
  FILTER(?p IN (foaf:name, dcterms:title, dcterms:description))
  FILTER(lang(?o) = "")
  BIND(STRLANG(?o, "en") AS ?olang)
}
""",
# Fix dates
# Note: a bug in the implementation of the CONCAT function in rdflib prevents
# to combine those two queries.
"""
DELETE {
  ?s dcterms:modified ?str
} INSERT {
  ?s dcterms:modified ?date
} WHERE {
  ?s dcterms:modified ?str
  BIND(xsd:dateTime(CONCAT(?str, "T00:00:00")) AS ?date)
}
""",
"""
DELETE {
  ?s dcterms:issued ?str
} INSERT {
  ?s dcterms:issued ?date
} WHERE {
  ?s dcterms:issued ?str
  BIND(xsd:dateTime(CONCAT(?str, "T00:00:00")) AS ?date)
}
""",
# Add missing dcterms:modified on Assets
"""
INSERT {
  ?asset dcterms:modified ?date .
} WHERE {
  ?asset a adms:Asset ;
         dcterms:issued ?date .
  FILTER NOT EXISTS { ?asset dcterms:modified ?modified }
}
""",
# Generate missing descriptions
"""
INSERT {
  ?asset dcterms:description "The description of this asset is not available"@en
} WHERE {
  ?asset a adms:Asset
  FILTER NOT EXISTS { ?asset dcterms:description ?description }
}
"""
]


def process():
    g = Graph.load(NAME, URL, format='xml')
    logging.debug("Constructing ADMS graph")
    adms = g.query(CONSTRUCT).graph
    for query in QUERIES:
        logging.debug("Running update query %s", query)
        adms.update(query)
    logging.debug("Extracting repository.")
    repo = adms.extract(URIRef("http://lov.okfn.org/dataset/lov"))
    repo.modified = get_modified(NAME, URL)
    return repo
