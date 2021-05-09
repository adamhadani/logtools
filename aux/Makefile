# Makefile in logtools/aux directory
#
# Added to assist with some maintenance tasks
#
# ----------------------------------------------------------------------
#

#
# Assist with building table of contents in Markdown
#
SHELL= /bin/bash
PYTHON= python3

PYDIR= ../logtools

MARKDOWNFILES=$(wildcard *.md)


#
# Generate UML with pyreverse
#
.PHONY: doUML 

doUML:
	pyreverse $(PYDIR)
	echo HOU
	for f in classes.dot packages.dot ; \
	    do  \
	      echo $f ; \
	      if [ -f $$f ] ; \
	         then \
	            pyreversePlus --in $$f --out UML$$f --add UMLDetails.add; \
	            ddot UML$$f; \
	         else \
	            echo  $$f not found  ; \
	      fi ; \
	    done
