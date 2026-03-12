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

"""Tests for context-normalized impact calculation using Leiden clustering."""

import numpy as np
import pandas as pd

from context_normalized_impact import (
    calculate_context_impact,
    calculate_context_impact_fallback,
    calculate_citation_potential,
    calculate_journal_citation_potential,
    build_graph,
    run_leiden_clustering,
    assign_journals_to_communities,
    _otsu_threshold,
    _merge_small_communities,
    MAX_COMMUNITIES_PER_JOURNAL,
)


def test_calculate_context_impact_basic():
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

    result = calculate_context_impact(
        publications_df, citations_df, journal_potential_df
    )
    assert len(result) == 3
    assert "impact_score" in result.columns

    scores = result.set_index("journal_id")["impact_score"]
    # (citations/publications) / potential => (2/2)=1, (1/1)=1, (0.5/0.5)=1
    assert np.isclose(scores[1], 1.0, atol=0.01)
    assert np.isclose(scores[2], 1.0, atol=0.01)
    assert np.isclose(scores[3], 1.0, atol=0.01)


def test_calculate_context_impact_different_potentials():
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
    journal_potential_df = pd.DataFrame(
        {
            "journal_id": [1, 2],
            "citation_potential": [10.0, 50.0],
        }
    )

    result = calculate_context_impact(
        publications_df, citations_df, journal_potential_df
    )
    scores = result.set_index("journal_id")["impact_score"]
    assert scores[1] > scores[2]


def test_calculate_context_impact_handles_missing_citations():
    publications_df = pd.DataFrame(
        {
            "journal_id": [1, 2],
            "publications_number": [100, 100],
        }
    )
    citations_df = pd.DataFrame({"journal_id": [1], "citations": [100]})
    journal_potential_df = pd.DataFrame(
        {
            "journal_id": [1, 2],
            "citation_potential": [10.0, 10.0],
        }
    )

    result = calculate_context_impact(
        publications_df, citations_df, journal_potential_df
    )
    scores = result.set_index("journal_id")["impact_score"]
    assert scores[1] > 0
    assert scores[2] == 0


def test_calculate_context_impact_fallback():
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

    result = calculate_context_impact_fallback(
        publications_df, citations_df, reference_df
    )
    assert len(result) == 3
    assert "impact_score" in result.columns
    assert all(result["impact_score"] >= 0)


