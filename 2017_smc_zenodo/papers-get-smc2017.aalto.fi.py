#!/usr/bin/python
# -*- coding: utf-8 -*-

import os, sys
import re
import lxml.html as LH #from lxml import html
from lxml import etree
import requests
# sudo apt-get install python3-pip
# sudo -H pip2 install bibtexparser
# sudo -H pip3 install bibtexparser
import bibtexparser
from bibtexparser.bwriter import BibTexWriter
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.customization import convert_to_unicode
if sys.version_info[0] == 3:
  from urllib.parse import urlsplit, urlunsplit
else:
  from urlparse import urlsplit, urlunsplit
from titlecase import titlecase
from datetime import datetime
import inspect, pprint


# # #url_smc = 'http://smcnetwork.org/resources/smc_papers'
# # url_base_smc = 'http://smcnetwork.org/resources/'
# url_smc = 'http://smc2017.aalto.fi/proceedings.html'
url_base_smc = 'http://smc2017.aalto.fi/'
url_smc = url_base_smc + 'proceedings.html'

dir_data = "_DATA_"
logfile = open("_get.log",'w')

# SO:107705; unbuffer for both python 2 and 3; to have this work: python papers-get-smc2017.aalto.fi.py 2>&1 | tee _get.log
buf_arg = 0
if sys.version_info[0] == 3:
  os.environ['PYTHONUNBUFFERED'] = '1'
  buf_arg = 1
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', buf_arg)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', buf_arg)

def printlog(formalarg):
  #logfile.write(formalarg + '\n') # nope, capture log from bash with 2>&1 for errors
  print(formalarg)

# Fix Python 2.x.
try: input = raw_input
except NameError: pass


if not os.path.exists(dir_data):
  os.makedirs(dir_data)
  printlog("Created " + dir_data + " directory")
else:
  printlog("Directory " + dir_data + " exists.")


printlog("Parse online data to bib files? [y/n]")
choice = input().lower()
doBibFiles = False
if choice == "y":
  doBibFiles = True

##########

