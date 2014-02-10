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
import re
import collections

NAME = 'egif'
BASE_URL = "http://www.yap.gov.gr/e-gif/schemas/current/"

TITLE = "Greek Interoperability Catalogue"
DESCRIPTION = "The Greek Interoperability Catalogue contains assets produced by Greek public administration that can be used for the development of e-government services."

PUBLISHER = Publisher(URIRef("http://www.yap.gov.gr"))
PUBLISHER.name = Literal("Informatics Development Agency, Ministry of Administrative Reform and eGovernance", lang="en")
PUBLISHER.type = PublisherType.NationalAuthority


EGIFSection = collections.namedtuple('EGIFSection', ['url', 'asset_type',
                                                     'pattern', 'title'])

SECTIONS = [
    EGIFSection(url = BASE_URL + "BusinessInformationEntities/",
                asset_type = AssetType.Schema,
                pattern = re.compile(r".*/eGIF_(?P<name>[^/_]+)_ABIE-v(?P<version>[0-9-]+)\.xsd$"),
                title = "{name} - e-GIF Business Information Entity"),
    EGIFSection(url = BASE_URL + "CodeLists/",
                asset_type = AssetType.CodeList,
                pattern = re.compile(r".*/eGIF_(?P<name>[^/_]+)CodeList_v(?P<version>[0-9-]+)\.xsd$"),
                title = "{name} - e-GIF Code List"),
    EGIFSection(url = BASE_URL + "CoreComponents/",
                asset_type = AssetType.CoreComponent,
                pattern = re.compile(r".*/eGIF_CoreComponents_(?P<name>[^/_]+)_v(?P<version>[0-9-]+)\.xsd$"),
                title = "{name} - e-GIF Core Component"),
    EGIFSection(url = BASE_URL + "PublicAdministrationDocuments/",
                asset_type = AssetType.Schema,
                pattern = re.compile(r".*/eGIF_(?P<name>[^/_]+)-v(?P<version>[0-9-]+)\.xsd$"),
                title = "{name} - e-GIF Document")
]


def process_section(repo, section):
    for url in HTMLPage(NAME, section.url).get_child_links():
        m = re.match(section.pattern, url)
        if not m:
            continue
        name, version = m.group('name'), m.group('version')
        name = unquote(name)
        name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
        name = re.sub(r"([A-Z])([A-Z][a-z])", r"\1 \2", name)
        version = version.replace("-", ".")
        title = section.title.format(name=name, version=version)
        open_data(NAME, url).close()  # get last modification date
        asset = Asset(URIRef(url))
        asset.title = Literal(title, lang="en")
        asset.description = Literal("XSD Schema file for " + title, lang="en")
        asset.modified = get_modified(NAME, url)
        asset.publisher = repo.publisher
        asset.theme = Eurovoc.term("100223")
        asset.spatial = repo.spatial
        asset.status = Status.Completed
        asset.type = section.asset_type
        asset.interoperabilityLevel = InteroperabilityLevel.Semantic
        asset.versionInfo = version
        asset.distribution = AssetDistribution(URIRef(url + "?type=distribution"))
        asset.distribution.accessURL = asset.uri
        asset.distribution.status = asset.status
        asset.distribution.mediaType = MediaType.term("application/xml")
        repo.dataset.add(asset)


def process():
    repo = Repository(URIRef("http://www.e-gif.gov.gr/"))
    repo.title = Literal(TITLE, lang="en")
    repo.description = Literal(DESCRIPTION, lang="en")
    repo.accessURL = repo.uri
    repo.publisher = PUBLISHER
    repo.spatial = GeoNames.term("390903")
    repo.dataset = set()
    for section in SECTIONS:
        process_section(repo, section)
    repo.modified = max(asset.modified for asset in repo.dataset)
    return repo
