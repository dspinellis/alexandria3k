#
# Determine author relative productivity in terms of works authored per year.
#

VARS_BUILTIN := $(.VARIABLES)

export MAINDB?=au-productivity
export DEPENDENCIES=populate

include ../common/Makefile

# Populate database with a 0.02% sample of Crossref containers
populate: $(CROSSREF_DIR)
	$(TIME) alexandria3k --data-source Crossref "$(CROSSREF_DIR)" \
	 --populate "$(MAINDB).db" \
	  --debug progress \
	  --columns works.id \
	    works.published_year \
	    work_authors.work_id \
	    work_authors.given \
	    work_authors.family \
	  --row-selection 'works.published_year BETWEEN 1945 and 2021'
	touch $@
