########################################################################
#
# Makefile template for Document Format Conversion - pandoc
#
# Copyright 2018 (c) Graham.Williams@togaware.com
#
# License: Creative Commons Attribution-ShareAlike 4.0 International.
#
########################################################################

########################################################################
# GLOBAL VARIABLES
#
# I think the geometry for LaTeX should be a4 rather than a4paper to
# work with newer LaTeX. Should only need lang which pandoc should
# underneath also set babel-lang but that does not seem to be working
# 20171230 (reference man page).

PANDOC_PDF_OPTIONS=-V urlcolor=cyan -V geometry=a4paper -V lang=en-AU -V babel-lang=british --number-sections

PANDOC_TEX_OPTIONS=$(PANDOC_PDF_OPTIONS) --standalone --template eisvogel --listings

PANDOC_CSS=pandoc.css

PANDOC_HTML_OPTIONS=--standalone --self-contained
ifneq ("$(wildcard ../$(PANDOC_CSS))","")
  PANDOC_HTML_OPTIONS := $(PANDOC_HTML_OPTIONS) --include-in-header=../$(PANDOC_CSS)
endif
ifneq ("$(wildcard $(PANDOC_CSS))","")
  PANDOC_HTML_OPTIONS := $(PANDOC_HTML_OPTIONS) --include-in-header=$(PANDOC_CSS)
endif

########################################################################
# HELP

define PANDOC_HELP
PanDoc:

  Input:
    org   Emacs org mode (the original).
    rst   Attempt to improve markdown.
    md    Mardown documents.

  Output:
    txt   Plain text file with duplicate empty lines removed.
    md	  Markdown.
    docx  Microsoft Word.
    html
    tex	  LaTeX.
    pdf

  Example:

    $ make README.pdf  # Generate .pdf from .org.

  Default conversion options:

    PDF:  $(PANDOC_PDF_OPTIONS)
    TEX:  $(PANDOC_TEX_OPTIONS)
    HTML: $(PANDOC_HTML_OPTIONS)

endef
export PANDOC_HELP

help::
	@echo "$$PANDOC_HELP"

########################################################################
# RULES

%.txt: %.rst
	pandoc -t plain $< | perl -00pe0 > $@

%.txt: %.md
	pandoc -t plain $< | perl -00pe0 > $@

%.md: %.rst
	pandoc $< -o $@

%.docx: %.org
	pandoc $(PANDOC_PDF_OPTIONS) $< -o $@

%.html: %.org
	pandoc -o $@ $<

%.html: %.rst
	pandoc $(PANDOC_HTML_OPTIONS) -o $@ $<
ifneq ("$(HTML_MSG)","")
	sed -i -e "s|</body>|$(HTML_MSG)\n</body>|g" $@
endif

%.html: %.md
	pandoc $(PANDOC_HTML_OPTIONS) -o $@ $<

%.md: %.rst
	pandoc $< -o $@

%.md: %.ipynb
	jupyter nbconvert --to markdown $< --stdout > $@

#	notedown $< --to markdown --strip > $@

%.R: %.ipynb
	jupyter-nbconvert --to python $< --stdout > $@

%.py: %.ipynb
	jupyter-nbconvert --to python $< --stdout > $@

%.txt: %.rst
	pandoc -t plain $< | perl -00pe0 > $@

%.txt: %.md
	pandoc -t plain $< | perl -00pe0 $@

%.tex: %.org
	pandoc $(PANDOC_TEX_OPTIONS) $< -o $@

%.tex: %.md
	pandoc $(PANDOC_TEX_OPTIONS) $< -o $@

%.tex: %.rst
	pandoc $(PANDOC_TEX_OPTIONS) $< -o $@

%.pdf: %.org
	pandoc $(PANDOC_PDF_OPTIONS) $< -o $@

%.pdf: %.rst
	pandoc $(PANDOC_PDF_OPTIONS) $< -o $@

%.pdf: %.md
	pandoc $(PANDOC_TEX_OPTIONS) $< -o $@

%.pdf: %.Rmd
	Rscript -e "rmarkdown::render('$^', 'pdf_document')"
