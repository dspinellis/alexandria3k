#
# Create a table with the CD index of all CS works
#

DBLP?=dblp.xml.gz

export MAINDB?=cs_cdindex

export DEPENDENCIES=populate ../cdindex/tables/cdindex

include ../common/Makefile

# Populate database with required fields
populate: $(CROSSREF_DIR) dblp.db
	$(TIME) $(A3K) --progress \
	  populate "$(MAINDB).db" crossref "$(CROSSREF_DIR)" \
	  --attach-databases 'dblp:dblp.db' \
	  --row-selection 'EXISTS (SELECT 1 FROM dblp.dois WHERE works.doi = dois.doi)'
	touch $@

$(DBLP):
	wget https://dblp.org/xml/dblp.xml.gz

dblp.db: $(DBLP) cs_works.sed
	zcat $(DBLP) | ./cs_works.sed | sqlite3 dblp.db

# The CD index calculation is required for this example
../cdindex/tables/cdindex:
	make -C ../cdindex MAINDB=cdindex tables/cdindex
