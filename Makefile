# Makefile in logtools directory
#
# Added to assist with some maintenance tasks
#
# ----------------------------------------------------------------------
#
.PHONY: clean showMd

clean:
	- rm -fr logtools/__pycache__
	- rm logtools/*.pyc

showMd:
	grip -b README.md

