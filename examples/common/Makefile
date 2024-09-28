#
# Common rules and functionality for all analysis tasks
#

export RDBMS?=sqlite
# TODO: Set MAINDB
export ROLAPDB?=rolap

A3K?=a3k
CROSSREF_DIR?=../common/Crossref-April-2024
USPTO_DIR?=../common/uspto-data
ORCID_SUMMARIES?=../common/ORCID_2022_10_summaries.tar.gz
ROR?=../common/ror-v1.17.1-2022-12-16.zip
PUBMED_DIR?=../common/pubmed
DATACITE?=../common/datacite.tar.gz

V?=1
TIME?=time
export SQLITE_TMPDIR?=.

include simple-rolap/Makefile

$(CROSSREF_DIR):
	cd ../common && \
	aria2c https://doi.org/10.13003/83b2gq && \
	mv 'April 2022 Public Data File from Crossref' Crossref-April-2022

$(USPTO_DIR):
	cd ../common && ./fetch-uspto.sh

$(PUBMED_DIR):
	cd ../common && ./fetch-pubmed.sh

$(ORCID_SUMMARIES):
	curl -L https://orcid.figshare.com/ndownloader/files/37635374 >$@

$(ROR):
	curl -L 'https://zenodo.org/record/7448410/files/v1.17.1-2022-12-16-ror-data.zip?download=1' >$@

$(DATACITE):
	@echo "Download the DataCite Public Data File as datacite.tar.gz from https://datafiles.datacite.org/"

# TODO when using this Makefile: Add rule in including Makefile named
# "populate" to populate the database with required data

asjcs: populate
	$(TIME) $(A3K) --progress populate "$(MAINDB).db" asjcs
	touch $@

doaj: populate
	$(TIME) $(A3K) --progress populate "$(MAINDB).db" doaj $(DOAJ)
	touch $@

link-works-asjcs: asjcs populate
	$(TIME) $(A3K) process "$(MAINDB).db" link-works-asjcs
	touch $@

rors: populate $(ROR)
	$(TIME) $(A3K) --progress populate "$(MAINDB).db" ror $(ROR)
	touch $@

link-aa-base-ror: rors populate
	$(TIME) $(A3K) process "$(MAINDB).db" link-aa-base-ror
	touch $@

link-aa-top-ror: rors populate
	$(TIME) $(A3K) process "$(MAINDB).db" link-aa-top-ror
	touch $@

# Add journal names
journal-names:
	$(TIME) $(A3K) --progress populate "$(MAINDB).db" journal-names $(JOURNAL_NAMES)
	touch $@

simple-rolap/Makefile:
	git clone https://github.com/dspinellis/simple-rolap

depclean:
	rm -f $(DEPENDENCIES)