if doBibFiles:
  ts_bibpartstart = datetime.now()

  printlog("\nDownloading conferences...\n")
  allconfsbibdicts = []
  allconfsbibdbs = []
  bibwriter = BibTexWriter()
  bibwriter.indent = '  '     # indent entries with 2 spaces instead of one
  confissn = "2518-3672" # hardcoded, is given on url_smc

  #~ for conflink in [ conflinks[0] ]: # recast to array to properly address tuple element in truncated list
  #~ for conflink in [conflinks[3],conflinks[9],conflinks[2]]:
  #~ for conflink in conflinks:
  conflink = ['SMC Conference 2017', 'http://smc2017.aalto.fi/proceedings.html', 2017, 0]

  printlog("\n *****")
  conflink_dir = os.path.join(dir_data, conflink[0])
  if not os.path.exists(conflink_dir):
    os.makedirs(conflink_dir)
    printlog("Created '" + conflink_dir + "' directory")
  else:
    printlog("Directory '" + conflink_dir + "' exists.")

  conflink_url = conflink[1]
  conflink_year = conflink[2]
  thisconfbibdicts = []
  bibfile = conflink[0] + ".bib"
  #bibfile = bibfile.replace(" ", "_")
  bibfile = os.path.join(conflink_dir, bibfile)
  printlog("Scraping conference page %s , and creating bibtex entries in '%s' ..."%(conflink_url, bibfile))
  thisconfbibsdb = BibDatabase()
  thisconfbibsdb.entries = []

  confpage = requests.get(conflink_url)
  #print(confpage.encoding) # crap, it detects ISO-8859-1, even if the page declares <meta charset="utf-8"> (however, it does so after using unicode characters!)
  # note - to avoid mojibake, now I should use confpage.text instead of confpage.content!
  # https://stackoverflow.com/questions/51956649/
  confpage.encoding = "UTF-8" # MUST have this, so confpage.text will work - works in both python 2 and 3 (but not obvious in python 2 _get.log!)
  confpagetree = LH.fromstring(confpage.text)
  #print(confpagetree.text_content()) # fails in python2
  confpagetree.make_links_absolute(base_url=url_base_smc)
  # # # .view-content > .views-table > tbody:nth-child(2)
  # # confpapers = confpagetree.xpath("//div[@class='view-content']/table[contains(@class, 'views-table')]/tbody/tr")
  # .twelve > p:nth-child(5) > a:nth-child(1)
  # here, only those <p> without a class carry actual papers data
  confpapers = confpagetree.xpath("//div[contains(@class,'twelve')]/p[not(@class)]")
  icp = 0 ; icpdf = 0;
  re_pat_pagenums = re.compile(r"p\.(\d+-\d+)")

  for confpaper in confpapers: #[:10]:
    icp += 1
    # # first td in tr is title, it has <a> inside which contains title and URL
    # #pprint.pprint("%02d "%(icp) + confpaper[0][0].text_content()) #ok
    # here, just the first <a> in the <p> is the link with title;
    # also the url is direct link to the pdf, not to a separate page
    confpapertitlecell = confpaper.xpath("a")[0]
    confpaperbibentry = {}
    confpaperbibentry['origtitle'] = confpapertitlecell.text_content()
    # don't need to fix with titlecase here for 2017, as the titles are proper:
    #confpaperbibentry['title'] = titlecase(confpaperbibentry['origtitle'].lower())
    confpaperbibentry['title'] = confpaperbibentry['origtitle']
    confpaperbibentry['url'] = confpapertitlecell.attrib['href']
    confpaperbibentry['numpaperorder'] = "%03d"%(icp)
    # # second td is multiple <a> links with authors, but with short names
    # # better to scrape each paper's HTML page, it has authors full names
    # here, author names are in the only <i> child of the <p> - see below
    confpapertitlecell = confpaper.xpath("a")[0]

    # # this was needed previously, when url was a HTML page with the PDF on it - not like that here
    # confpaperpage = requests.get(confpaperbibentry['url'])
    # confpaperpagetree = LH.fromstring(confpaperpage.content)
    # confpaperpagetree.make_links_absolute(base_url=url_base_smc)

    # this now is "type" "Conference paper" (so @inproceedings+booktitle?)
    confpaperbibentry['origtype'] = "Conference Paper"
    #confpaperbibentry['type'] = "inproceedings" # no dice
    confpaperbibentry['ENTRYTYPE'] = "inproceedings" # this is it
    confpaperbibentry['ID'] = "smc:%s:%s"%(conflink_year, confpaperbibentry['numpaperorder']) # make a numeric id

    # # # here select only the <a> child nodes - each of them has the full author name
    # # confpaperauthors = confpaperpagetree.xpath("//div[@class='biblio_authors']/a")
    # here, author names are in the only <i> child of the <p>
    confpaperauthors = confpaper.xpath("i")[0]

    # # extract only the names via generator expression
    # confpaperauthors = [ cpauthor.text_content() for cpauthor in confpaperauthors ]
    confpaperauthors = confpaperauthors.text_content()
    confpaperauthors = confpaperauthors.split(", ")
    # concatenate names with "and", as per bibtex
    confpaperbibentry['author'] = " and ".join(confpaperauthors)

    # this now is: "Proceedings of the Sound and Music Computing Conference 2016, SMC 2016, Hamburg, Germany (2016)"
    # actually, the format is widely different, and sometimes even plain wrong
    # so booktitle will have to be manually edited
    # however, for 2013 and 2012, there are also page numbers embedded here as p.05-10...
    # however, one of those uses en-dash instead of minus, so handle that too
    confpaperbibentry['booktitle'] = "Proceedings of the 14th Sound and Music Computing Conference (SMC2017)"
    respn = re_pat_pagenums.findall(confpaperbibentry['booktitle'])
    if respn:
      confpaperbibentry['pages'] = respn[0]
      # also delete from string
      confpaperbibentry['booktitle'] = re_pat_pagenums.sub("", confpaperbibentry['booktitle'])
    else: confpaperbibentry['pages'] = ""
    confpaperbibentry['issn'] = confissn
    # # now the ISBN - a bit tricky
    # confpaperbibentry['isbn'] = confpaperpagetree.xpath("//h3[text()='ISBN:']/following-sibling::text()[1]")
    confpaperbibentry['isbn'] = "978-952-60-3729-5"
    #if confpaperbibentry['isbn']: # only handle if it is present:
    #  confpaperbibentry['isbn'] = confpaperbibentry['isbn'][0].strip()
    #else:
    #  confpaperbibentry['isbn'] = ""
    confpaperbibentry['year'] = str(conflink_year)
    confpaperbibentry['month'] = ""
    confpaperbibentry['editor'] = ""
    confpaperbibentry['venue'] = ""
    confpaperbibentry['publisher'] = ""
    # this is the URL on the author home page, which is given on the paper page confpaperbibentry['url']:
    # not present here, but keep for consistency w/ previous bibs
    confpaperbibentry['urlhome'] = "" #confpaperpagetree.xpath("//h3[text()='URL:']/following::a[1]") #[0].attrib['href']
    if confpaperbibentry['urlhome']: # only handle if it is present:
      confpaperbibentry['urlhome'] = confpaperbibentry['urlhome'][0].attrib['href']
    else:
      confpaperbibentry['urlhome'] = ""
    confpaperbibentry['urlpdf'] = confpaperbibentry['url'] #confpaperpagetree.xpath("//table[@id='attachments']/tbody/tr/td[1]/a")
    #if confpaperbibentry['urlpdf']: # only handle if it is present:
    #  confpaperbibentry['urlpdf'] = confpaperbibentry['urlpdf'][0].attrib['href']
    #else:
    #  confpaperbibentry['urlpdf'] = ""
    # for older proceedings, urlpdf is "" and urlhome is actually the pdf link; check for this and replace:
    if ( (confpaperbibentry['urlpdf'] == "") and (".pdf" in confpaperbibentry['urlhome']) ):
      confpaperbibentry['urlpdf'] = confpaperbibentry['urlhome']
      confpaperbibentry['urlhome'] = ""
    if (".pdf" in confpaperbibentry['urlpdf']):
      icpdf += 1
      confpaperbibentry['file'] = "smc_%s_%s.pdf"%(conflink_year, confpaperbibentry['numpaperorder']) # for JabRef, and local PDF names
    else: confpaperbibentry['file'] = ""
    thisconfbibdicts.append(confpaperbibentry)
    thisconfbibsdb.entries.append(confpaperbibentry)
    pprint.pprint(confpaperbibentry)

  # found papers, and found PDFs
  conflink.append(icp)
  conflink.append(icpdf)
  #conflinks[ conflink[3] ] = conflink # save/update the modified conflink!
  # save bib file
  with open(bibfile, 'w') as thebibfile:
    #thebibfile.write(bibwriter.write(thisconfbibsdb)) # may cause UnicodeEncodeError: 'ascii' codec can't encode character u'\xf2' in position 4314: ordinal not in range(128)
    # see https://github.com/sciunto-org/python-bibtexparser/issues/51
    bibtex_str = bibtexparser.dumps(thisconfbibsdb)
    if sys.version_info[0]<3: # python 2
      thebibfile.write(bibtex_str.encode('utf8'))
    else: #python 3
      thebibfile.write(bibtex_str)
  allconfsbibdicts.append(thisconfbibdicts)
  allconfsbibdbs.append(thisconfbibsdb)

  printlog("Report: Conference year - found papers/found PDFs:")
  foundptotal = 0; foundpdftotal = 0;
  #for conflink in conflinks:
  if len(conflink)==4: #short
    fp, fpdf = "0", "0"
  else:
    fp, fpdf = conflink[4], conflink[5]
  printlog( "> %s - %s/%s"%(conflink[2], fp, fpdf) )
  foundptotal += int(fp)
  foundpdftotal += int(fpdf)
  printlog("Total: %s/%s"%(foundptotal,foundpdftotal))

  ts_bibpartend = datetime.now()
  printlog("Script bib part start: %s ; end: %s ; duration: %s"%(ts_bibpartstart.strftime("%Y-%m-%d %H:%M:%S"), ts_bibpartend.strftime("%Y-%m-%d %H:%M:%S"), str(ts_bibpartend-ts_bibpartstart)))


