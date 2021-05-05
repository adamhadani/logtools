# Makefile in logtools directory
#
# Added to assist with some maintenance tasks
#
# ----------------------------------------------------------------------
#

#
# Assist with building table of contents in Markdown
#
PYTHON= python3
MD-TOC-PGM= $(PYTHON) -m md_toc --in-place
MD-TOC-OPTIONS= github

MARKDOWNFILES=$(wildcard *.md)



.PHONY: clean showMd

clean:
	- rm -fr logtools/__pycache__
	- rm logtools/*.pyc

showMd:
	grip -b README.md



#
# Build table of contents in Markdown
#

.PHONY: md-tocs
md-tocs: $(MARKDOWNFILES)
	$(MD-TOC-PGM) $(MD-TOC-OPTIONS) $?

#
# Generate html documentation
#
.PHONY: doxy
doxy:
	doxygen aux/logtools.doxyfile
