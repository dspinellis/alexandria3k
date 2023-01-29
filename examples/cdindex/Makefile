#
# Output the CD index of all works
#

export MAINDB?=cdindex

export DEPENDENCIES=populate tables/cdindex

include ../common/Makefile

# Populate database with required fields
populate: $(CROSSREF_DIR)
	$(TIME) alexandria3k --data-source Crossref "$(CROSSREF_DIR)" \
	  --populate "$(MAINDB).db" \
	  --debug progress \
	  --columns works.id \
	    works.doi \
	    works.published_year \
	    works.published_month \
	    works.published_day \
	    work_references.work_id \
	    work_references.doi
	touch $@

reports/cdindex-otf.txt: $(CROSSREF_DIR) cdindex-otf.py
	mkdir -p reports
	$(TIME) python cdindex-otf.py "$(CROSSREF_DIR)" >$@

tables/cdindex: populate cdindex-db
	mkdir -p tables
	$(TIME) ./cdindex-db "$(MAINDB).db" "$(ROLAPDB).db" >$@

# Note: dev branch required for iterator access
# https://github.com/SqliteModernCpp/sqlite_modern_cpp/pull/126
sqlite_modern_cpp:
	git clone -b dev https://github.com/SqliteModernCpp/sqlite_modern_cpp.git

fast-cdindex:
	git clone https://github.com/dspinellis/fast-cdindex.git

cdindex-db: cdindex-db.cpp sqlite_modern_cpp fast-cdindex
	g++ -std=c++17 -I sqlite_modern_cpp/hdr -I fast-cdindex/src -o $@ cdindex-db.cpp fast-cdindex/src/cdindex.cpp -lsqlite3 -ltbb -ggdb3 -O3
