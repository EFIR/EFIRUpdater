# Translation utilities
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

from .files import *
import goslate


def translate(text):
    '''Return text translated to english.'''
    # Initialize cache
    if not hasattr(translate, 'cache'):
        translate.filename = os.path.join(CACHE_DIR, "translations.csv")
        translate.translator = goslate.Goslate()
        os.makedirs(os.path.dirname(translate.filename), exist_ok=True)
        if os.path.exists(translate.filename):
            logging.debug("Reading cached translations.")
            with open(translate.filename) as f:
                translate.cache = {row[0]:row[1] for row in csv.reader(f)}
        else:
            translate.cache = {}
    # Translate if not in cache
    if text not in translate.cache:
        logging.debug("Translating %s", text)
        translation = translate.translator.translate(text, 'en')
        with open(translate.filename, 'a') as f:
            csv.writer(f).writerow([text, translation])
        translate.cache[text] = translation
    # Return cached result
    return translate.cache[text]
