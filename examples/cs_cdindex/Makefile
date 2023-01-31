#
# Create a table with the CD index of all CS works
#

export MAINDB?=cs_cdindex

export DEPENDENCIES=populate

include ../common/Makefile

# Populate database with required fields
populate: $(CROSSREF_DIR) dblp.db
	$(TIME) alexandria3k --data-source Crossref "$(CROSSREF_DIR)" \
	  --populate "$(MAINDB).db" \
	  --debug progress \
	  --attach-databases 'dblp:dblp.db' \
	  --row-selection 'EXISTS (SELECT 1 FROM dblp.dois WHERE works.doi = dois.doi)'
	touch $@

dblp.xml.gz:
	wget https://dblp.org/xml/dblp.xml.gz

dblp.db: dblp.xml.gz cs_works.sed
	zcat dblp.xml.gz | ./cs_works.sed | sqlite3 dblp.db
