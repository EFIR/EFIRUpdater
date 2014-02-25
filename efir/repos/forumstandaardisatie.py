# Dutch Standardisation Forum - "Comply or explain"-standards
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
import mimetypes

URL = "https://lijsten.forumstandaardisatie.nl/lijsten/open-standaarden"

TITLE = 'Dutch Standardisation Forum - "Comply or explain"-standards'
TITLE_NL = 'Forum Standaardisatie - "Pas toe of leg uit"-standaarden'
DESCRIPTION = """The goal of the Dutch government policy on open standards is to promote interoperability of the Dutch public and semi-public sectors, while at the same time ensuring provider independence. Interoperability means the ability to exchange data electronically; in this case between government bodies and businesses, between government bodies and civilians, and between government bodies. In order to attain this goal, the Standardisation Forum and Board were established in 2006. These institutions do not develop standards, but can assign a status (required or recommended) to existing standards in the public and semi-public sector. The Board and Forum maintain the following two lists: 1) List of open standards for which a ‘Comply or Explain’-regime is in place. 2) List of recommended common open standards. Inclusion in the 'Comply or Explain' list means that the Board members have committed to use the standard within their own organisation, and at the same time call upon third parties to also use the standard. Inclusion in the list also means that all government bodies and semi-government bodies are required to adjust their procurement process to the list. When organisations procure an ICT service or product, they are required to choose one of the applicable open standards from the 'Comply or Explain' list ('comply'). Only if this leads to insurmountable problems, may an organisation choose otherwise. However, in this case the annual report must give account of why the different choice was made ('explain'). The 'Comply or Explain' policy is embedded in decree and government agreements. Anyone can submit a standard for inclusion in one of the lists. The standard goes through an assessment procedure during which, based on the consideration criteria and substantive criteria, is determined for which list the standard qualifies, and whether the standard should be included.The assessment of open standards for inclusion in one of the lists is based on an assessment framework. Firstly, it is assessed whether a submitted standard falls within the scope of the lists, based on the consideration criteria. Only if the corresponding questions are answered positively, will the standard qualify for assessment according to the four substantive criteria. The target group for the lists consist of the entire public and semi-public sectors. In addition to government departments, implementing bodies, provinces, district water boards and municipalities, this includes education, healthcare and social security institutions. (function=inform). This repository contains all standards from the 'Comply or Explain' list ("pas toe of leg uit"-lijst)."""

PUBLISHER = Publisher(URIRef("http://www.forumstandaardisatie.nl/organisatie"))
PUBLISHER.name = Literal("Forumstandaardisatie.nl", lang="en")
PUBLISHER.type = PublisherType.NationalAuthority

DESCRIPTIONS = {URIRef(data["URI"]):data["Description"]
                for data in read_csv("descriptions.csv")}

URL_FIXES = {}
for data in read_csv("urlfixes.csv"):
    urifrom, urito = URIRef(data["From"]), URIRef(data["To"])
    if urifrom not in URL_FIXES:
        URL_FIXES[urifrom] = set()
    URL_FIXES[urifrom].add(urito)


def get_asset_uris():
    '''Yield the URIRefs of all assets.'''
    home = HTMLPage(URL)
    table = home.find('table', summary="overzichtstabel")
    for tr in table.tbody.find_all('tr'):
        yield URIRef(urljoin(URL, tr.a['href']))


def get_items(page, name):
    '''Return the contents of the field named name on the HTMLPage page.
    The fields are formatted as follows on the page:
        <div class="field-field-name">
          <div class="field-label">...</div>
          <div class="field-items">
            <div class="field-item odd">...</div>
            <div class="field-item even">...</div>
            ...
          </div>
        </div>
    The result is a list of items (the field-item tags).
    '''
    div = page.find(class_="field-field-"+name)
    if div is None:
        return []
    return div.find_all(class_="field-item")


def get_text(page, name):
    '''Return a list of text values for field named name on page.'''
    return [html_to_plain(item) for item in get_items(page, name)]


