[![Alexandria3k CI](https://github.com/dspinellis/alexandria3k/actions/workflows/ci.yml/badge.svg)](https://github.com/dspinellis/alexandria3k/actions/workflows/ci.yml)

## Alexandria3k

The _alexandria3k_ package supplies a library and a command-line tool
providing efficient relational query access to diverse publication open
data sets.
The largest one is the entire
[Crossref data set](https://www.nature.com/articles/d41586-022-02926-y)
(157 GB compressed, 1 TB uncompressed).
This contains publication metadata from about 134 million publications from
all major international publishers with full citation data for 60 million
of them.
In addition,
the Crossref data set can be linked with
the [ORCID summary data set](https://support.orcid.org/hc/en-us/articles/360006897394-How-do-I-get-the-public-data-file-)
  (25 GB compressed, 435 GB uncompressed),
  containing about 78 million author records,
the [United States Patent Office issued patents](https://bulkdata.uspto.gov/)
  (11 GB compressed, 115 GB uncompressed),
  containing about 5.4 million records,
as well as
data sets of
funder bodies,
journal names,
open access journals,
and research organizations.

The _alexandria3k_ package installation contains all elements required
to run it.
It does not require the installation, configuration, and maintenance
of a third party relational or graph database.
It can therefore be used out-of-the-box for performing reproducible
publication research on the desktop.

## Documentation

The complete reference and use documentation for *alexandria3k*  can be found [here](https://dspinellis.github.io/alexandria3k/).

## Pre-print and citation

Details about the rationale, design, implementation, and use of this software
can be found in the following paper.

Diomidis Spinellis. Open Reproducible Systematic Publication Research. arXiv:2301.13312, February 2023. https://doi.org/10.48550/arXiv.2301.13312
