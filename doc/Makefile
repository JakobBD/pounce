# "make" builds all

# Switch to build all document parts - or only ready parts
BUILDALL=

SRC=000_documentation.md 100_getting_started.md 200_features.md 300_scheduling.md 400_workflow.md 500_code_design.md 600_implementing.md 999_references.md

# GNU Make can only perform numerical comparison, split and compare by parts
PANDOCVERSION := $(shell pandoc --version | grep ^pandoc | sed 's/^.* //g')
PANDOCMAJOR   := $(shell echo $(PANDOCVERSION) | cut -f1 -d.)
PANDOCMINOR   := $(shell echo $(PANDOCVERSION) | cut -f2 -d.)

# Pandoc changed citeproc in 2.11
PANDOCFILTER:=--filter pandoc-citeproc
ifeq ($(shell expr $(PANDOCMAJOR) \= 2), 1)
ifeq ($(shell expr $(PANDOCMINOR) \>= 11), 1)
PANDOCFILTER:=--citeproc
endif
endif

# Update template to current version if possible
TEMPLATE_INFO := $(shell pandoc -D latex > /dev/null; echo $$?)
ifeq ($(shell expr $(TEMPLATE_INFO) \= 0), 1)
  $(info Found pandoc latex template, using system version)
  $(shell pandoc -D latex > template.tex)
else
  $(info pandoc latex template not found on system, using git version)
endif

all: documentation
	@echo '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'
	@echo ' SUCCESS: DOCUMENTATION GENERATED!'
	@echo '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~'

documentation:
	pandoc $(SRC)   -o documentation.pdf -s -N $(PANDOCFILTER) --from markdown+implicit_figures --bibliography references.bib --listings --template=template.tex

# utility targets

tests:
	pandoc tests.md -o test.pdf      -s -N $(PANDOCFILTER) --from markdown+implicit_figures --bibliography references.bib --listings --template=template.tex

.PHONY: documentation

