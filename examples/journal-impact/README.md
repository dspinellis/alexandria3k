# Calculate journal impact metrics

This directory contains the implementation for calculating
diverse journal impact metrics, such as the
[journal impact factor](https://en.wikipedia.org/wiki/Impact_factor),
[Eigenfactor scores](http://www.eigenfactor.org/methods.pdf),
[SCImago Journal Rank (SJR)](https://en.wikipedia.org/wiki/SCImago_Journal_Rank),
[Article Influence Score (AIS)](https://en.wikipedia.org/wiki/Eigenfactor#Article_Influence_Score), and
[Source Normalized Impact per Paper (SNIP)](https://www.sciencedirect.com/science/article/abs/pii/S1751157712001010?via%3Dihub).

A journal's impact factor is based on the ratio between its publications
and references to them.
The other metrics use eigenvector centrality to measure journal importance,
with different normalization approaches to account for field differences
and journal size.

## Eigenfactor calculation overview

The Eigenfactor score measures a journal's total importance to the
scientific community, calculated similarly to Google's PageRank algorithm.

The calculation involves the following steps:
1. **Data Preparation**: Aggregating citation data (5-year window)
   and article counts from the main database into indexed intermediate tables.
2. **Self-Citation Removal**: Journal self-citations are completely excluded
   from the citation network.
3. **Score Calculation**: The Python script (`eigenfactor.py`)
   reads the aggregated data,
   constructs a sparse adjacency matrix of the citation network, and
   computes the principal eigenvector using the power iteration method.
4. **Normalization**: Scores are normalized so that all journals sum to 100%.
5. **Reporting**: The calculated scores are stored in the database
   for subsequent reporting.

## SJR (SCImago Journal Rank) calculation overview

The SCImago Journal Rank measures prestige per article, accounting for both
the number and quality of citations received.

Key differences from Eigenfactor:
1. **3-year citation window**: Uses a shorter time frame than Eigenfactor.
2. **Limited self-citations**: Self-citations are capped at 33% of incoming
   citations (not excluded entirely), reflecting that some self-citation
   is normal academic practice.
3. **Per-article normalization**: Scores are normalized by article count,
   then scaled so the average journal has SJR = 1.0.
   This makes SJR size-independent.

Run with: `./eigenfactor.py --metric sjr`

## AIS (Article Influence Score) calculation overview

The Article Influence Score measures the average influence of a journal's articles over 5 years.
It is essentially the Eigenfactor score normalized by the journal's
article output, making it comparable to the traditional impact factor.

Key characteristics:
1. **5-year citation window**: Same as Eigenfactor.
2. **Excluded self-citations**: Same as Eigenfactor.
3. **Per-article normalization**: Divides prestige by article count,
   then scales so the average article has AIS = 1.0.
   An AIS > 1.0 means above-average influence per article.

Run with: `./eigenfactor.py --metric ais`

## SNIP (Source Normalized Impact per Paper) calculation overview

SNIP measures contextual citation impact by normalizing citations
against the citation potential of each journal's field.
This makes SNIP directly comparable across different disciplines.

The calculation uses Leiden community detection on the bibliographic
coupling network to discover research fields organically:

1. **Bibliographic Coupling Network**: A weighted graph is constructed where
   journals are nodes and edges represent shared references. Two journals
   are connected if they cite common sources; the edge weight is the
   number of shared references.
2. **Leiden Clustering**: The Leiden algorithm (an improved version of Louvain)
   is applied to discover communities of related journals. Unlike seeded
   approaches, this finds fields based on actual citation patterns without
   bias toward high-citation areas.
3. **Multi-Community Assignment**: Journals can belong to multiple communities.
   A journal is assigned to a community if its coupling strength to that
   community is ≥30% of its maximum coupling strength. This handles
   interdisciplinary journals naturally.
4. **Citation Potential per Community**: For each community, the weighted
   average reference density is calculated based on member journals.
5. **Journal Citation Potential**: Each journal's citation potential is the
   weighted average of its communities' potentials.
6. **SNIP Calculation**: SNIP = (Citations/Paper) / Citation_Potential

Key advantages of the Leiden approach:
- **No bias toward high-citation fields**: Communities emerge from data
- **Handles niche fields**: Even low-citation areas form communities
- **Better interdisciplinary handling**: Multi-community assignment
- **Reproducible**: Uses a fixed random seed for deterministic results

SNIP is calculated using the `snip.py` Python script, which requires
the `leidenalg` and `python-igraph` packages. Run with: `make tables/snip`

## Dependencies

The Eigenfactor, SJR, and AIS calculations require the installation of
the _pandas_, _numpy_, and _scipy_ Python packages.

The SNIP calculation additionally requires the _leidenalg_ and _python-igraph_
packages for community detection.

Install them with your favourite Python package manager (e.g. _uv_, _pip_),
ideally in a virtual environment.

## Journal Impact Report Fields

The file `reports/journal-impact-report.txt` contains the following columns for each journal:

- **title**: Journal title
- **publisher**: Journal publisher
- **issn_print**: Print ISSN
- **issn_eprint**: Electronic ISSN
- **issns_additional**: Additional ISSNs (if any)
- **doi**: Journal DOI (if available)
- **citations_number2**: Number of citations received in the 2-year window (for 2-year impact factor)
- **publications_number2**: Number of articles published in the 2-year window
- **impact_factor2**: 2-year impact factor (citations_number2 / publications_number2)
- **citations_number5**: Number of citations received in the 5-year window (for 5-year impact factor)
- **publications_number5**: Number of articles published in the 5-year window
- **impact_factor5**: 5-year impact factor (citations_number5 / publications_number5)
- **h5_index**: h5-index (number of articles with at least h citations in the last 5 years)
- **h5_median**: Median number of citations for articles in the h5-index
- **eigenfactor_score**: Eigenfactor score (journal's overall influence in the citation network)
- **sjr_score**: SCImago Journal Rank (prestige per article, normalized)
- **ais_score**: Article Influence Score (average influence per article)
- **snip_score**: Source Normalized Impact per Paper (SNIP, normalized by field citation potential)

This report provides a comprehensive comparison of journals across multiple impact metrics and citation windows.
