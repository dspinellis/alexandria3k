#
# Output the CD index of all works
#

export MAINDB?=cdindex
#export DEPENDENCIES=reports/cdindex-otf.csv
export DEPENDENCIES=populate reports/cdindex-db.csv

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

reports/cdindex-otf.csv: $(CROSSREF_DIR) cdindex-otf.py
	mkdir -p reports
	$(TIME) python cdindex-otf.py "$(CROSSREF_DIR)" >$@

reports/cdindex-db.csv: populate cdindex-db.py
	mkdir -p reports
	$(TIME) python cdindex-db.py  "$(MAINDB).db" >$@
