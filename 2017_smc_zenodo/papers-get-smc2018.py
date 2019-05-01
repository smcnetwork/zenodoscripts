#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import re

import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.customization import convert_to_unicode
import subprocess
import regex # sudo pip2/3 install regex # for detecting unicode capital letters
# Install PyPi regex module and use \p{Lu} class .... \p{Ll} is the category of lowercase letters, while \p{L} comprises all the characters in one of the "Letter" categories (Letter, uppercase; Letter, lowercase; Letter, titlecase; Letter, modifier; and Letter, other).
import inspect, pprint
#import PyPDF2 as pyPdf # sudo pip2/pip3 install pypdf2; 'import pyPdf' does not work for v2 anymore
import copy
import shutil

dir_data = "_DATA_"

# SO:107705; unbuffer for both python 2 and 3; to have this work: python papers-get-smc2018.py 2>&1 | tee _get_2018.log
buf_arg = 0
if sys.version_info[0] == 3:
  os.environ['PYTHONUNBUFFERED'] = '1'
  buf_arg = 1
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buf_arg)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buf_arg)

# NOTE: in SMC2018, there is no webpage to scrape;
# instead, got a zip of individual PDFs, so
# the names etc to create the bibtex have to
# be obtained from the PDFs themselves...

# actually, easier - from the total proceedings, copy/paste
# the table of contents into a "Proceedings_SMC18_TOC.txt" file;
# then parse this file to derive the paper and authors' names
# for the .bib file; then simply associate the individual PDFs in order
# ... since things get messed up doing a manual copy/paste from PDF;
# try to extract using this script and pdftotext? Unfortunately
# pdftotext extracts nothing from this doc...
# ... PyPDF2 can extract, but it still messy - so best to do it manually anyway...

bookprocdir = os.path.abspath("../")
bookprocpdfpath = os.path.join(bookprocdir, "Proceedings_SMC18_ISBN_30082018.pdf")
unzippaperpath = os.path.join(bookprocdir, "PapersSMC2018")
unzippapers = sorted( [f for f in os.listdir(unzippaperpath) if os.path.isfile(os.path.join(unzippaperpath, f))] )
confbdname = "SMC Conference 2018" # conflink[0]
conflink_dir = os.path.join(dir_data, confbdname)
bookproctocpath = os.path.join(conflink_dir, "Proceedings_SMC18_TOC.txt")
print(bookproctocpath)
conflink_year = 2018
confissn = "2518-3672"

# pdf = pyPdf.PdfFileReader(file(bookprocpdfpath, "rb"))
# content = ""
# content += pdf.getPage(6).extractText() + " \n"
# print(content)

# the TOC.txt file has structure:
# first line - paper name; second line - author names; third line - pp info
# all these sections are separated by empty line(s)

# first, double-check manually correctness of TOC vs actual paper titles

# assume first line of TOC.txt is a valid paper name, then scan line by line
# to populate allpapersinfo

allpapersinfo = []

with open(bookproctocpath) as fp:
  cneline = 0 # count of non-empty lines
  prealloc = [None] * 3 # preallocated for the three lines of info in TOC.txt file
  indpapinfo = copy.copy(prealloc) # individual paper info;
  for cnt, line in enumerate(fp):
    line = line.strip()
    if(line):
      cneline += 1
      remcnel = cneline % 3 # remainder of division
      if (remcnel == 1):
        if (indpapinfo != prealloc): # if non-empty indpapinfo, append to allpapersinfo
          allpapersinfo.append(indpapinfo)
        indpapinfo = copy.copy(prealloc) # reset indpap; preallocated
      # individual index: remcnel should change as 1, 2, 3, we need
      # to convert that to indexes 0, 1, 2
      indind = (remcnel-1) if (remcnel != 0) else 2;
      indpapinfo[indind] = line
  # after the final indpapinfo, there is no more reset condition which would add it to allpapersinfo
  # so, perform that add manually here:
  allpapersinfo.append(indpapinfo)

print(len(allpapersinfo))
#pprint.pprint(allpapersinfo)

def printPdfHeadingText(inpath):
  pdfcmd = 'pdftotext -layout -f 1 -l 1 "%s" 2>&1 - | sed "/abstract/Iq"'%( inpath )
  proc = subprocess.Popen(pdfcmd, stdout=subprocess.PIPE, shell=True)
  print(">>>>>>>>>>")
  if sys.version_info[0] == 3:
    pdfheading = proc.stdout.read()
    print(pdfheading.decode('utf-8'))
  else: #python 2
    pdfheading = proc.stdout.read().decode('utf-8')
    print(pdfheading.encode('utf-8'))
  print("<<<<<<<<<<")


thisconfbibdicts = []
thisconfbibsdb = BibDatabase()
thisconfbibsdb.entries = []
bibfile = confbdname + ".bib"
#bibfile = bibfile.replace(" ", "_")
bibfile = os.path.join(conflink_dir, bibfile)