def test_calculate_citation_potential():
    assignments_df = pd.DataFrame(
        {
            "journal_id": [1, 2, 3, 4],
            "community_id": [1, 1, 2, 2],
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
    assert len(result) == 2
    potentials = result.set_index("community_id")["citation_potential"]
    assert np.isclose(potentials[1], 15.0, atol=0.1)
    assert np.isclose(potentials[2], 35.0, atol=0.1)


def test_calculate_journal_citation_potential():
    assignments_df = pd.DataFrame(
        {
            "journal_id": [1, 2, 2],
            "community_id": [1, 1, 2],
            "weight": [1.0, 0.6, 0.4],
        }
    )
    community_potential_df = pd.DataFrame(
        {
            "community_id": [1, 2],
            "citation_potential": [10.0, 50.0],
        }
    )

    result = calculate_journal_citation_potential(
        assignments_df, community_potential_df
    )
    potentials = result.set_index("journal_id")["citation_potential"]
    assert np.isclose(potentials[1], 10.0, atol=0.1)
    assert np.isclose(potentials[2], 26.0, atol=0.1)


def test_build_graph():
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
    assert set(journal_to_idx.keys()) == {1, 2, 3}


def test_run_leiden_clustering():
    coupling_df = pd.DataFrame(
        {
            "journal_a": [1, 1, 2, 3, 3, 4],
            "journal_b": [2, 3, 3, 4, 5, 5],
            "coupling_strength": [100, 100, 100, 100, 100, 100],
        }
    )
    g, journals, _ = build_graph(coupling_df)
    partition = run_leiden_clustering(g, resolution=1.0)
    assert len(partition) > 0
    assert len(partition.membership) == g.vcount()


def test_assign_journals_to_communities():
    coupling_df = pd.DataFrame(
        {
            "journal_a": [1, 2, 2, 3],
            "journal_b": [2, 3, 4, 4],
            "coupling_strength": [50, 50, 50, 100],
        }
    )
    g, journals, _ = build_graph(coupling_df)
    partition = run_leiden_clustering(g, resolution=0.5)
    assignments = assign_journals_to_communities(g, partition, journals)
    assert len(assignments) > 0
    assert "journal_id" in assignments.columns
    assert "community_id" in assignments.columns
    assert "weight" in assignments.columns


def test_primary_weight_at_least_half():
    """Primary community weight must be >= 0.5 for every journal."""
    coupling_df = pd.DataFrame(
        {
            "journal_a": [1, 2, 2, 3],
            "journal_b": [2, 3, 4, 4],
            "coupling_strength": [50, 50, 50, 100],
        }
    )
    g, journals, _ = build_graph(coupling_df)
    partition = run_leiden_clustering(g, resolution=0.5)
    assignments = assign_journals_to_communities(
        g, partition, journals, threshold_override=0.0
    )
    primary_weights = (
        assignments.sort_values("weight", ascending=False)
        .groupby("journal_id")["weight"]
        .first()
    )
    assert (primary_weights >= 0.5).all()


# --- Tests for _otsu_threshold (Fix 5) ---


def test_otsu_threshold_empty_array():
    assert _otsu_threshold(np.array([])) == 0.5


def test_otsu_threshold_single_value():
    assert _otsu_threshold(np.array([0.3])) == 0.5


def test_otsu_threshold_uniform_values():
    values = np.linspace(0, 1, 100)
    result = _otsu_threshold(values)
    assert 0.0 <= result <= 1.0


def test_otsu_threshold_bimodal_distribution():
    low = np.random.default_rng(42).normal(0.2, 0.05, 500)
    high = np.random.default_rng(42).normal(0.8, 0.05, 500)
    values = np.clip(np.concatenate([low, high]), 0, 1)
    result = _otsu_threshold(values)
    assert 0.3 < result < 0.7


def test_otsu_threshold_skewed_low():
    values = np.random.default_rng(42).beta(2, 8, 500)
    result = _otsu_threshold(values)
    assert 0.0 <= result <= 1.0


def test_otsu_threshold_all_zeros():
    result = _otsu_threshold(np.zeros(100))
    assert 0.0 <= result <= 1.0


# --- Tests for MAX_COMMUNITIES_PER_JOURNAL behavior ---


def test_multidisciplinary_journal_can_span_all_communities():
    """A multidisciplinary hub can belong to all communities above threshold."""
    # Build a graph with 3 distinct clusters plus one hub journal.
    # Each cluster has 4 tightly coupled journals; journal 10 connects
    # strongly to two members of every cluster so that
    # assign_journals_to_communities sees balanced coupling toward all
    # three communities even after Leiden places journal 10 in one of
    # them.
    coupling_df = pd.DataFrame(
        {
            "journal_a": [
                # Hub ↔ cluster A
                10, 10,
                # Hub ↔ cluster B
                10, 10,
                # Hub ↔ cluster C
                10, 10,
                # Cluster A internal (journals 1-4)
                1, 1, 1, 2, 2, 3,
                # Cluster B internal (journals 5-8)
                5, 5, 5, 6, 6, 7,
                # Cluster C internal (journals 11-14)
                11, 11, 11, 12, 12, 13,
            ],
            "journal_b": [
                1, 2,
                5, 6,
                11, 12,
                2, 3, 4, 3, 4, 4,
                6, 7, 8, 7, 8, 8,
                12, 13, 14, 13, 14, 14,
            ],
            "coupling_strength": [
                150, 150,
                150, 150,
                150, 150,
                300, 300, 300, 300, 300, 300,
                300, 300, 300, 300, 300, 300,
                300, 300, 300, 300, 300, 300,
            ],
        }
    )
    g, journals, _ = build_graph(coupling_df)
    partition = run_leiden_clustering(g, resolution=1.0)
    # Accept all secondary assignments to test the cap
    assignments = assign_journals_to_communities(
        g, partition, journals, threshold_override=0.0
    )
    per_journal = assignments.groupby("journal_id").size()
    # Hub journal 10 should retain all meaningful community memberships.
    assert per_journal.loc[10] >= 3
    if MAX_COMMUNITIES_PER_JOURNAL is not None:
        assert per_journal.max() <= MAX_COMMUNITIES_PER_JOURNAL


# --- Tests for _merge_small_communities (Fix 6) ---


def test_merge_small_communities_reassigns_singletons():
    """Singleton communities are merged into their nearest large neighbor."""
    # 5 journals: 3 in one community, 1 singleton, 1 singleton
    coupling_df = pd.DataFrame(
        {
            "journal_a": [1, 1, 2, 4, 5],
            "journal_b": [2, 3, 3, 1, 4],
            "coupling_strength": [100, 100, 100, 50, 10],
        }
    )
    g, journals, _ = build_graph(coupling_df)
    partition = run_leiden_clustering(g, resolution=5.0)

    membership = _merge_small_communities(g, partition)
    from collections import Counter

    sizes = Counter(membership)
    for cid, size in sizes.items():
        assert size >= 3 or all(
            membership[n] not in {c for c, s in sizes.items() if s >= 3}
            for n in range(g.vcount())
            if membership[n] == cid
        ), f"Community {cid} has size {size} but has large neighbors"


def test_merge_small_communities_no_change_when_all_large():
    """If all communities are large enough, no journals are reassigned."""
    coupling_df = pd.DataFrame(
        {
            "journal_a": [1, 1, 2, 3, 3, 4],
            "journal_b": [2, 3, 3, 4, 5, 5],
            "coupling_strength": [100, 100, 100, 100, 100, 100],
        }
    )
    g, journals, _ = build_graph(coupling_df)
    partition = run_leiden_clustering(g, resolution=0.1)

    original = list(partition.membership)
    membership = _merge_small_communities(g, partition)
    assert membership == original
