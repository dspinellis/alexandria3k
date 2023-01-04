#
# Common rules and functionality for all analysis tasks
#

export RDBMS?=sqlite
# TODO: Set MAINDB
export ROLAPDB?=rolap

CROSSREF_DIR?=../common/Crossref-April-2022
ORCID_SUMMARIES?=../common/ORCID_2022_10_summaries.tar.gz

V?=1
TIME?=time
export SQLITE_TMPDIR?=.

include simple-rolap/Makefile

$(CROSSREF_DIR):
	cd ../common && \
	aria2c https://doi.org/10.13003/83b2gq && \
	mv 'April 2022 Public Data File from Crossref' Crossref-April-2022

$(ORCID_SUMMARIES):
	curl -L https://orcid.figshare.com/ndownloader/files/37635374 >$@

# TODO: Add rule in including Makefile to populate database with required data

asjcs: populate
	$(TIME) alexandria3k --data-source ASJC --populate "$(MAINDB).db"
	touch $@

link-works-asjcs: asjcs populate
	$(TIME) alexandria3k --execute link-works-asjcs \
	  --populate "$(MAINDB).db"
	touch $@

rors: populate
	$(TIME) alexandria3k --data-source ROR ../common/ror-v1.17.1-2022-12-16.zip --populate "$(MAINDB).db"
	touch $@

link-aa-base-ror: rors populate
	$(TIME) alexandria3k --execute link-aa-base-ror \
	  --populate "$(MAINDB).db"
	touch $@

link-aa-top-ror: rors populate
	$(TIME) alexandria3k --execute link-aa-top-ror \
	  --populate "$(MAINDB).db"
	touch $@

# Add journal names
journal-names:
	$(TIME) alexandria3k --data-source journal-names \
	  --populate-db-path "$(MAINDB).db"
	touch $@

simple-rolap/Makefile:
	git clone https://github.com/dspinellis/simple-rolap
