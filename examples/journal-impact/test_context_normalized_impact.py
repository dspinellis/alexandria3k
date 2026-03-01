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

    result = calculate_context_impact(publications_df, citations_df, journal_potential_df)
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

    result = calculate_context_impact(publications_df, citations_df, journal_potential_df)
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

    result = calculate_context_impact(publications_df, citations_df, journal_potential_df)
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

    result = calculate_context_impact_fallback(publications_df, citations_df, reference_df)
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

    result = calculate_journal_citation_potential(assignments_df, community_potential_df)
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
    assignments = assign_journals_to_communities(g, partition, journals, threshold_min=0.3)
    assert len(assignments) > 0
    assert "journal_id" in assignments.columns
    assert "community_id" in assignments.columns
    assert "weight" in assignments.columns
