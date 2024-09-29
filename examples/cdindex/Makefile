#
# Output the CD index of all works
#

export MAINDB?=cdindex

export DEPENDENCIES=populate tables/cdindex

# Intel thread building blocks library
TBB?=-ltbb

CFLAGS+=-std=c++17 -ggdb3 -O3
LDFLAGS+=-lsqlite3 $(TBB) -ldl -lpthread

# If a modern SQLite3 is not available, create one in e.g.
# sqlite-amalgamation-3460000 with
# gcc -c sqlite3.c -o sqlite3.o
# ar rcs libsqlite3.a sqlite3.o
# and pass the directory as an SQLITE_DIR to make
ifdef SQLITE_DIR
  CFLAGS+=-I $(SQLITE_DIR)
  LDFLAGS+=-L $(SQLITE_DIR)
endif


include ../common/Makefile

# Populate database with required fields
populate: $(CROSSREF_DIR)
	$(TIME) $(A3K) --progress \
	  populate "$(MAINDB).db" crossref "$(CROSSREF_DIR)" \
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
	git clone --depth=1 https://github.com/SqliteModernCpp/sqlite_modern_cpp.git

fast-cdindex:
	git clone --depth=1 https://github.com/dspinellis/fast-cdindex.git

cdindex-db: cdindex-db.cpp sqlite_modern_cpp fast-cdindex
	g++ $(CFLAGS) -I sqlite_modern_cpp/hdr -I fast-cdindex/src -o $@ cdindex-db.cpp fast-cdindex/src/cdindex.cpp $(LDFLAGS)

# Fix a DOI containing a |
reports/cd5index-all.txt.gz: reports/cd5index-all.txt
	sed 's/\\|\[ndash/-/;s/|/\t/' $? | gzip -c >$@

# For benchmarking; this will also create the cdindex table
tables/cdindex-py: populate cdindex-db.py
	mkdir -p tables
	$(TIME) python cdindex-db.py "$(MAINDB).db" "$(ROLAPDB).db" >$@
