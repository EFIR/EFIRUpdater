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


def get_description(url):
    '''Try to fetch the abstract in url for use as a description.'''
    page = HTMLPage(NAME, url)
    abstract = page.get_section_text("Abstract", stop=["Status", "Notices"])
    if abstract:
        return Literal(abstract, lang="en")
    else:
        logging.warning("No abstract found in %s", url)
        return None


def get_date(tag):
    '''Return the date contained in one of the <p> children of tag.'''
    for p in tag.find_all('p'):
        try:
            return datetime.datetime.strptime(p.text.strip(), '%B %Y')
        except ValueError:
            pass
    return None


def get_distribution_name(a):
    '''Return the guessed distribution name of link a.'''
    # Find outermost tag containing only this link
    tag = a
    while tag.name not in {'li', 'td'} and \
          len(tag.parent.find_all('a', href=True)) < 2:
        tag = tag.parent
    # Three words or more, or part of sentence, or filename: this is the name
    name = clean_text(a.text, oneline=True)
    if len(name.split()) > 2 or \
       (tag != a and isinstance(get_next_real_sibling(a), str) and \
                     isinstance(get_previous_real_sibling(a), str)) or \
       (len(name.split()) == 1 and name != "ASN.1" and ('.' in name or '-' in name)):
        return clean_text(tag.text, oneline=True)
    # Otherwise: attach to previous text
    while tag.name != 'td':
        tag = tag.parent
    text = None
    for s in tag.strings:
        if s.parent == a:
            break
        ss = s.strip()
        if ss not in {'', '/'} and \
           (s.parent.name != 'a' or 'href' not in s.parent.attrs):
            text = s
    else:
        assert False
    if text:
        text = clean_text(text, oneline=True)
        if text.endswith(':'):
            return text + " " + name
        else:
            return text + " (" + name + ")"
    else:
        return name


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
    for a in standard.find_all('a', href=True):
        d = AssetDistribution(URIRef(urljoin(URL, a['href'])))
        d.accessURL = d.uri
        d.status = asset.status
        d.title = Literal(get_distribution_name(a), lang="en")
        d.license = LICENSE
        mime = mimetypes.guess_type(str(d.accessURL))[0]
        if mime:
            d.mediaType = MediaType.term(mime)
        if asset.description is None and mime == "text/html" and \
           not d.uri.endswith(".toc.html"):
            asset.description = get_description(str(d.uri))
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
