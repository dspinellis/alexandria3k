#
# Report yearly pages per work
#

export MAINDB?=pages
export DEPENDENCIES=populate

include ../common/Makefile

# Populate database with works and their pages
populate: $(CROSSREF_DIR)
	$(TIME) $(A3K) --progress \
	  populate "$(MAINDB).db" crossref "$(CROSSREF_DIR)" \
	  --columns works.id \
	    works.published_year \
	    works.page
	touch $@
