#
# A makefile that populates crossref dataset based on one ethnicity
#
export MAINDB?=ethnicity
export DEPENDENCIES=populate
include ../common/Makefile

ETH?=greek

populate: populate-rest

populate-names: $(CROSSREF_DIR)
	$(A3K) populate "$(MAINDB).db" crossref "$(CROSSREF_DIR)" \
	--columns work_authors.id work_authors.given work_authors.family work_authors.work_id 
	touch $@

classify: populate-names $(CROSSREF_DIR)
	$(A3K) process "$(MAINDB).db" link-author-ethnicities
	touch $@

populate-rest: classify $(CROSSREF_DIR)
	$(A3K) populate "$(MAINDB).db" crossref "$(CROSSREF_DIR)" \
	--row-selection "work_authors.work_id IN (SELECT work_id FROM author_ethnicities WHERE ethnicity = '$(ETH)')"
	touch $@