EFIR Update Scripts
====================

This repository contains update scripts for the
[European Federated Interoperability Repository][EFIR] (EFIR),
available on the Joinup platform.

[EFIR]: https://joinup.ec.europa.eu/catalogue/repository


Prerequisites
--------------

You will need a [Python][] 3.3 or later interpreter with the following
additional modules:

* [rdflib][] 4
* [isodate][]
* [BeautifulSoup 4][]
* [lxml][]
* [html5lib][]
* [goslate][]

[Python]: http://python.org/
[rdflib]: https://pypi.python.org/pypi/rdflib
[isodate]: https://pypi.python.org/pypi/isodate
[BeautifulSoup 4]: https://pypi.python.org/pypi/beautifulsoup4
[lxml]: https://pypi.python.org/pypi/lxml
[html5lib]: https://pypi.python.org/pypi/html5lib
[goslate]: https://pypi.python.org/pypi/goslate


Usage
------

Run the following command in the root of the repository to get the usage notice.

    python -m efir -h

*Note: all commands shall be executed from the root of the repository.*


Licence
--------

Copyright 2014 PwC EU Services

Licensed under the EUPL, Version 1.1 or - as soon they
will be approved by the European Commission - subsequent
versions of the EUPL (the "Licence");
You may not use this work except in compliance with the
Licence.
You may obtain a copy of the Licence at:
<http://ec.europa.eu/idabc/eupl>

Unless required by applicable law or agreed to in
writing, software distributed under the Licence is
distributed on an "AS IS" basis,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either
express or implied.
See the Licence for the specific language governing
permissions and limitations under the Licence.
