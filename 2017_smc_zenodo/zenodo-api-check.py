#!/usr/bin/python
# -*- coding: utf-8 -*-

# note, if you cannot install newer requests, this should run in virtualenv (source py3env/bin/activate ...)!
# with older requests, will get: request() got an unexpected keyword argument 'json' (see https://github.com/jeffwidman/bitbucket-issue-migration/issues/61)

import os, sys
import re
import lxml.html as LH #from lxml import html
from lxml import etree
import json
import requests
# sudo apt-get install python3-pip
# sudo -H pip2 install bibtexparser
# sudo -H pip3 install bibtexparser
import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.customization import convert_to_unicode
from bibtexparser.bparser import BibTexParser
if sys.version_info[0] == 3:
  from urllib.parse import urlsplit, urlunsplit
else:
  from urlparse import urlsplit, urlunsplit
from datetime import datetime
import inspect
from pprint import pprint, pformat

url_base_zenodo = 'https://zenodo.org/'
url_base_zenodo_api = 'https://zenodo.org/api/.'
dir_data = "_DATA_"
ACCESS_TOKEN = "GUudIg6kR1ETIdBVQcAT9U68nebJhPUfjdGR2RqGLtLdFODMdbcy4WvF3w7P" # PersonalNoPublish; but must have the Publish API key here, in order to publish!

# SO:107705; unbuffer for both python 2 and 3; to have this work: python papers-get-smc.py 2>&1 | tee _get.log
buf_arg = 0
if sys.version_info[0] == 3:
  os.environ['PYTHONUNBUFFERED'] = '1'
  buf_arg = 1
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buf_arg)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buf_arg)

# Fix Python 2.x.
try: input = raw_input
except NameError: pass


print("Accessing API...")
r = requests.get('https://zenodo.org/api/deposit/depositions',
                 params={'access_token': ACCESS_TOKEN})
print( "Status: %d; length:%d"%( r.status_code, len(r.json()) ) ) # just 10 entries, even if I have 1050!


#~ print("Getting max 2000 hits from API...")
#~ r = requests.get('https://zenodo.org/api/deposit/depositions',
                  #~ params={'size': 2000,
                          #~ # 'status': 'draft',
                          #~ 'access_token': ACCESS_TOKEN})
#~ print( "Status: %d; length:%d"%( r.status_code, len(r.json()) ) )
#~ # pprint(r.json()) # is huge

print("Getting status: draft hits from API...")
r = requests.get('https://zenodo.org/api/deposit/depositions',
                  params={'size': 2000,
                          'status': 'draft',
                          'access_token': ACCESS_TOKEN})
print( "Status: %d; length:%d"%( r.status_code, len(r.json()) ) )
# getting 73 hits here; even if I have only 65 for SMC
#pprint(r.json())

print("Getting status: draft hits with SMC2017 query from API...")
r = requests.get('https://zenodo.org/api/deposit/depositions',
                  params={'size': 2000,
                          'status': 'draft',
                          #'q': 'communities:"smc"', # seems to work
                          #'q': 'metadata:{conference_acronym:SMC2017}', # nowork, apparently since conference_acronym is not mentioned in https://help.zenodo.org/guides/search/
                          #'q': 'isbn:"978-952-60-3729-5"', # nowork
                          #'q': 'title:"Jazz"', # works
                          #'q': 'title:Jazz', # works
                          #'q': 'related_identifiers.identifier:"978-952-60-3729-5"', # nowork
                          #'q': 'related_identifiers.identifier:"2518-3672"', # nowork
                          #'q': 'related_identifiers.identifier:2518-3672', # nowork
                          #'q': 'related_identifiers.identifier:2518-3672', # nowork
                          # [search: queries for nested fields not possible · Issue #1508 · zenodo/zenodo · GitHub](https://github.com/zenodo/zenodo/issues/1508); still a feature request, so not available!
                          'q': 'SMC2017', # this works! returns 65, as it should
                          'access_token': ACCESS_TOKEN})
print( "Status: %d; length:%d"%( r.status_code, len(r.json()) ) )
#pprint(r.json())
