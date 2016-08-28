# arxiv-wide-screen
View PDFs from the arXiv in your preferred screen ratio.

## Description
Are you an academic who needs to read many articles onscreen today, without scrolling up and down trying to revisit what you just read? Or perhaps you want to enjoy reading articles on your non-A4 size tablet at last? Then this python script is for you.

The script will download the tex file (or gz archive), find the master file, remove/insert latex directives unsing regular expressions, and finally... `pdflatex` you a new pdf article. Simply execute something like
    python aws.py 1603.04216
or similar. Note that the working directory is hard wired but this is easy to change, as are the regular expressions. 

## Alternatives
It will work well for most articles, but not for harvmac or when the source has lots of tex primitives. You may want to check out k2pdfopt that crops and rearranges PDFs, or krop and briss where you crop PDFs manually. These methods though are lossy: no hyperlinks, OCR, resolution.
