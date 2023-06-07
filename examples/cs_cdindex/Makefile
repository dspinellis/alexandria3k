#
# Create a table with the CD index of all CS works
#

DBLP?=dblp.xml.gz

export MAINDB?=cs_cdindex

export DEPENDENCIES=populate

include ../common/Makefile

# Populate database with required fields
populate: $(CROSSREF_DIR) dblp.db
	$(TIME) $(A3K) --debug progress \
	  populate "$(MAINDB).db" crossref "$(CROSSREF_DIR)" \
	  --attach-databases 'dblp:dblp.db' \
	  --row-selection 'EXISTS (SELECT 1 FROM dblp.dois WHERE works.doi = dois.doi)'
	touch $@

$(DBLP):
	wget https://dblp.org/xml/dblp.xml.gz

dblp.db: $(DBLP) cs_works.sed
	zcat $(DBLP) | ./cs_works.sed | sqlite3 dblp.db
