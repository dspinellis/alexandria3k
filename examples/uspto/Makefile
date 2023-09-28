#
# CI placeholder for USPTO example
#

export RDBMS?=sqlite
export ROLAPDB?=rolap

A3K?=a3k

V?=1
TIME?=time
export SQLITE_TMPDIR?=.

include simple-rolap/Makefile

simple-rolap/Makefile:
	git clone https://github.com/dspinellis/simple-rolap

depclean:
	rm -f $(DEPENDENCIES)
