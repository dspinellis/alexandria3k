# Calculate journal impact metrics

This directory contains the implementation for calculating
diverse journal impact metrics, such as the
[journal impact factor](https://en.wikipedia.org/wiki/Impact_factor) and
[Eigenfactor scores](http://www.eigenfactor.org/methods.pdf).
A journal's impact factor is based on the ratio between its publications
and references to them.
The Eigenfactor score is a measure of a journal's importance,
calculated in a way similar to Google's PageRank algorithm
applied to the citation network.

## Eigenfactor calculation overview

The calculation involves the following steps.
1. **Data Preparation**: Aggregating citation data and article counts
   from the main database into indexed intermediate tables.
2. **Score Calculation**: A Python script (`eigenfactor.py`)
   reads the aggregated data,
   constructs a sparse adjacency matrix of the citation network, and
   computes the principal eigenvector using the power iteration method.
3. **Reporting**: The calculated scores are stored in the database
   for subsequent reporting.

## Dependencies

The Eigenfactor calculation requires the installation of
the _pandas_, _numpy_, and _scipy_ Python packages.
Install them with your favourite Python package manager (e.g. _uv_, _pip_),
ideally in a virtual environment.
