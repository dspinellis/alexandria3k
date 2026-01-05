#
# Alexandria3k Crossref bibliographic metadata processing
# Copyright (C) 2025  Panagiotis Spanakis
# SPDX-License-Identifier: GPL-3.0-or-later
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

"""
Tests for the SNIP calculation module using Leiden clustering.
"""

import pytest
import pandas as pd
import numpy as np
import igraph as ig
import leidenalg

from snip import (
    calculate_snip,
    calculate_snip_fallback,
    calculate_citation_potential,
    calculate_journal_citation_potential,
    build_graph,
    run_leiden_clustering,
    assign_journals_to_communities,
)


# =============================================================================
# SNIP CALCULATION TESTS
# =============================================================================


def test_calculate_snip_basic():
    """
    Test basic SNIP calculation.
    SNIP = Raw Impact per Paper / Citation Potential
    """
    publications_df = pd.DataFrame(
        {
            "journal_id": [1, 2, 3],
            "publications_number": [100, 100, 100],
        }
    )

    citations_df = pd.DataFrame(
        {
            "journal_id": [1, 2, 3],
            "citations": [200, 100, 50],
        }
    )

    journal_potential_df = pd.DataFrame(
        {
            "journal_id": [1, 2, 3],
            "citation_potential": [2.0, 1.0, 0.5],
        }
    )

    result = calculate_snip(publications_df, citations_df, journal_potential_df)

    assert len(result) == 3
    assert "snip_score" in result.columns

    scores = result.set_index("journal_id")["snip_score"]
    # SNIP = (citations/publications) / citation_potential
    # Journal 1: (200/100) / 2.0 = 1.0
    # Journal 2: (100/100) / 1.0 = 1.0
    # Journal 3: (50/100) / 0.5 = 1.0
    assert np.isclose(scores[1], 1.0, atol=0.01)
    assert np.isclose(scores[2], 1.0, atol=0.01)
    assert np.isclose(scores[3], 1.0, atol=0.01)


def test_calculate_snip_different_potentials():
    """
    Test that different citation potentials lead to different SNIP scores.
    """
    publications_df = pd.DataFrame(
        {
            "journal_id": [1, 2],
            "publications_number": [100, 100],
        }
    )

    citations_df = pd.DataFrame(
        {
            "journal_id": [1, 2],
            "citations": [100, 100],
        }
    )

    # Journal 2 is in a high-citation field (higher potential)
    journal_potential_df = pd.DataFrame(
        {
            "journal_id": [1, 2],
            "citation_potential": [10.0, 50.0],
        }
    )

    result = calculate_snip(publications_df, citations_df, journal_potential_df)
    scores = result.set_index("journal_id")["snip_score"]

    # Journal 1 has higher SNIP because same citations in a lower-citation field
    assert scores[1] > scores[2]


def test_calculate_snip_handles_missing_citations():
    """
    Test that journals with no citations get SNIP = 0.
    """
    publications_df = pd.DataFrame(
        {
            "journal_id": [1, 2],
            "publications_number": [100, 100],
        }
    )

    # Journal 2 has no citations
    citations_df = pd.DataFrame(
        {
            "journal_id": [1],
            "citations": [100],
        }
    )

    journal_potential_df = pd.DataFrame(
        {
            "journal_id": [1, 2],
            "citation_potential": [10.0, 10.0],
        }
    )

    result = calculate_snip(publications_df, citations_df, journal_potential_df)
    scores = result.set_index("journal_id")["snip_score"]

    assert scores[1] > 0
    assert scores[2] == 0


def test_calculate_snip_fallback():
    """
    Test fallback SNIP calculation when Leiden is unavailable.
    """
    publications_df = pd.DataFrame(
        {
            "journal_id": [1, 2, 3],
            "publications_number": [100, 100, 100],
        }
    )

    citations_df = pd.DataFrame(
        {
            "journal_id": [1, 2, 3],
            "citations": [200, 100, 50],
        }
    )

    reference_df = pd.DataFrame(
        {
            "journal_id": [1, 2, 3],
            "avg_references": [20.0, 20.0, 20.0],
        }
    )

    result = calculate_snip_fallback(publications_df, citations_df, reference_df)

    assert len(result) == 3
    assert "snip_score" in result.columns
    assert all(result["snip_score"] >= 0)


# =============================================================================
# CITATION POTENTIAL TESTS
# =============================================================================


def test_calculate_citation_potential():
    """
    Test citation potential calculation per community.
    """
    assignments_df = pd.DataFrame(
        {
            "journal_id": [1, 2, 3, 4],
            "community_id": [0, 0, 1, 1],
            "weight": [1.0, 1.0, 1.0, 1.0],
        }
    )

    reference_df = pd.DataFrame(
        {
            "journal_id": [1, 2, 3, 4],
            "avg_references": [10.0, 20.0, 30.0, 40.0],
        }
    )

    result = calculate_citation_potential(assignments_df, reference_df)

    assert len(result) == 2  # Two communities
    potentials = result.set_index("community_id")["citation_potential"]

    # Community 0: avg of 10, 20 = 15
    # Community 1: avg of 30, 40 = 35
    assert np.isclose(potentials[0], 15.0, atol=0.1)
    assert np.isclose(potentials[1], 35.0, atol=0.1)


