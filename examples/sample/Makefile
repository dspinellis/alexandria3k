#
# Minimal application of Alexandria3k
#

export MAINDB?=sample
export DEPENDENCIES=populate

include ../common/Makefile

# Populate database with a 0.02% sample of Crossref containers
populate: $(CROSSREF_DIR)
	$(TIME) alexandria3k --data-source Crossref "$(CROSSREF_DIR)" \
	 --populate "$(MAINDB).db" \
	  --debug progress \
	  --sample 'random.random() < 0.01'
	touch $@