for ind, indpapinfo in enumerate(allpapersinfo):
  icp = ind+1
  confpaperbibentry = {}
  confpaperbibentry['origtitle'] = allpapersinfo[ind][0]
  confpaperbibentry['title'] = confpaperbibentry['origtitle']
  confpaperbibentry['url'] = ""
  confpaperbibentry['numpaperorder'] = "%03d"%(icp)
  confpaperbibentry['origtype'] = "Conference Paper"
  #confpaperbibentry['type'] = "inproceedings" # no dice
  confpaperbibentry['ENTRYTYPE'] = "inproceedings" # this is it
  confpaperbibentry['ID'] = "smc:%s:%s"%(conflink_year, confpaperbibentry['numpaperorder']) # make a numeric id
  confpaperbibentry['author'] = " and ".join( map(str.strip, allpapersinfo[ind][1].split(",")) )
  confpaperbibentry['booktitle'] = "Proceedings of the 15th Sound and Music Computing Conference (SMC2018)"
  confpaperbibentry['pages'] = allpapersinfo[ind][2] #.replace("p.", "")
  confpaperbibentry['issn'] = confissn
  confpaperbibentry['isbn'] = "978-9963-697-30-4"
  confpaperbibentry['year'] = str(conflink_year)
  confpaperbibentry['month'] = "4-7 July"
  confpaperbibentry['editor'] = "Anastasia Georgaki and Areti Andreopoulou"
  confpaperbibentry['venue'] = "Limassol, Cyprus"
  confpaperbibentry['publisher'] = ""
  confpaperbibentry['urlpdf'] = ""
  confpaperbibentry['url'] = ""
  confpaperbibentry['urlhome'] = ""
  confpaperbibentry['urlconf'] = "http://cyprusconferences.org/smc2018/"
  confpaperbibentry['file'] = "smc_%s_%s.pdf"%(conflink_year, confpaperbibentry['numpaperorder'])
  thisconfbibdicts.append(confpaperbibentry)
  thisconfbibsdb.entries.append(confpaperbibentry)

  print("%03d: %s"%(icp, confpaperbibentry['title']))
  print("%03d: %s"%(icp, allpapersinfo[ind][1]))
  print("%03d: %s"%(icp, allpapersinfo[ind][2]))
  origpdfname = unzippapers[ind] if ( ind < len(unzippapers) ) else ""
  origpdfpath = os.path.join( unzippaperpath, unzippapers[ind] )
  newpdfpath = os.path.join( conflink_dir, confpaperbibentry['file'] )
  print("%03d: %s -> %s"%(ind+1, origpdfpath, newpdfpath))
  #printPdfHeadingText( origpdfpath )
  shutil.copy2(origpdfpath, newpdfpath)
  pprint.pprint(confpaperbibentry)
  print("---")

# save bib file
with open(bibfile, 'w') as thebibfile:
  #thebibfile.write(bibwriter.write(thisconfbibsdb)) # may cause UnicodeEncodeError: 'ascii' codec can't encode character u'\xf2' in position 4314: ordinal not in range(128)
  # see https://github.com/sciunto-org/python-bibtexparser/issues/51
  bibtex_str = bibtexparser.dumps(thisconfbibsdb)
  if sys.version_info[0]<3: # python 2
    thebibfile.write(bibtex_str.encode('utf8'))
  else: #python 3
    thebibfile.write(bibtex_str)