def test_calculate_journal_citation_potential():
    """
    Test journal-level citation potential (weighted by community membership).
    """
    # Journal 1 is in community 0 only
    # Journal 2 is split between communities 0 and 1
    assignments_df = pd.DataFrame(
        {
            "journal_id": [1, 2, 2],
            "community_id": [0, 0, 1],
            "weight": [1.0, 0.6, 0.4],
        }
    )

    community_potential_df = pd.DataFrame(
        {
            "community_id": [0, 1],
            "citation_potential": [10.0, 50.0],
        }
    )

    result = calculate_journal_citation_potential(
        assignments_df, community_potential_df
    )
    potentials = result.set_index("journal_id")["citation_potential"]

    # Journal 1: 1.0 * 10 = 10
    # Journal 2: 0.6 * 10 + 0.4 * 50 = 6 + 20 = 26
    assert np.isclose(potentials[1], 10.0, atol=0.1)
    assert np.isclose(potentials[2], 26.0, atol=0.1)


# =============================================================================
# LEIDEN CLUSTERING TESTS (only if available)
# =============================================================================


def test_build_graph():
    """
    Test graph construction from coupling data.
    """
    coupling_df = pd.DataFrame(
        {
            "journal_a": [1, 1, 2],
            "journal_b": [2, 3, 3],
            "coupling_strength": [10, 5, 8],
        }
    )

    g, journals, journal_to_idx = build_graph(coupling_df)

    assert g.vcount() == 3
    assert g.ecount() == 3
    assert set(journals) == {1, 2, 3}
    assert "weight" in g.es.attributes()


def test_run_leiden_clustering():
    """
    Test that Leiden clustering returns valid partition.
    """
    # Create a simple graph with two clear communities
    coupling_df = pd.DataFrame(
        {
            "journal_a": [1, 1, 2, 3, 3, 4],
            "journal_b": [2, 3, 3, 4, 5, 5],
            "coupling_strength": [100, 100, 100, 100, 100, 100],
        }
    )

    g, journals, journal_to_idx = build_graph(coupling_df)
    partition = run_leiden_clustering(g, resolution=1.0)

    # Should return a valid partition
    assert len(partition) > 0
    assert len(partition.membership) == g.vcount()


def test_assign_journals_to_communities():
    """
    Test multi-community assignment based on coupling strength.
    """
    # Create graph where journal 2 is between two communities
    coupling_df = pd.DataFrame(
        {
            "journal_a": [1, 2, 2, 3],
            "journal_b": [2, 3, 4, 4],
            "coupling_strength": [50, 50, 50, 100],
        }
    )

    g, journals, journal_to_idx = build_graph(coupling_df)
    partition = run_leiden_clustering(g, resolution=0.5)

    assignments = assign_journals_to_communities(
        g, partition, journals, threshold_min=0.3
    )

    assert len(assignments) > 0
    assert "journal_id" in assignments.columns
    assert "community_id" in assignments.columns
    assert "weight" in assignments.columns

    # Weights should sum to 1 for each journal
    weight_sums = assignments.groupby("journal_id")["weight"].sum()
    assert all(np.isclose(weight_sums, 1.0, atol=0.01))


def test_leiden_finds_clear_communities():
    """
    Test that Leiden correctly identifies two distinct communities.
    """
    # Two tightly-coupled groups with weak connection
    coupling_df = pd.DataFrame(
        {
            "journal_a": [1, 1, 2, 4, 4, 5],
            "journal_b": [2, 3, 3, 5, 6, 6],
            "coupling_strength": [100, 100, 100, 100, 100, 100],  # Strong within-group
        }
    )

    g, journals, journal_to_idx = build_graph(coupling_df)
    partition = run_leiden_clustering(g, resolution=1.0)

    # Should find 2 communities (possibly more depending on resolution)
    assert len(partition) >= 2

    # Journals 1,2,3 should be in one community; 4,5,6 in another
    communities = partition.membership
    assert communities[journal_to_idx[1]] == communities[journal_to_idx[2]]
    assert communities[journal_to_idx[1]] == communities[journal_to_idx[3]]
    assert communities[journal_to_idx[4]] == communities[journal_to_idx[5]]
    assert communities[journal_to_idx[4]] == communities[journal_to_idx[6]]


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


def test_full_snip_pipeline():
    """
    Test the complete SNIP calculation pipeline.
    """
    # Create test data
    coupling_df = pd.DataFrame(
        {
            "journal_a": [1, 1, 2, 3, 3, 4],
            "journal_b": [2, 3, 3, 4, 5, 5],
            "coupling_strength": [100, 100, 100, 100, 100, 100],
        }
    )

    publications_df = pd.DataFrame(
        {
            "journal_id": [1, 2, 3, 4, 5],
            "publications_number": [100, 100, 100, 100, 100],
        }
    )

    citations_df = pd.DataFrame(
        {
            "journal_id": [1, 2, 3, 4, 5],
            "citations": [100, 150, 200, 50, 75],
        }
    )

    reference_df = pd.DataFrame(
        {
            "journal_id": [1, 2, 3, 4, 5],
            "avg_references": [20, 25, 30, 15, 18],
        }
    )

    # Run pipeline
    g, journals, journal_to_idx = build_graph(coupling_df)
    partition = run_leiden_clustering(g, resolution=1.0)
    assignments_df = assign_journals_to_communities(g, partition, journals)
    community_potential_df = calculate_citation_potential(assignments_df, reference_df)
    journal_potential_df = calculate_journal_citation_potential(
        assignments_df, community_potential_df
    )
    snip_df = calculate_snip(publications_df, citations_df, journal_potential_df)

    # Verify output
    assert len(snip_df) == 5
    assert all(snip_df["snip_score"] >= 0)
    assert "raw_impact" in snip_df.columns
    assert "citation_potential" in snip_df.columns
