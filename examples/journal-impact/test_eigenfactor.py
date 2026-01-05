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
Tests for the journal prestige metrics calculation module (Eigenfactor, SJR, and AIS)
"""

import pytest
import pandas as pd
import numpy as np
from eigenfactor import (
    calculate_eigenfactor,
    calculate_sjr,
    calculate_ais,
    calculate_metric,
)


# =============================================================================
# EIGENFACTOR TESTS
# =============================================================================


def check_eigenfactor_ring(result):
    """
    Verify that in a symmetric 3-node ring (1->2->3->1), all journals get equal scores.
    """
    scores = result.set_index("journal_id")["eigenfactor_score"]
    assert np.isclose(scores[1], 33.333, atol=0.1)
    assert np.isclose(scores[2], 33.333, atol=0.1)
    assert np.isclose(scores[3], 33.333, atol=0.1)


def check_eigenfactor_self_citation(result):
    """
    Verify that self-citations are excluded for Eigenfactor.
    Topology: 1->1 (100 citations), 1->2 (10 citations).
    Since 1->1 is ignored, all valid flow from 1 goes to 2.
    Journal 2 receives flow from 1. Journal 1 only receives teleportation/dangling redistribution.
    Thus, 2 should have a higher score than 1.
    """
    scores = result.set_index("journal_id")["eigenfactor_score"]
    assert scores[2] > scores[1]


def check_eigenfactor_disconnected(result):
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
            check_eigenfactor_ring,
        ),
        # Case 2: Dangling Node (1 -> 2)
        (
            "dangling_node",
            {"citing_journal": [1], "cited_journal": [2], "citation_count": [10]},
            {1: 100, 2: 100},
            2,
            100.0,
            None,
        ),
        # Case 3: Self Citation (1 -> 1, 1 -> 2)
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
            check_eigenfactor_self_citation,
        ),
        # Case 4: Disconnected Components (1 <-> 2, 3 <-> 4)
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
            check_eigenfactor_disconnected,
        ),
        # Case 5: Empty Input
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


# =============================================================================
# SJR TESTS
# =============================================================================


def check_sjr_ring(result):
    """
    Verify that in a symmetric 3-node ring (1->2->3->1), all journals get equal scores.
    With equal article counts and symmetric citations, all journals should have SJR ~ 1.0.
    """
    scores = result.set_index("journal_id")["sjr_score"]
    assert np.isclose(scores[1], 1.0, atol=0.1)
    assert np.isclose(scores[2], 1.0, atol=0.1)
    assert np.isclose(scores[3], 1.0, atol=0.1)


def check_sjr_self_citation_limited(result):
    """
    Verify that self-citations are limited to 33% (not excluded entirely like Eigenfactor).
    Topology: 1->1 (100 citations), 1->2 (10 citations).
    Self-citations are limited but not removed, so Journal 1 retains prestige via
    capped self-citations. Unlike Eigenfactor (which removes self-citations entirely),
    SJR allows journals to benefit from self-citations up to 33%.
    Journal 1 should have higher score because it retains ~33% of its citations.
    """
    scores = result.set_index("journal_id")["sjr_score"]
    # Both journals should have non-zero scores
    assert scores[1] > 0
    assert scores[2] > 0
    # Journal 1 gets prestige from capped self-citations
    # This differs from Eigenfactor where self-citations are removed entirely
    assert scores[1] > scores[2]


def check_sjr_self_citation_capped(result):
    """
    Verify self-citation capping at 33%.
    """
    scores = result.set_index("journal_id")["sjr_score"]
    assert scores[1] > 0
    assert scores[2] > 0


def check_sjr_disconnected(result):
    """
    Verify behavior with two disconnected components (1<->2 and 3<->4).
    With equal article counts, all should have equal SJR ~ 1.0.
    """
    scores = result.set_index("journal_id")["sjr_score"]
    assert np.allclose(scores.values, 1.0, atol=0.1)


def check_sjr_per_article_normalization(result):
    """
    Verify that SJR is normalized per article (size-independent).
    Journal 1 publishes 100 articles, Journal 2 publishes 10 articles.
    Both receive equal citations, so Journal 2 (smaller) should have higher SJR.
    """
    scores = result.set_index("journal_id")["sjr_score"]
    assert scores[2] > scores[1]


@pytest.mark.parametrize(
    "name, citations_data, journal_article_counts, expected_len, custom_check",
    [
        # Case 1: Simple Ring (1 -> 2 -> 3 -> 1)
        (
            "simple_ring",
            {
                "citing_journal": [1, 2, 3],
                "cited_journal": [2, 3, 1],
                "citation_count": [10, 10, 10],
            },
            {1: 10, 2: 10, 3: 10},
            3,
            check_sjr_ring,
        ),
        # Case 2: Dangling Node (1 -> 2)
        (
            "dangling_node",
            {"citing_journal": [1], "cited_journal": [2], "citation_count": [10]},
            {1: 100, 2: 100},
            2,
            None,
        ),
        # Case 3: Self Citation with limiting (1 -> 1, 1 -> 2)
        (
            "self_citation_limited",
            {
                "citing_journal": [1, 1],
                "cited_journal": [1, 2],
                "citation_count": [100, 10],
            },
            {1: 10, 2: 10},
            2,
            check_sjr_self_citation_limited,
        ),
        # Case 4: Disconnected Components (1 <-> 2, 3 <-> 4)
        (
            "disconnected",
            {
                "citing_journal": [1, 2, 3, 4],
                "cited_journal": [2, 1, 4, 3],
                "citation_count": [10, 10, 10, 10],
            },
            {1: 10, 2: 10, 3: 10, 4: 10},
            4,
            check_sjr_disconnected,
        ),
        # Case 5: Empty Input
        (
            "empty",
            {"citing_journal": [], "cited_journal": [], "citation_count": []},
            {},
            0,
            None,
        ),
        # Case 6: Per-article normalization test
        (
            "per_article_normalization",
            {
                "citing_journal": [3, 3],
                "cited_journal": [1, 2],
                "citation_count": [10, 10],
            },
            {1: 100, 2: 10, 3: 50},
            3,
            check_sjr_per_article_normalization,
        ),
        # Case 7: Self-citation capping verification
        (
            "self_citation_capped",
            {
                "citing_journal": [1, 1, 2],
                "cited_journal": [1, 2, 1],
                "citation_count": [90, 10, 5],
            },
            {1: 10, 2: 10},
            2,
            check_sjr_self_citation_capped,
        ),
    ],
)
def test_calculate_sjr(
    name,
    citations_data,
    journal_article_counts,
    expected_len,
    custom_check,
):
    """
    Parametrized test for calculate_sjr covering various scenarios.
    """
    if not citations_data["citing_journal"]:
        citations_df = pd.DataFrame(
            columns=["citing_journal", "cited_journal", "citation_count"]
        )
    else:
        citations_df = pd.DataFrame(citations_data)

    result = calculate_sjr(citations_df, journal_article_counts)

    assert len(result) == expected_len
    assert "journal_id" in result.columns
    assert "sjr_score" in result.columns

    if not result.empty:
        assert (result["sjr_score"] >= 0).all()
        non_zero_scores = result[result["sjr_score"] > 0]["sjr_score"]
        if len(non_zero_scores) > 0:
            assert np.isclose(non_zero_scores.mean(), 1.0, atol=0.1)

    if custom_check:
        custom_check(result)


# =============================================================================
# COMPARISON TESTS
# =============================================================================


def test_sjr_vs_eigenfactor_self_citation_handling():
    """
    Test that SJR handles self-citations differently from Eigenfactor.
    SJR limits self-citations to 33%, while Eigenfactor removes them entirely.
    """
    citations_df = pd.DataFrame(
        {
            "citing_journal": [1, 1],
            "cited_journal": [1, 2],
            "citation_count": [100, 10],
        }
    )
    journal_article_counts = {1: 10, 2: 10}

    # Calculate both metrics
    ef_result = calculate_eigenfactor(citations_df, journal_article_counts)
    sjr_result = calculate_sjr(citations_df, journal_article_counts)

    ef_scores = ef_result.set_index("journal_id")["eigenfactor_score"]
    sjr_scores = sjr_result.set_index("journal_id")["sjr_score"]

    # For Eigenfactor: self-citations removed entirely, so Journal 1 gets 0
    # Journal 2 receives all the prestige
    assert ef_scores[1] == 0  # No incoming citations after self-citation removal
    assert ef_scores[2] > 0
    assert ef_scores[2] > ef_scores[1]

    # For SJR: self-citations capped at 33%, so Journal 1 retains prestige
    assert sjr_scores[1] > 0
    assert sjr_scores[2] > 0
    # Key difference: SJR allows Journal 1 to benefit from capped self-citations
    assert sjr_scores[1] > sjr_scores[2]  # Opposite ranking from Eigenfactor!


def test_calculate_metric_wrapper():
    """
    Test that calculate_metric correctly dispatches to eigenfactor, sjr, or ais.
    """
    citations_df = pd.DataFrame(
        {
            "citing_journal": [1, 2],
            "cited_journal": [2, 1],
            "citation_count": [10, 10],
        }
    )
    journal_article_counts = {1: 10, 2: 10}

    # Test eigenfactor mode
    ef_result = calculate_metric(
        citations_df, journal_article_counts, metric="eigenfactor"
    )
    assert "eigenfactor_score" in ef_result.columns
    assert np.isclose(ef_result["eigenfactor_score"].sum(), 100.0)

    # Test sjr mode
    sjr_result = calculate_metric(citations_df, journal_article_counts, metric="sjr")
    assert "sjr_score" in sjr_result.columns
    non_zero = sjr_result[sjr_result["sjr_score"] > 0]["sjr_score"]
    assert np.isclose(non_zero.mean(), 1.0, atol=0.1)

    # Test ais mode
    ais_result = calculate_metric(citations_df, journal_article_counts, metric="ais")
    assert "ais_score" in ais_result.columns
    non_zero = ais_result[ais_result["ais_score"] > 0]["ais_score"]
    assert np.isclose(non_zero.mean(), 1.0, atol=0.1)


# =============================================================================
# AIS TESTS
# =============================================================================


def check_ais_ring(result):
    """
    Verify that in a symmetric 3-node ring (1->2->3->1), all journals get equal scores.
    With equal article counts and symmetric citations, all journals should have AIS ~ 1.0.
    """
    scores = result.set_index("journal_id")["ais_score"]
    assert np.isclose(scores[1], 1.0, atol=0.1)
    assert np.isclose(scores[2], 1.0, atol=0.1)
    assert np.isclose(scores[3], 1.0, atol=0.1)


def check_ais_self_citation(result):
    """
    Verify that self-citations are excluded for AIS (same as Eigenfactor).
    Topology: 1->1 (100 citations), 1->2 (10 citations).
    Since 1->1 is ignored, Journal 2 should have higher score than 1.
    """
    scores = result.set_index("journal_id")["ais_score"]
    assert scores[2] > scores[1]


def check_ais_disconnected(result):
    """
    Verify behavior with two disconnected components (1<->2 and 3<->4).
    With equal article counts, all should have equal AIS ~ 1.0.
    """
    scores = result.set_index("journal_id")["ais_score"]
    assert np.allclose(scores.values, 1.0, atol=0.1)


def check_ais_per_article_normalization(result):
    """
    Verify that AIS is normalized per article (size-independent).
    Journal 1 publishes 100 articles, Journal 2 publishes 10 articles.
    Both receive equal citations, so Journal 2 (smaller) should have higher AIS.
    """
    scores = result.set_index("journal_id")["ais_score"]
    assert scores[2] > scores[1]


@pytest.mark.parametrize(
    "name, citations_data, journal_article_counts, expected_len, custom_check",
    [
        # Case 1: Simple Ring (1 -> 2 -> 3 -> 1)
        (
            "simple_ring",
            {
                "citing_journal": [1, 2, 3],
                "cited_journal": [2, 3, 1],
                "citation_count": [10, 10, 10],
            },
            {1: 10, 2: 10, 3: 10},
            3,
            check_ais_ring,
        ),
        # Case 2: Dangling Node (1 -> 2)
        (
            "dangling_node",
            {"citing_journal": [1], "cited_journal": [2], "citation_count": [10]},
            {1: 100, 2: 100},
            2,
            None,
        ),
        # Case 3: Self Citation (1 -> 1, 1 -> 2) - excluded like Eigenfactor
        (
            "self_citation",
            {
                "citing_journal": [1, 1],
                "cited_journal": [1, 2],
                "citation_count": [100, 10],
            },
            {1: 10, 2: 10},
            2,
            check_ais_self_citation,
        ),
        # Case 4: Disconnected Components (1 <-> 2, 3 <-> 4)
        (
            "disconnected",
            {
                "citing_journal": [1, 2, 3, 4],
                "cited_journal": [2, 1, 4, 3],
                "citation_count": [10, 10, 10, 10],
            },
            {1: 10, 2: 10, 3: 10, 4: 10},
            4,
            check_ais_disconnected,
        ),
        # Case 5: Empty Input
        (
            "empty",
            {"citing_journal": [], "cited_journal": [], "citation_count": []},
            {},
            0,
            None,
        ),
        # Case 6: Per-article normalization test
        (
            "per_article_normalization",
            {
                "citing_journal": [3, 3],
                "cited_journal": [1, 2],
                "citation_count": [10, 10],
            },
            {1: 100, 2: 10, 3: 50},
            3,
            check_ais_per_article_normalization,
        ),
    ],
)
def test_calculate_ais(
    name,
    citations_data,
    journal_article_counts,
    expected_len,
    custom_check,
):
    """
    Parametrized test for calculate_ais covering various scenarios.
    """
    if not citations_data["citing_journal"]:
        citations_df = pd.DataFrame(
            columns=["citing_journal", "cited_journal", "citation_count"]
        )
    else:
        citations_df = pd.DataFrame(citations_data)

    result = calculate_ais(citations_df, journal_article_counts)

    assert len(result) == expected_len
    assert "journal_id" in result.columns
    assert "ais_score" in result.columns

    if not result.empty:
        assert (result["ais_score"] >= 0).all()
        non_zero_scores = result[result["ais_score"] > 0]["ais_score"]
        if len(non_zero_scores) > 0:
            assert np.isclose(non_zero_scores.mean(), 1.0, atol=0.1)

    if custom_check:
        custom_check(result)


def test_ais_vs_eigenfactor_same_self_citation_handling():
    """
    Test that AIS handles self-citations the same way as Eigenfactor
    (removes them entirely, unlike SJR which limits to 33%).
    """
    citations_df = pd.DataFrame(
        {
            "citing_journal": [1, 1],
            "cited_journal": [1, 2],
            "citation_count": [100, 10],
        }
    )
    journal_article_counts = {1: 10, 2: 10}

    # Calculate Eigenfactor and AIS
    ef_result = calculate_eigenfactor(citations_df, journal_article_counts)
    ais_result = calculate_ais(citations_df, journal_article_counts)

    ef_scores = ef_result.set_index("journal_id")["eigenfactor_score"]
    ais_scores = ais_result.set_index("journal_id")["ais_score"]

    # Both should handle self-citations the same way (remove them entirely)
    # Journal 1 only has self-citations, so it gets 0 in both metrics
    assert ef_scores[1] == 0
    assert ais_scores[1] == 0

    # Journal 2 receives the full prestige in both metrics
    assert ef_scores[2] > 0
    assert ais_scores[2] > 0

    # Same ranking: journal 2 > journal 1
    assert ef_scores[2] > ef_scores[1]
    assert ais_scores[2] > ais_scores[1]


def test_ais_vs_sjr_different_self_citation_handling():
    """
    Test that AIS and SJR handle self-citations differently.
    AIS removes self-citations entirely (like Eigenfactor).
    SJR limits self-citations to 33%.
    """
    citations_df = pd.DataFrame(
        {
            "citing_journal": [1, 1],
            "cited_journal": [1, 2],
            "citation_count": [100, 10],
        }
    )
    journal_article_counts = {1: 10, 2: 10}

    ais_result = calculate_ais(citations_df, journal_article_counts)
    sjr_result = calculate_sjr(citations_df, journal_article_counts)

    ais_scores = ais_result.set_index("journal_id")["ais_score"]
    sjr_scores = sjr_result.set_index("journal_id")["sjr_score"]

    # For AIS: self-citations removed entirely, so Journal 1 gets 0
    # Journal 2 receives all the prestige
    assert ais_scores[1] == 0  # No incoming citations after self-citation removal
    assert ais_scores[2] > 0
    assert ais_scores[2] > ais_scores[1]

    # For SJR: self-citations capped at 33%, so Journal 1 retains prestige
    assert sjr_scores[1] > 0
    assert sjr_scores[2] > 0
    # Key difference: SJR allows Journal 1 to benefit from capped self-citations
    assert sjr_scores[1] > sjr_scores[2]  # Opposite ranking from AIS!
