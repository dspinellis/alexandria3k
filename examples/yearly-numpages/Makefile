#
# Report yearly pages per work
#

export MAINDB?=pages
export DEPENDENCIES=populate

include ../common/Makefile

# Populate database with works and their pages
populate: $(CROSSREF_DIR)
	$(TIME) alexandria3k --data-source Crossref "$(CROSSREF_DIR)" \
	 --populate "$(MAINDB).db" \
	  --debug progress \
	  --columns works.id \
	    works.published_year \
	    works.page \
	  --debug progress
	touch $@
