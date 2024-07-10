# Calculate the CD5 index of Crossref works

A publication's [consolidation-disruption (CD) index](https://doi.org/10.1287/mnsc.2015.2366)
provides a dynamic network measure of scientific progress.
The scripts in this directory calculate the CD₅ (five-year) index
for Crossref works published between 1945 and 2021.
To do so it populates a graph with 116,568,934 nodes (publications) and
1,255,033,889 edges (citations).
The C++ implementation used ([cdindex-db.cpp](./cdindex-db.cpp))
is multithreaded, so on an 8-core machine it takes less than 10 hours.
It also demonstrates using an Alexandria3k populated database with C++.

The original Python implementation ([cdindex-db.py](./cdindex-db.py))
[cannot be easily parallelized](https://stackoverflow.com/questions/75267745/how-can-i-share-a-large-data-structure-among-forked-python-processes),
and would take
16 days to finish with the
[original cdindex package](https://github.com/russellfunk/cdindex) or
50 hours to finish with the
[fast-cidindex package](https://github.com/dspinellis/fast-cdindex),
which is also used by the C++ implementation.
The [cdindex-otf.py](./cdindex-otf.py) performs the same calculation
on the fly, as a demonstration of using the _Alexandria3k_ Python API.
