# Calculate CD5 index of Crossref works

A publication's [CD index](https://doi.org/10.1287/mnsc.2015.2366)
provides a dynamic network measure of scientific progress.
The scripts in this directory calculate the CD₅ (five-year) index
for Crossref works published between 1945 and 2021.
To do so it populates a graph with 116,568,934 nodes (publications) and
1,255,033,889 edges (citations).

Thw [cdindex-db.py](./cdindex-db.py) does so on a previously populated
database.
The [cdindex-otf.py](./cdindex-otf.py) performs the same calculation
on the fly, as a demonstration of Using the _Alexandria3k_ Python API.
