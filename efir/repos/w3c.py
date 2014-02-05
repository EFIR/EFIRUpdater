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

from .. import *

URL = "http://www.w3.org/2012/06/tr2adms/adms"

QUERIES = [
# Remove double statuses
"""
DELETE {
  ?asset adms:status ?other
} WHERE {
  ?asset a adms:SemanticAsset ;
         adms:status <http://purl.org/adms/status/Deprecated> ;
         adms:status ?other
  FILTER(?other != <http://purl.org/adms/status/Deprecated>)
}
""",
# Fix dcterms:created dates
"""
DELETE {
  ?s dcterms:created ?str
} INSERT {
  ?s dcterms:created ?date
} WHERE {
  ?s dcterms:created ?str
  BIND(xsd:dateTime(CONCAT(?str, "T00:00:00")) AS ?date)
}
""",
# Split assets and distributions
"""
DELETE {
  ?asset a adms:SemanticAssetDistribution ;
         radion:distribution ?asset ;
         dcterms:format ?format ;
         dcterms:license ?license ;
         dcterms:type ?type ;
         dcterms:title ?title ;
         adms:accessURL ?accessURL .
} INSERT {
  ?d a adms:SemanticAssetDistribution ;
     radion:distributionOf ?asset ;
     adms:accessURL ?asset ;
     rdfs:label ?name ;
     dcterms:license ?license ;
     dcterms:format <http://purl.org/NET/mediatypes/text/html> ;
     adms:status ?status .
  ?asset radion:distribution ?d ;
         dcterms:type <http://purl.org/adms/assettype/Schema> ;
         dcat:theme <http://eurovoc.europa.eu/100150> .
} WHERE {
  ?asset a adms:SemanticAsset ;
         rdfs:label ?name ;
         dcterms:format ?format ;
         dcterms:license ?license ;
         dcterms:type ?type ;
         dcterms:title ?title ;
         adms:accessURL ?accessURL ;
         adms:status ?status .
  BIND(IRI(CONCAT(str(?asset), "?type=distribution")) AS ?d)
}
""",
# Add dcterms:modified if it does not exist
"""
INSERT {
  ?asset dcterms:modified ?date .
} WHERE {
  ?asset a adms:SemanticAsset ;
         dcterms:created ?date .
  FILTER NOT EXISTS { ?asset dcterms:modified ?modified }
}
""",
# Delete empty description properties from semantic assets
"""
DELETE {
  ?s dcterms:description ?desc
} WHERE {
  ?s dcterms:description ?desc
  FILTER(str(?desc) = "")
}
""",
# Add description for semantic assets without description
"""
INSERT {
  ?asset dcterms:description "The description of this asset is not available"@en
} WHERE {
  ?asset a adms:SemanticAsset
  FILTER NOT EXISTS { ?asset dcterms:description ?description }
}
""",
# Add missing data
"""
INSERT DATA {
  <http://www.w3.org/data#W3C> a foaf:Agent ;
    foaf:name "World Wide Web Consortium" ;
    dcterms:type <http://purl.org/adms/publishertype/StandardisationBody> .
  <http://www.w3.org/2012/05/cat#DocLicense> dcterms:type
    <http://purl.org/adms/licencetype/NoDerivativeWork> .
}
"""
]


def process():
    g = Graph.load(URL, format='turtle')
    for query in QUERIES:
        logging.debug("Running update query %s", query)
        g.update(query)
    logging.debug("Extracting assets from RDF for validation.")
    assets = g.extract_all(Asset)
    return Graph(assets)
