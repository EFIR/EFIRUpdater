# ADMS-AP domain model implemented in Python classes
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

import datetime
from .rdf import *


## Controlled vocabularies

InteroperabilityLevel = rdflib.Namespace("http://purl.org/adms/interoperabilitylevel/")
RepresentationTechnique = rdflib.Namespace("http://purl.org/adms/representationtechnique/")
Status = rdflib.Namespace("http://purl.org/adms/status/")
#MediaType = rdflib.Namespace("http://publications.europa.eu/resource/authority/file-type")
MediaType = rdflib.Namespace("http://purl.org/NET/mediatypes/")
Eurovoc = rdflib.Namespace("http://eurovoc.europa.eu/")
Language = rdflib.Namespace("http://publications.europa.eu/resource/authority/language")
Country = rdflib.Namespace("http://publications.europa.eu/resource/authority/country")
Place = rdflib.Namespace("http://publications.europa.eu/resource/authority/place/")
AssetType = rdflib.Namespace("http://purl.org/adms/assettype/")
SolutionType = rdflib.Namespace("http://purl.org/adms/solutiontype/")
LicenceType = rdflib.Namespace("http://purl.org/adms/licencetype/")
PublisherType = rdflib.Namespace("http://purl.org/adms/publishertype/")


## Classes

@adms_resource(DCTERMS.Agent, also=FOAF.Agent)
class Publisher(ADMSResource):

    # Recommended properties
    name            = ADMSProperty(RDFS.label, also=FOAF.name, rng=Literal)
    type            = ADMSProperty(DCTERMS.type, rng=PublisherType)

    def __init__(self, uri):
        ADMSResource.__init__(self, uri)


@adms_resource(DCTERMS.LicenseDocument)
class LicenseDocument(ADMSResource):

    # Mandatory properties
    type            = ADMSProperty(DCTERMS.type, rng=LicenceType, min=1, max=1)
    # Recommended properties
    label           = ADMSProperty(RDFS.label, rng=Literal)
    description     = ADMSProperty(DCTERMS.description, rng=Literal)

    def __init__(self, uri):
        ADMSResource.__init__(self, uri)


@adms_resource(ADMS.SemanticAssetDistribution, also=ADMS.AssetDistribution)
class AssetDistribution(ADMSResource):

    # Mandatory properties
    accessURL       = ADMSProperty(ADMS.accessURL, also=DCAT.accessURL, rng=URIRef, min=1)
    # Recommended properties
    status          = ADMSProperty(ADMS.status, rng=Status, max=1)
    downloadURL     = ADMSProperty(DCAT.downloadURL, rng=URIRef)
    mediaType       = ADMSProperty(DCAT.mediaType, rng=MediaType, max=1)
    license         = ADMSProperty(DCTERMS.license, rng=LicenseDocument, max=1)
    # Optional properties
    representationTechnique = ADMSProperty(ADMS.representationTechnique, rng=RepresentationTechnique, max=1)
    description     = ADMSProperty(DCTERMS.description, rng=Literal)
    format          = ADMSProperty(DCTERMS.term("format"), rng=MediaType, max=1)
    issued          = ADMSProperty(DCTERMS.created, also=DCTERMS.issued, rng=datetime.datetime, max=1)
    modified        = ADMSProperty(DCTERMS.modified, rng=datetime.datetime, max=1)
    publisher       = ADMSProperty(DCTERMS.publisher, rng=Publisher)
    title           = ADMSProperty(DCTERMS.title, RDFS.label, rng=Literal)
    fileSize        = ADMSProperty(SCHEMA.fileSize, max=1)
    checksum        = ADMSProperty(SPDX.checksum, max=1)
    tagURL          = ADMSProperty(ADMSSW.tagURL, max=1)

    def __init__(self, uri):
        ADMSResource.__init__(self, uri)