printlog("Download online PDFs? [y/n]")
choice = input().lower()
doPdfFiles = False
if choice == "y":
  doPdfFiles = True

# read the .bib files here, so this part can run independent
# else have to wait for 7 mins for the allconfsbibdicts to be reconstructed...
if doPdfFiles:
  ts_pdfpartstart = datetime.now()

  conflink = ['SMC Conference 2017', 'http://smc2017.aalto.fi/proceedings.html', 2017, 0]

  conflink_dir = os.path.join(dir_data, conflink[0])
  #thisconfbibdicts = allconfsbibdicts[cidx]
  #for confpaperbibentry in thisconfbibdicts:
  bibfile = conflink[0] + ".bib"
  bibfile = os.path.join(conflink_dir, bibfile)
  printlog("\n"+bibfile)
  #with open(bibfile) as bibtex_file:
  #  bibtex_str = bibtex_file.read()
  #bib_database = bibtexparser.loads(bibtex_str)
  with open(bibfile) as bibtex_file:
    print(bibfile, bibtex_file)
    bib_database = bibtexparser.load(bibtex_file)
  for confpaperbibentry in bib_database.entries:
    if (".pdf" in confpaperbibentry['urlpdf']):
      printlog("%s : %s"%(confpaperbibentry['file'], confpaperbibentry['urlpdf']))
      localfpath = os.path.join(conflink_dir, confpaperbibentry['file'])
      dl = 0
      with open(localfpath, "wb") as f:
        #print "Downloading %s" % file_name
        response = requests.get(confpaperbibentry['urlpdf'], stream=True)
        total_length = response.headers.get('content-length')
        if total_length is None: # no content length header
          #f.write(response.content)
          for data in response.iter_content(chunk_size=32768):#4096):
            dl += len(data)
            f.write(data)
            sys.stdout.write(".")
            sys.stdout.flush()
        else:
          total_length = int(total_length)
          for data in response.iter_content(chunk_size=32768):#4096):
            dl += len(data)
            f.write(data)
            done = int(50 * dl / total_length)
            #sys.stdout.write("\r[%s%s]" % ('=' * done, ' ' * (50-done)) )
            sys.stdout.write("=")
            sys.stdout.flush()
    printlog(" got %d bytes."%(dl))
  ts_pdfpartend = datetime.now()
  printlog("Script pdf part start: %s ; end: %s ; duration: %s"%(ts_pdfpartstart.strftime("%Y-%m-%d %H:%M:%S"), ts_pdfpartend.strftime("%Y-%m-%d %H:%M:%S"), str(ts_pdfpartend-ts_pdfpartstart)))

printlog("Done getting .bib info for all conferences. Check and edit the .bibs manually")
logfile.close()
