# OASIS
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
import mimetypes

NAME = 'oasis'
URL = "https://www.oasis-open.org/standards"

TITLE = 'Organization for the Advancement of Structured Information Standards - OASIS'
DESCRIPTION = """OASIS (Organization for the Advancement of Structured Information Standards) is a non-profit consortium that drives the development, convergence and adoption of open standards for the global information society.

OASIS promotes industry consensus and produces worldwide standards for security, Cloud computing, SOA, Web services, the Smart Grid, electronic publishing, emergency management, and other areas. OASIS open standards offer the potential to lower cost, stimulate innovation, grow global markets, and protect the right of free choice of technology. """

PUBLISHER = Publisher(URIRef("https://www.oasis-open.org/org"))
PUBLISHER.name = Literal("OASIS", lang="en")
PUBLISHER.type = PublisherType.NonProfitOrganisation

LICENSE = LicenseDocument(URIRef("https://www.oasis-open.org/policies-guidelines/ipr"))
LICENSE.label = Literal("OASIS Intellectual Property Rights (IPR) Policy", lang="en")
LICENSE.type = LicenceType.NoDerivativeWork


def get_abstract_from_tag(title):
    '''Try to read the abstract following the title tag.'''
    if isinstance(title, str):
        title = title.parent
    while title.name in {'span', 'b', 'i', 'font', 'a'}:
        if title.name == 'a' and 'href' in title.attrs:
            return None
        title = title.parent
    tag = get_next_real_sibling(title)
    titleclass = None
    if title.name == 'p':
        if 'class' not in title.attrs and tag.name == 'p':
            # <p>Abstract:</p>
            # <p>...</p>
            # <p>Status:</p>
            tag = tag.contents[0]
        elif 'class' in title.attrs and len(title['class']) == 1:
            # <p class="Titlepageinfo">Abstract:</p>
            # <p class="Abstract">...</p>
            # <p class="Abstract">...</p>
            # <p class="Titlepageinfo">Status:</p>
            titleclass = title['class'][0]
            if 'class' in tag.attrs and titleclass in tag['class']:
                # <p class="MsoNormal">Abstract:</p>
                # <p class="MsoNormal">...</p>
                # <p class="MsoNormal">Status:</p>
                titleclass = None
                tag = tag.contents[0]
        else:
            return None
    elif title.name == 'div':
        if tag.name == 'div':
            # <div>Abstract:</div>
            # <div>...</div>
            tag = tag.contents[0]
        else:
            return None
    elif title.name == 'dt':
        if tag.name == 'dd':
            # <dt>Abstract:</dt>
            # <dd>...</dd>
            tag = tag.contents[0]
        else:
            return None
    elif is_heading(title):
        # <h2>Abstract</h2>
        # ...
        # <h2>Introduction</h2>
        pass
    else:
        return None
    abstract = ""
    while tag:
        if isinstance(tag, str):
            abstract += " " + tag
        elif is_heading(tag):
            break
        elif titleclass and 'class' in tag.attrs and titleclass in tag['class']:
            break
        elif tag.name == 'p':
            abstract += "\n\n" + tag.text
        else:
            abstract += " " + tag.text
        tag = get_next_real_sibling(tag)
    # Remove spurious whitespaces from abstract
    abstract = abstract.strip().replace("\r\n", "\n")
    abstract = re.sub(r"\n(?!\n)", r" ", abstract)
    abstract = re.sub(r"[ \t]+", r" ", abstract)
    abstract = re.sub(r"\n+", r"\n\n", abstract)
    abstract = re.sub(r"^ +| +$", r"", abstract, flags=re.M)
    return abstract


def get_abstract(url):
    '''Try to fetch the abstract in url.'''
    page = HTMLPage(NAME, url)
    for title in page.find_all(text=re.compile(r"^\s*Abstract:?\s*$")):
        abstract = get_abstract_from_tag(title)
        if abstract:
            return abstract
    return None


def get_date(tag):
    '''Return the date contained in one of the <p> children of tag.'''
    for p in tag.find_all('p'):
        try:
            return datetime.datetime.strptime(p.text.strip(), '%B %Y')
        except ValueError:
            pass
    return None


def get_asset_rows(page):
    '''Return the list of rows corresponding to assets.'''
    table = page.find(class_="node-inner").table
    return table.find_all('tr')[1:]


def get_asset(page, tr):
    '''Generate the asset from row tr.'''
    standard, producer, approved = tr.find_all('td')
    for a in standard.find_all('a', attrs={'name':True}):
        name = a.attrs["name"]
        link = page.find('a', href='#'+name)
        if link:
            title = link.text
            break
    logging.debug("Parsing asset %s.", name)
    asset = Asset(URIRef(URL + '#' + name))
    asset.title = Literal(title, lang="en")
    asset.status = Status.Completed
    asset.modified = get_date(approved)
    asset.versionInfo = re.search(r"([0-9.]*)(?: \(.*\)|: .*)?$", title).group(1)
    asset.language = Language.en
    asset.publisher = PUBLISHER
    asset.theme = Eurovoc.term("100223")
    asset.type = AssetType.Schema
    asset.distribution = set()
    for a in standard.find_all('a'):
        if 'href' not in a.attrs:
            continue
        d = AssetDistribution(URIRef(urljoin(URL, a['href'])))
        d.accessURL = d.uri
        d.status = asset.status
        d.title = Literal(a.text, lang="en")
        d.license = LICENSE
        mime = mimetypes.guess_type(str(d.accessURL))[0]
        if mime:
            d.mediaType = MediaType.term(mime)
        if asset.description is None and mime == "text/html" and \
           not d.uri.endswith(".toc.html"):
            abstract = get_abstract(str(d.uri))
            if abstract:
                asset.description = Literal(abstract, lang="en")
            else:
                logging.warning("No abstract found in %s", d.uri)
        asset.distribution.add(d)
    if asset.description is None:
        asset.description = Literal(standard.p.text, lang="en")
    return asset


def process():
    page = HTMLPage(NAME, URL)
    repo = Repository(URIRef(URL))
    repo.accessURL = URIRef(URL)
    repo.title = Literal(TITLE, lang="en")
    repo.description = Literal(DESCRIPTION, lang="en")
    repo.publisher = PUBLISHER
    repo.modified = get_modified(NAME, URL)
    repo.dataset = {get_asset(page, row) for row in get_asset_rows(page)}
    return repo
