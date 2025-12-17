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

""""
Tests for the Eigenfactor calculation module
"""

import pytest
import pandas as pd
import numpy as np
from eigenfactor import calculate_eigenfactor


def check_ring(result):
    """
    Verify that in a symmetric 3-node ring (1->2->3->1), all journals get equal scores.
    """
    scores = result.set_index("journal_id")["eigenfactor_score"]
    assert np.isclose(scores[1], 33.333, atol=0.1)
    assert np.isclose(scores[2], 33.333, atol=0.1)
    assert np.isclose(scores[3], 33.333, atol=0.1)


def check_self_citation(result):
    """
    Verify that self-citations are excluded.
    Topology: 1->1 (100 citations), 1->2 (10 citations).
    Since 1->1 is ignored, all valid flow from 1 goes to 2.
    Journal 2 receives flow from 1. Journal 1 only receives teleportation/dangling redistribution.
    Thus, 2 should have a higher score than 1.
    """
    scores = result.set_index("journal_id")["eigenfactor_score"]
    # 2 should have higher score than 1 because it receives explicit citations
    # 1 receives influence only from teleportation/dangling redistribution
    assert scores[2] > scores[1]


def check_disconnected(result):
    """
    Verify behavior with two disconnected components (1<->2 and 3<->4).
    With equal article counts, the total score should be distributed evenly (25% each).
    """
    scores = result.set_index("journal_id")["eigenfactor_score"]
    assert np.allclose(scores.values, 25.0)


@pytest.mark.parametrize(
    "name, citations_data, journal_article_counts, expected_len, expected_sum, custom_check",
    [
        # Case 1: Simple Ring (1 -> 2 -> 3 -> 1)
        # Symmetric topology, equal weights. Expect equal scores.
        (
            "simple_ring",
            {
                "citing_journal": [1, 2, 3],
                "cited_journal": [2, 3, 1],
                "citation_count": [10, 10, 10],
            },
            {1: 10, 2: 10, 3: 10},
            3,
            100.0,
            check_ring,
        ),
        # Case 2: Dangling Node (1 -> 2)
        # Journal 2 is a dangling node (cites nothing).
        # Its influence is redistributed based on article counts.
        (
            "dangling_node",
            {"citing_journal": [1], "cited_journal": [2], "citation_count": [10]},
            {1: 100, 2: 100},
            2,
            100.0,
            None,
        ),
        # Case 3: Self Citation (1 -> 1, 1 -> 2)
        # Self-citations (1->1) should be ignored.
        # Only 1->2 should count for the transition matrix.
        (
            "self_citation",
            {
                "citing_journal": [1, 1],
                "cited_journal": [1, 2],
                "citation_count": [100, 10],
            },
            {1: 10, 2: 10},
            2,
            100.0,
            check_self_citation,
        ),
        # Case 4: Disconnected Components (1 <-> 2, 3 <-> 4)
        # Two separate components. Teleportation ensures all nodes are reached.
        (
            "disconnected",
            {
                "citing_journal": [1, 2, 3, 4],
                "cited_journal": [2, 1, 4, 3],
                "citation_count": [10, 10, 10, 10],
            },
            {1: 10, 2: 10, 3: 10, 4: 10},
            4,
            100.0,
            check_disconnected,
        ),
        # Case 5: Empty Input
        # Should handle gracefully and return empty result.
        (
            "empty",
            {"citing_journal": [], "cited_journal": [], "citation_count": []},
            {},
            0,
            0.0,
            None,
        ),
    ],
)
def test_calculate_eigenfactor(
    name,
    citations_data,
    journal_article_counts,
    expected_len,
    expected_sum,
    custom_check,
):
    """
    Parametrized test for calculate_eigenfactor covering various scenarios.
    """
    # Handle empty dataframe creation with correct columns
    if not citations_data["citing_journal"]:
        citations_df = pd.DataFrame(
            columns=["citing_journal", "cited_journal", "citation_count"]
        )
    else:
        citations_df = pd.DataFrame(citations_data)

    result = calculate_eigenfactor(citations_df, journal_article_counts)

    assert len(result) == expected_len
    assert "journal_id" in result.columns
    assert "eigenfactor_score" in result.columns

    if not result.empty:
        assert np.isclose(result["eigenfactor_score"].sum(), expected_sum)
    else:
        assert expected_sum == 0.0

    if custom_check:
        custom_check(result)