@adms_resource(ADMS.SemanticAsset, also=ADMS.Asset)
class Asset(ADMSResource):

    # Mandatory properties
    theme           = ADMSProperty(also=DCAT.theme, rng=Eurovoc, min=1)
    description     = ADMSProperty(DCTERMS.description, rng=Literal, min=1)
    modified        = ADMSProperty(DCTERMS.modified, rng=datetime.datetime, min=1, max=1)
    publisher       = ADMSProperty(DCTERMS.publisher, rng=Publisher, min=1)
    title           = ADMSProperty(DCTERMS.title, RDFS.label, rng=Literal, min=1)
    type            = ADMSProperty(DCTERMS.type, rng=(AssetType,SolutionType), min=1)
    # Recommended properties
    status          = ADMSProperty(ADMS.status, rng=Status, max=1)
    interoperabilityLevel = ADMSProperty(ADMS.interoperabilityLevel, rng=InteroperabilityLevel)
    contactPoint    = ADMSProperty(DCAT.contactPoint, max=1)
    distribution    = ADMSProperty(RADION.distribution, inv=RADION.distributionOf, rng=AssetDistribution)
    keyword         = ADMSProperty(DCAT.keyword, rng=Literal)
    landingPage     = ADMSProperty(DCAT.landingPage, max=1)
    language        = ADMSProperty(DCTERMS.language, max=1)
    related         = ADMSProperty(DCTERMS.relation, rng=URIRef)
    spatial         = ADMSProperty(DCTERMS.spatial, rng=(Country,Place))
    temporal        = ADMSProperty(DCTERMS.temporal)
    logo            = ADMSProperty(FOAF.logo, rng=URIRef)
    # Optional properties
    identifier      = ADMSProperty(ADMS.identifier)
    included        = ADMSProperty(ADMS.includedAsset)
    last            = ADMSProperty(XHV.last, also=ADMS.last, max=1)
    next            = ADMSProperty(XHV.next, also=ADMS.next)
    prev            = ADMSProperty(XHV.prev, also=ADMS.prev)
    sample          = ADMSProperty(ADMS.sample)
    translation     = ADMSProperty(ADMS.translation)
    versionNotes    = ADMSProperty(ADMS.versionNotes, rng=Literal, max=1)
    issued          = ADMSProperty(DCTERMS.created, also=DCTERMS.issued, rng=datetime.datetime, max=1)
    documentation   = ADMSProperty(FOAF.page)
    versionInfo     = ADMSProperty(OWL.versioninfo, rng=Literal)
    altLabel        = ADMSProperty(SKOS.altLabel, rng=Literal)
    describedBy     = ADMSProperty(WRDS.describedBy, max=1)
    metrics         = ADMSProperty(ADMSSW.metrics)

    def __init__(self, uri):
        ADMSResource.__init__(self, uri)

Asset.included.rng = Asset
Asset.last.rng = Asset
Asset.next.rng = Asset
Asset.prev.rng = Asset
Asset.sample.rng = Asset
Asset.translation.rng = Asset


@adms_resource(ADMS.SemanticAssetRepository, also=ADMS.AssetRepository)
class Repository(ADMSResource):

    # Mandatory properties
    accessURL       = ADMSProperty(ADMS.accessURL, also=DCAT.accessURL, rng=URIRef, min=1)
    title           = ADMSProperty(RDFS.label, also=DCTERMS.title, rng=Literal, min=1)
    description     = ADMSProperty(DCTERMS.description, rng=Literal, min=1)
    publisher       = ADMSProperty(DCTERMS.publisher, rng=Publisher, min=1)
    modified        = ADMSProperty(DCTERMS.modified, rng=datetime.datetime, min=1, max=1)
    # Recommended properties
    dataset         = ADMSProperty(also=DCAT.dataset, inv=DCTERMS.isPartOf, rng=Asset)
    contactPoint    = ADMSProperty(DCAT.contactPoint, rng=URIRef)
    themeTaxonomy   = ADMSProperty(DCAT.themeTaxonomy, RADION.themeTaxonomy, rng=Eurovoc)
    spatial         = ADMSProperty(DCTERMS.spatial, rng=(Country,Place))
    # Optional properties
    supportedSchema = ADMSProperty(ADMS.supportedSchema, rng=Asset)
    issued          = ADMSProperty(DCTERMS.created, also=DCTERMS.issued, rng=datetime.datetime, max=1)

    def __init__(self, uri):
        ADMSResource.__init__(self, uri)