"""
Note: the original papers break here:

028: An Xception Residual Recurrent Neural Network for Audio Event Detection and Tagging.
028: Tomas Gajarsky, Hendrik Purwins
028: p.210
028: 27.Gajarsky.pdf
---
029: #nowplaying-RS: A New Benchmark Dataset for Building Context-Aware Music Recommender Systems. *******************
029: Asmita Poddar, Eva Zangerle, Yi-Hsuan Yang
029: p.217
029: 28.Matuszewski.pdf ****************
---
030: Toward a Web of Audio Things.
030: Benjamin Matuszewski, Frédéric Bevilacqua
030: p.225
030: 29.Das.pdf
---

# temporary script to rename the original papers:
# - make them 1-based instead of 0-based (00.Cadoz.pdf -> 01.Cadoz.pdf)
# - make a space for the missing paper (28.Matuszewski.pdf -> 30.Matuszewski.pdf)

pat = re.compile("(\d\d\.)")
for origuzpaper in unzippapers:
  # split at "%02d." of filenames, (keeping the delimiter via capture group in regex), and filtering empty strings from result
  nameparts = list(filter(None, pat.split(origuzpaper)))
  # also do strip of whitespace:
  nameparts = [ x.strip() for x in nameparts ]
  # parse the original file index from filename as integer (removing the last '.' character)
  origfindex = int(nameparts[0][:-1])
  newfindex = 0
  if (origfindex < 28):
    newfindex = origfindex+1;
  else:
    newfindex = origfindex+2;
  newfname = "%02d.%s"%(newfindex, nameparts[1])
  #print(origfindex, newfindex, nameparts)
  # these are full paths, so can use os.rename
  oldfpath = os.path.join(unzippaperpath, origuzpaper)
  newfpath = os.path.join(unzippaperpath, newfname)
  print("%s -> %s"%(oldfpath, newfpath))
  os.rename(oldfpath, newfpath)

# ok, also extracted the missing paper with:
# pdftk ../Proceedings_SMC18_ISBN_30082018.pdf cat 217-224 output ../PapersSMC2018/29.Poddar.pdf

# ok, after all this, now there is another problem later:

066: GTTM Database and Manual Time-span Tree Generation Tool.
066: Masatoshi Hamanaka, Keiji Hirata, Satoshi Tojo
066: p.462
066: 66.Hamanaka.pdf
---
067: CTcomposer: A Music Composition Interface Considering Intra-Composer Consistency and Musical Typicality.
067: Hiromi Nakamura, Tomoyasu Nakano, Satoru Fukayama, Masataka Goto
067: p.468
067: 67.Neuman.pdf *****
---
068: Mapping Pitch Classes And Sound Objects: A Bridge Between Klumpenhouwer Networks And Schaeffer’s TARTYP.
068: Israel Neuman
068: p.476
068: 68.Nishino.pdf
---
069: Unit-generator Graph as a Generator of Lazily Evaluated Audio-vector Trees.
069: Hiroki Nishino
069: p.484
069: 69.Zannos.pdf
---
070: Metric Interweaving in Networked Dance and Music Performance.
070: Ioannis Zannos, Martin Carlé
070: p.492
070: 70.Cavdir.pdf
---
071: The BodyHarp: Designing the Intersection Between the Instrument and the Body.
071: Doga Buse Cavdir, Romain Michon, Ge Wang
071: p.498
071: 71.Gimenes.pdf
---
072: Sonic Crossings with Audience Participation: The Embodied iSound Performance.
072: Marcelo Gimenes
072: p.504
072: 72.Shiraishi.pdf
---
073: HamoKara: A System for Practice of Backing Vocals for Karaoke.
073: Mina Shiraishi, Kozue Ogasawara, Tetsuro Kitahara
073: p.511
073: 73.Michon.pdf
---
074: 3D Printing and Physical Modeling of Musical Instruments: Casting the Net.
074: Romain Michon, John Granzow
074: p.519
074: 74.Apergis.pdf
---
075: Sonoids: Interactive Sound Synthesis Driven by Emergent Social Behaviour in the Sonic Domain.
075: Andreas Apergis, Andreas Floros, Maximos Kaliakatsos-Papakostas
075: p.527
075: 75.Koch.pdf
---
076: Towards Flexible Audio Processing.
076: Thilo Koch, Marcelo Queiroz
076: p.535
076: 76.Freire.pdf

Will need to open and check these manually... actually, looks like in pdfs their authors are fine; tis my list that is a problem?!

for ix in /media/data1/work/aau/smc_proc/PapersSMC2018/*; do echo $ix; echo "****" ;pdftotext -layout -f 1 -l 1 $ix - | sed "/abstract/Iq"; echo "------------------------" ; done | less

Actually, seems that  Nakamura,CTcomposer indeed is not present? But how do they end on same ammount of papers? Ah, turns out my script doesn't output the very last entry?!

Now, more correct:

066: GTTM Database and Manual Time-span Tree Generation Tool.
066: Masatoshi Hamanaka, Keiji Hirata, Satoshi Tojo
066: p.462
066: 66.Hamanaka.pdf
---
067: CTcomposer: A Music Composition Interface Considering Intra-Composer Consistency and Musical Typicality.
067: Hiromi Nakamura, Tomoyasu Nakano, Satoru Fukayama, Masataka Goto
067: p.468
067: 67.Neuman.pdf
---
068: Mapping Pitch Classes And Sound Objects: A Bridge Between Klumpenhouwer Networks And Schaeffer’s TARTYP.
068: Israel Neuman
068: p.476
068: 68.Nishino.pdf
---

# another rename script
# 66.Hamanaka.pdf -> 66.Hamanaka.pdf ; 67.Neuman.pdf -> 68.Neuman.pdf

pat = re.compile("(\d\d\.)")
for origuzpaper in unzippapers:
  # split at "%02d." of filenames, (keeping the delimiter via capture group in regex), and filtering empty strings from result
  nameparts = list(filter(None, pat.split(origuzpaper)))
  # also do strip of whitespace:
  nameparts = [ x.strip() for x in nameparts ]
  # parse the original file index from filename as integer (removing the last '.' character)
  origfindex = int(nameparts[0][:-1])
  newfindex = 0
  if (origfindex < 67):
    newfindex = origfindex;
  else:
    newfindex = origfindex+1;
    newfname = "%02d.%s"%(newfindex, nameparts[1])
    #print(origfindex, newfindex, nameparts)
    # these are full paths, so can use os.rename
    oldfpath = os.path.join(unzippaperpath, origuzpaper)
    newfpath = os.path.join(unzippaperpath, newfname)
    print("%s -> %s"%(oldfpath, newfpath))
    os.rename(oldfpath, newfpath)

pdftk ../Proceedings_SMC18_ISBN_30082018.pdf cat 468-475 output ../PapersSMC2018/67.Nakamura.pdf

"""