def get_fulltext(page, name):
    '''Return the text value of field named name on page.'''
    return "\n".join(get_text(page, name))


def get_uris(page, name):
    '''Return the set of URI values of field named name on page.'''
    return set(URIRef(urljoin(URL, a['href']))
               for item in get_items(page, name)
               for a in item.find_all('a'))


def get_date(page, name):
    '''Return the datetime value of field named name on page.'''
    items = get_items(page, name)
    if not items:
        return None
    if len(items) > 1:
        logging.warning("Ignoring other date items for field %s.", name)
    item = items[0]
    if not item.span:
        logging.warning("Invalid date: %s.", item)
        return None
    text = item.span.text
    try:
        return datetime.datetime.strptime(text + " +0000", "%d/%m/%Y %z")
    except ValueError:
        logging.warning("Invalid date: %s.", text)
        return None


def get_asset(uri):
    '''Generate the asset with URI uri.'''
    logging.debug("Parsing asset %s.", uri)
    page = HTMLPage(str(uri))
    asset = Asset(uri)
    title = ", ".join(line.strip("* ")
                      for line in get_fulltext(page, "full-name").split("\n")
                      if line.strip("* "))
    asset.title = Literal(title, lang="en")
    asset.altLabel = Literal(page.find(class_="title").text.strip(), lang="en")
    description_nl = get_fulltext(page, "beschrijving")
    if uri in DESCRIPTIONS:
        description_en = DESCRIPTIONS[uri]
    else:
        description_en = translate(description_nl)
    asset.description = {Literal(description_nl, lang="nl"),
                         Literal(description_en, lang="en")}
    asset.status = Status.Completed
    asset.modified = get_date(page, "datum-opname") or get_modified(str(uri))
    asset.version = set(Literal(text, lang="en")
                        for text in get_text(page, "version") if text != "-")
    asset.language = Language.nl
    asset.publisher = PUBLISHER
    asset.type = AssetType.TechnicalInteropabilityAgreement
    asset.theme = Eurovoc.term("100223")
    asset.interoperabilityLevel = set()
    for level in get_text(page, "interoperabiliteitsniveau"):
        if level == "Process":
            asset.interoperabilityLevel.add(InteroperabilityLevel.Organisational)
        elif level.startswith("Techniek"):
            asset.interoperabilityLevel.add(InteroperabilityLevel.Technical)
        elif level.startswith("Betekenis") or level.startswith("Structuur"):
            asset.interoperabilityLevel.add(InteroperabilityLevel.Semantic)
    asset.related = get_uris(page, "relation")
    uris = set()
    for uri in get_uris(page, "specificatie"):
        if uri in URL_FIXES:
            uris |= URL_FIXES[uri]
        else:
            uris.add(uri)
    asset.distribution = set()
    for uri in uris:
        d = AssetDistribution(uri)
        d.accessURL = uri
        d.status = asset.status
        d.publisher = PUBLISHER
        d.issued = asset.modified
        d.modified = asset.modified
        d.title = asset.title
        d.license = UNKNOWN_LICENSE
        mime = mimetypes.guess_type(str(d.accessURL))[0]
        if mime:
            d.format = MediaType.term(mime)
        else:
            d.format = MediaType.term("text/html")
        asset.distribution.add(d)
    return asset


def process():
    repo = Repository(URIRef(URL))
    repo.accessURL = URIRef(URL)
    repo.title = {Literal(TITLE, lang="en"), Literal(TITLE_NL, lang="nl")}
    repo.description = Literal(DESCRIPTION, lang="en")
    repo.modified = get_modified(URL)
    repo.spatial = GeoNames.term("2750405")
    repo.dataset = {get_asset(uri) for uri in get_asset_uris()}
    repo.dataset.update(get_asset(URIRef(data["URI"]))
                        for data in read_csv("additional_assets.csv"))
    repo.publisher = PUBLISHER
    return repo
