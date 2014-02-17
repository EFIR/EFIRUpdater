# Greek Interoperability Catalogue
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
import collections
import mimetypes

BASE_URL = "http://www.yap.gov.gr/e-gif/schemas/current/"

TITLE = "Greek Interoperability Catalogue"
DESCRIPTION = "The Greek Interoperability Catalogue contains assets produced by Greek public administration that can be used for the development of e-government services."

PUBLISHER = Publisher(URIRef("http://www.yap.gov.gr"))
PUBLISHER.name = Literal("Informatics Development Agency, Ministry of Administrative Reform and eGovernance", lang="en")
PUBLISHER.type = PublisherType.NationalAuthority


EGIFSection = collections.namedtuple('EGIFSection',
        ['url', 'asset_type', 'pattern', 'title', 'description'])

SECTIONS = [
    EGIFSection(url = BASE_URL + "BusinessInformationEntities/",
                asset_type = AssetType.Schema,
                pattern = re.compile(r".*/eGIF_(?P<name>[^/_]+)_ABIE-v(?P<version>[0-9-]+)\.xsd$"),
                title = "e-GIF Business Information Entities",
                description = "The approved Business Information Entities of the e-GIF."),
    EGIFSection(url = BASE_URL + "CodeLists/",
                asset_type = AssetType.CodeList,
                pattern = re.compile(r".*/eGIF_(?P<name>[^/_]+)CodeList_v(?P<version>[0-9-]+)\.xsd$"),
                title = "e-GIF Code Lists",
                description = "The Approved CodeLists and Identifier Lists of the e-GIF"),
    EGIFSection(url = BASE_URL + "CoreComponents/",
                asset_type = AssetType.CoreComponent,
                pattern = re.compile(r".*/eGIF_CoreComponents_(?P<name>[^/_]+)-v(?P<version>[0-9-]+)\.xsd$"),
                title = "e-GIF Core Components",
                description = "The Approved list of Core Components of the e-GIF"),
    EGIFSection(url = BASE_URL + "PublicAdministrationDocuments/",
                asset_type = AssetType.Schema,
                pattern = re.compile(r".*/eGIF_(?P<name>[^/_]+)-v(?P<version>[0-9-]+)\.xsd$"),
                title = "e-GIF Public Administration Documents",
                description = "The XML Schemas of the first edition of the e-Government Interoperability Framework")
]


def process_section(repo, section):
    '''Create an asset from section and add it to repo.'''
    logging.debug("Processing section %s", section.url)
    asset = Asset(URIRef(section.url))
    asset.title = Literal(section.title, lang="en")
    asset.description = Literal(section.description, lang="en")
    asset.publisher = repo.publisher
    asset.theme = Eurovoc.term("100223")
    asset.spatial = repo.spatial
    asset.status = Status.Completed
    asset.type = section.asset_type
    asset.interoperabilityLevel = InteroperabilityLevel.Semantic
    asset.distribution = set()
    for url in HTMLPage(section.url).get_child_links():
        m = re.match(section.pattern, url)
        if not m:
            continue
        name, version = m.group('name'), m.group('version')
        name = unquote(name)
        name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
        name = re.sub(r"([A-Z])([A-Z][a-z])", r"\1 \2", name)
        version = version.replace("-", ".")
        d = AssetDistribution(URIRef(url))
        d.accessURL = d.uri
        d.title = Literal(name, lang="en")
        d.modified = get_modified(url)
        d.issued = d.modified
        d.status = asset.status
        d.format = MediaType.term("application/xml")
        d.publisher = repo.publisher
        d.representationTechnique = RepresentationTechnique.XMLSchema
        d.license = UNKNOWN_LICENSE
        asset.distribution.add(d)
        if not asset.version:
            asset.version = version
    asset.modified = max(d.modified for d in asset.distribution)
    repo.dataset.add(asset)


def process_static(repo):
    '''Read data/egif_static.csv and add the assets to repo.'''
    logging.debug("Processing static information.")
    for data in read_csv("static.csv"):
        asset = Asset(URIRef(data['URL']))
        asset.title = Literal(data['Title'], lang="en")
        asset.description = Literal(data['Description'], lang="en")
        asset.publisher = repo.publisher
        asset.modified = datetime.datetime.now(datetime.timezone.utc)  # FIXME
        asset.theme = Eurovoc.term("100223")
        asset.spatial = repo.spatial
        asset.status = Status.Completed
        asset.type = AssetType.Schema
        asset.interoperabilityLevel = InteroperabilityLevel.Semantic
        asset.language = Language.el
        d = AssetDistribution(URIRef(str(asset.uri) + "?type=distribution"))
        d.accessURL = asset.uri
        d.status = asset.status
        d.publisher = asset.publisher
        d.representationTechnique = RepresentationTechnique.HumanLanguage
        d.license = UNKNOWN_LICENSE
        d.issued = asset.modified
        d.modified = d.issued
        mime = mimetypes.guess_type(str(d.accessURL))[0]
        if mime:
            d.format = MediaType.term(mime)
        asset.distribution = d
        repo.dataset.add(asset)


def process():
    repo = Repository(URIRef("http://www.e-gif.gov.gr/"))
    repo.title = Literal(TITLE, lang="en")
    repo.description = Literal(DESCRIPTION, lang="en")
    repo.accessURL = repo.uri
    repo.publisher = PUBLISHER
    repo.spatial = GeoNames.term("390903")
    repo.dataset = set()
    process_static(repo)
    for section in SECTIONS:
        process_section(repo, section)
    repo.modified = max(asset.modified for asset in repo.dataset
                                       if asset.modified)
    return repo
