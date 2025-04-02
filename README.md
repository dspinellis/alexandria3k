[![Alexandria3k CI](https://github.com/dspinellis/alexandria3k/actions/workflows/ci.yml/badge.svg)](https://github.com/dspinellis/alexandria3k/actions/workflows/ci.yml)

## Alexandria3k

<!-- INTRO-BEGIN -->

The _alexandria3k_ package supplies a library and a command-line tool
providing fast and space-efficient relational query access to the following
large scientific publication open data sets.
Data are decompressed on the fly, thus allowing the package's use even on
storage-restricted laptops.
The _alexandria3k_ package supports the following large data sets.

* [Crossref](https://www.nature.com/articles/d41586-022-02926-y)
  (184 GiB compressed,
  1.9 TiB uncompressed — as of March 2025).
  This contains publication metadata from all major international publishers.
  The Crossref data set is split into about 33 thousand files.
  Each file contains JSON data for 5000 publications (works).
  In total, Crossref contains data for 167 million works,
  35 million abstracts, 465 million associated work authors,
  and 2.5 billion references.
<!--. gzip -l * | awk '{s += $2}END{print s, s / 1024 / 1024 / 1024 / 1024}'
 2081831841198 1.89342 -->

* [PubMed](https://pubmed.ncbi.nlm.nih.gov/)
  (43 GB compressed, 327 GB uncompressed).
  This comprises more than 36 million citations
  for biomedical literature from
  [MEDLINE](https://www.nlm.nih.gov/medline/medline_overview.html),
  life science journals, and online books,
  with rich domain-specific metadata,
  such as [MeSH](https://www.nlm.nih.gov/mesh/meshhome.html) indexing,
  funding, genetic, and chemical details.

* [ORCID summary data set](https://support.orcid.org/hc/en-us/articles/360006897394-How-do-I-get-the-public-data-file-)
  (37 GiB compressed, 651 GiB uncompressed — as of October 2024).
  This contains about 22 million author details records.
<!-- tar tzvf ORCID_2024_10_summaries.tar.gz | wc -l -->

* [DataCite](https://datacite.org/)
  (22 GB compressed, 197 GB uncompressed).
  This comprises research outputs and resources,
  such as data, pre-prints, images, and samples,
  containing about 50 million work entries.

* [United States Patent Office issued patents](https://bulkdata.uspto.gov/)
  (12 GiB compressed,
  128 GiB uncompressed — as of January 2025).
  This  contains about 5.4 million records.
<!-- find . -name \*.zip | xargs -n 1 unzip -v | awk '/files$/{ s+= $1}END{print s, s / 1024 / 1024 / 1024}' -->

Further supported data sets include
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
<!-- INTRO-END -->

## Installation and documentation

* 📦 The _alexandria3k_ is available on [PyPI](https://pypi.org/project/alexandria3k/).
* 📄 Full reference and use documentation for _alexandria3k_  is available [here](https://dspinellis.github.io/alexandria3k/).

## Major contributors

* [Aggelos Margkas](https://github.com/AggelosMargkas): US patents
* [Bas Verlooy](https://github.com/BasVerlooy): PubMed
* [Evgenia Pampidi](https://github.com/evgepab): DataCite

## Publication

Details about the rationale, design, implementation, and use of this software
can be found in the following paper.

Diomidis Spinellis. Open reproducible scientometric research with Alexandria3k. _PLoS ONE_ 18(11): e0294946. November 2023. [doi: 10.1371/journal.pone.0294946](https://doi.org/10.1371/journal.pone.0294946)
