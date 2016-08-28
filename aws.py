#! /usr/bin/python

import fileinput,sys,re,os,magic,tarfile,subprocess,urllib,gzip
# from awsgui import *
from shutil import copy2

def sortargs(filein):
  if filein == '' or len(filein)==1:
     fileintype = 'empty'
  elif os.path.isfile(filein):
     fileintype = 'file'
     filein = os.path.abspath(filein)
  else:
     fileintype = 'eprint'
  return filein, fileintype


def changeworkdir():
    workdir = os.getenv("HOME")+"/temp"
    if not os.path.exists(workdir): 
       os.mkdir(workdir)
    workdir = workdir+"/arxiv"
    if not os.path.exists(workdir): 
       os.mkdir(workdir)
    os.chdir(workdir)
    pdfdir = workdir+"/pdfs"
    if not os.path.exists(pdfdir):
       os.mkdir(pdfdir)
    return workdir
    

def arXivRef(ref):
    ref = ref.replace('arxiv:','')
    if re.search(r'^[a-zA-Z\-]+/\d{7}$',ref):
        type = 'old-style eprint'
    elif re.search(r'^\d{7}$',ref):
        type = 'old-style eprint'
        ref = 'hep-th/' + ref
    elif re.search('^\d{4}\.\d{4,5}$',ref):
        type = 'new-style eprint'
    else:
        type = 'not arXiv'
    return type, ref

def downloadArxiv(filein):
  typeis, ref = arXivRef(filein)
  if typeis=="not arXiv":
        print "argument not of arXiv form or existing file"
        sys.exit(0)
  fileis = os.path.abspath(ref.replace('/','-'))
  urllib.urlretrieve('http://arxiv.org/e-print/' + ref, fileis)
  return fileis

def mimefile(filein):
  m = magic.open(magic.MAGIC_MIME)
  m.load()
  typeis = m.file(filein)
  if re.search('tex',typeis):
    typeis ='tex'
  elif re.search('tar',typeis) or re.search('gzip',typeis):
    print typeis
    typeis ='tar'
  else:
    typeis='unknown'
  m.close()
  return typeis

def tex_files(members):
  texlist = []
  bibexists = False
  bblexists = False
  epsfiles = []
  for file in members:
    ext = os.path.splitext(file)[1]
    if ext == ".tex":
       texlist.append(file)
    if ext == ".bib":
       bibexists = True
    if ext == ".bbl":
       bblexists = True
  #  if ext == ".eps":
  #     epsfiles.append(tarinfo.name)
  # epsfiles [x.name for x in members if os.path.splitext(tarinfo.name)[1] == ".eps"]
  if len(texlist)==0:
    for file in members:
      if mimefile(file)=='tex':
	 texlist.append(file)
  if len(texlist)==1:
    texfile=texlist[0]
    print "one tex file found: "+texfile
  elif len(texlist)>1:
    texfile=texlist[0]
    print "many tex files found. using first of:"
    print texlist
  else:
    print "no texfiles found in gz source file!"
    texfile=""
    sys.exit()
  return texfile, bibexists, bblexists

def addtex(texfile,bibexists,bblexists):
  for line in fileinput.input(texfile, inplace=1):
    if line.startswith('\\documentstyle'):
       line = re.sub('documentstyle', 'documentclass',line)
    if line.startswith('\\documentclass'):
       line = re.sub('1[01]pt', '12pt',line)
       if re.search("\{revtex",line):
	 if not re.search("twocolumn",line):
	   if re.search("\]\{revtex",line):
	     line = re.sub('\]\{revtex', r',twocolumn]{revtex',line)
	   else:
	     line = re.sub('\{revtex', r'[twocolumn]{revtex',line)
    if line.startswith('\\setlength') or line.startswith('\\topmargin') or line.startswith('\\oddsidemargin'):
       line = "% "+line
    if bblexists:
       if re.search(r"end{document}",line):
          bblfile = os.path.splitext(texfile)[0]+".bbl"
          print r"\input{"+bblfile+r"}"
       if line.startswith('\\bibliography'):
	    line = ''
    if line.startswith('\\begin{document}'):
       print r'''
% python insertions for wide screen pdf
\DeclareMathSizes{12}{10}{9}{8}
\setlength{\parindent}{0pt}
\setlength{\parskip}{1ex plus 0.5ex minus 0.2ex}
\def\baselinestretch{1}
\renewcommand{\normalsize}{\fontsize{12}{15}\selectfont}
\usepackage{geometry}
\geometry{twocolumn,papersize={13.07in,7.35in},scale={0.9,0.9},offset=0in,columnsep=0.6in}
\usepackage{epstopdf} %for texlive2009
% end insertions
'''
    print line,
  return

def getfile(filein):
  filein, fileintype = sortargs(filein[1]) # check if arg is: empty, file (absolute path), or eprint
  workdir = changeworkdir() # change to a working directory
  if fileintype == 'eprint':
    print 'downloading source,',
    filein = downloadArxiv(filein) #absolute path
    print 'done:',
    fileintype = 'file'
  elif fileintype == 'file':
    print 'source found on disk:',
  return filein

def main(filein):
  filein=getfile(filein)
  typeis = mimefile(filein)
  if typeis == 'unknown':
    print 'unknown file format'
    sys.exit()
  print typeis+' file.'
  bibexists = False
  bblexists = False
  if typeis=='tar':
    if tarfile.is_tarfile(filein):
      tar = tarfile.open(filein, "r")
      filenames = tar.getnames()
      tar.extractall()
      tar.close()
      texfile, bibexists, bblexists = tex_files(filenames)
      print "bibexists",bibexists
    else:
      zip = gzip.open(filein)
      texfile = filein+'.tex'
      fileout = open(texfile , 'wb')
      content = zip.read()
      fileout.write(content)
      fileout.close()
      zip.close()
    texfile = os.path.abspath(texfile)
    proceed=True
  if typeis=='tex':
    workdir = changeworkdir()
    texfile = os.path.basename(filein)
    if os.path.splitext(texfile)[1]!='.tex': texfile+='.tex'
    copy2(filein,workdir+"/"+texfile)
    proceed=True

  if proceed and not texfile=="":
    addtex(texfile,bibexists,bblexists)
    print "done tex insertions!"
    nul=open(os.devnull, "w")
    pdflatexcmd = "pdflatex --enable-write18 -interaction=batchmode "+texfile  
    print "running pdflatex,",
    returncode=subprocess.call(pdflatexcmd, stdout=nul,stderr=nul,shell=True)
    print "pdflatex,",
    returncode=subprocess.call(pdflatexcmd, stdout=nul,stderr=nul,shell=True)
    if bibexists and not bblexists:
      bibtexcmd = "bibtex "+os.path.splitext(texfile)[0]
      print "bibtex,",
      returncode=subprocess.call(bibtexcmd, stdout=nul,stderr=nul,shell=True)
    print "pdflatex,",
    returncode=subprocess.call(pdflatexcmd, stdout=subprocess.PIPE,stderr=nul,shell=True)
    nul.close()
    pdffile = os.path.abspath(os.path.splitext(texfile)[0]+'.pdf')
    print "done"
  
  copy2(pdffile,"pdfs/")
  subprocess.Popen( [ 'okular',pdffile ])

if __name__ == "__main__":
#  if len(sys.argv) == 1:
#    guiinput()
#  elif len(sys.argv)==2:
    main(sys.argv)
    
