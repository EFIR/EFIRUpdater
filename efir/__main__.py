# Main entry point
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

import logging
import argparse


from . import *

parser = argparse.ArgumentParser(prog="efir")
parser.add_argument('-v', '--verbose', action='store_true',
                    help="be verbose")
parser.add_argument('-l', '--list', action='store_true',
                    help="list known repositories")
parser.add_argument('repository', nargs='?',
                    help="repository to process")
args = parser.parse_args()

logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO,
                    format="[%(asctime)s] %(levelname)s %(message)s")

if args.list:
    for name in sorted(processors.keys()):
        print(name)
    parser.exit(0)

if not args.repository:
    parser.print_help()
    parser.exit(0)

if args.repository not in processors:
    parser.error("Unknown repository")
processors[args.repository].process()
