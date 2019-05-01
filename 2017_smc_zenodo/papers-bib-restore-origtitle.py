#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import re

import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.customization import convert_to_unicode
from bibtexparser.bparser import BibTexParser
import subprocess
import inspect, pprint

dir_data = "_DATA_"

buf_arg = 0
if sys.version_info[0] == 3:
  os.environ['PYTHONUNBUFFERED'] = '1'
  buf_arg = 1
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buf_arg)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buf_arg)

# restore a possibly titlecased 'title' field from 'origtitle' in bib file...

subdirs = [ "SMC Conference 2017" ]

tbparser = BibTexParser()
tbparser.homogenize_fields = False  # no dice
tbparser.alt_dict['url'] = 'url'    # this finally prevents change 'url' to 'link'
bibfile = "" # so it is not a local variable
for subdir in subdirs:
  bibfile = os.path.join(dir_data, subdir, "%s.bib"%(subdir))
  print((bibfile, os.path.isfile(bibfile)))
  with open(bibfile) as bibtex_file:
    bibtex_str = bibtex_file.read()
  bib_database = bibtexparser.loads(bibtex_str, tbparser)
  #pprint.pprint(bib_database.entries) # already here,replaces 'url' with 'link'
  confbiblen = len(bib_database.entries)

  for icpbe, confpaperbibentry in enumerate(bib_database.entries):
    report = "%03d: '%s' -> '%s'"%(icpbe, confpaperbibentry['title'], confpaperbibentry['origtitle'] )
    origtitlestr = confpaperbibentry['origtitle']
    confpaperbibentry['title'] = origtitlestr
    bib_database.entries[icpbe] = confpaperbibentry
    if sys.version_info[0] == 3:
      print(report)
    else: #python 2
      print(report.encode('utf-8'))

  with open(bibfile, 'w') as thebibfile:
    bibtex_str = bibtexparser.dumps(bib_database)
    if sys.version_info[0]<3: # python 2
      thebibfile.write(bibtex_str.encode('utf8'))
    else: #python 3
      thebibfile.write(bibtex_str)

print("\nRestored all 'title' fields with 'origtitle' content in bib file: %s."%(bibfile))
print("Note that after this process, 'title' field may be broken into two lines - fix that manually if needed...")