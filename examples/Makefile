#
# Makefile for running regression tests on the provided examples.
#
# The examples are executed on small sample files.
# Running make with SUBDIRS set, allows this to be run on
# a subset of subdirectories.
#

TOP_DIR=$(shell pwd)/..
export CROSSREF_DIR?=$(TOP_DIR)/tests/data/sample
export ORCID_SUMMARIES?=$(TOP_DIR)/tests/data/ORCID_2022_10_summaries.tar.gz
export DBLP?=$(TOP_DIR)/tests/data/dblp.xml.gz
export ROR?=$(TOP_DIR)/tests/data/ror.zip
export A3K?=$(TOP_DIR)/bin/a3k
export TBB?=
export TIME=

# This is set to avoid Python scripts requiring numpy and scipy
export EXPENSIVE_DEPENDENCIES = true

SUBDIRS?=$(shell find . -mindepth 1 -maxdepth 1 -type d)

.PHONY: subdirs $(SUBDIRS)

subdirs: $(SUBDIRS)

$(SUBDIRS):
	$(MAKE) -C $@
