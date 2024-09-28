#
# Minimal application of Alexandria3k
# Report the average number of work authors per decade
#

export MAINDB?=hello
export DEPENDENCIES=populate

include ../common/Makefile

# Populate database with a 0.02% sample of Crossref containers
populate: $(CROSSREF_DIR)
	$(TIME) $(A3K) --progress \
	  populate "$(MAINDB).db" crossref "$(CROSSREF_DIR)" \
	  --sample 'random.random() < 0.0002' \
	  --columns works.id \
	    works.published_year \
	    work_authors.work_id \
	  --row-selection 'works.published_year >= 1940'
	touch $@
