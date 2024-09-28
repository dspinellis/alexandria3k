#
# Run USPTO example queries
#

export MAINDB?=uspto
export DEPENDENCIES=populate

include ../common/Makefile

# Populate database with USPTO data
populate: $(USPTO_DIR)
	$(TIME) $(A3K) --progress \
	  populate "$(MAINDB).db" uspto "$(USPTO_DIR)"
	touch $@
