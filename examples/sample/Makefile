#
# Minimal application of Alexandria3k
#

export MAINDB?=sample
export DEPENDENCIES=populate

include ../common/Makefile

# Populate database with a 0.02% sample of Crossref containers
populate: $(CROSSREF_DIR)
	$(TIME) $(A3K) --progress \
	  populate "$(MAINDB).db" crossref "$(CROSSREF_DIR)" \
	  --sample 'random.random() < 0.01'
	touch $@
