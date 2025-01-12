#
# Makefile for running regression tests on the provided examples.
#
# The examples are executed on small sample files.
# Running make with SUBDIRS set, allows this to be run on
# a subset of subdirectories.
#

TOP_DIR=$(shell readlink -f ..)

# Use small data samples for all data files
export CROSSREF_DIR?=$(TOP_DIR)/tests/data/crossref-sample
export USPTO_DIR?=$(TOP_DIR)/tests/data/uspto-2023-04
export ORCID_SUMMARIES?=$(TOP_DIR)/tests/data/ORCID_2022_10_summaries.tar.gz
export DBLP?=$(TOP_DIR)/tests/data/dblp.xml.gz
export ROR?=$(TOP_DIR)/tests/data/ror.zip
export DOAJ?=$(TOP_DIR)/tests/data/doaj.csv
export JOURNAL_NAMES?=$(TOP_DIR)/tests/data/titleFile.csv
export PUBMED_DIR?=$(TOP_DIR)/tests/data/pubmed-sample
export DATACITE?=$(TOP_DIR)/tests/data/datacite.tar.gz

# Use source code tree implementation
export A3K?=$(TOP_DIR)/bin/a3k

# Do not use Intel Thread Building Blocks library
export TBB?=

# Do not time commands
export TIME?=

# Avoid Python scripts requiring numpy and scipy
export EXPENSIVE_DEPENDENCIES?=true

SUBDIRS?=$(shell find . -mindepth 1 -maxdepth 1 -type d -not -name cdindex \
  -not -name tawfik -not -name cs_cdindex)

.PHONY: all $(SUBDIRS) verify-links clean

all: $(SUBDIRS)

$(SUBDIRS):
	$(MAKE) -C $@

verify-links:
	sed -n 's|.*(\./\([^)]*\).*|\1|p' README.md | xargs ls >/dev/null

clean:
	for dir in $(SUBDIRS); do \
		$(MAKE) -C $$dir clean depclean; \
	done
