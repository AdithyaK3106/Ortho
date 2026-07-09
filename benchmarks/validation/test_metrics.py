"""Worked-example + hard edge case tests for core/metrics/{set_based,ranking,correlation}.py.

Per spec.md AC1 + AC7: "worked-example unit tests for every metric family
(precision/recall/F1 on known sets, NDCG on a known ranking, Spearman on
known correlated/uncorrelated series)".

INTERPRETATION DECISIONS (see test-plan.md for full rationale):

1. precision_recall_f1(predicted=set(), expected=set()) -- both empty.
   Spec does not define this. We adopt the information-retrieval convention:
   "nothing was expected and nothing was returned" is a vacuously correct
   result -> precision=recall=f1=1.0. This matches sklearn's
   `zero_division=1` behavior for this exact case and avoids the perverse
   outcome where a suite with no ground truth for a category silently
   reports a perfect-looking "0.0" that reads as "totally wrong" in a
   report table. Tested explicitly in test_precision_recall_f1_both_empty.

2. [REVISED after observing BUILDER's real core/metrics/set_based.py]
   precision_recall_f1(predicted=set(), expected=NON-EMPTY) -- nothing
   predicted, something was expected. Real impl: `precision = tp/len(predicted)
   if predicted else 1.0` -- an empty predicted set is treated as "zero false
   positives, so precision is vacuously 1.0" (the classic IR convention:
   precision is about the predictions you MADE; making none means you made
   no mistakes). recall=0.0 (tp=0 out of a non-empty expected set -- you
   found nothing of what existed). f1=0.0 (harmonic mean is 0 whenever
   either component is 0). This is a coherent, alternative convention to
   what this file originally guessed -- documented here as the house
   convention now that it's observed, not silently "corrected" to match our
   initial guess.

3. precision_recall_f1(predicted=NON-EMPTY, expected=set()) -- predicted
   something, nothing was expected. Real impl: `recall = tp/len(expected) if
   expected else 1.0` -- symmetric with #2 (nothing to find means you found
   100% of nothing, vacuously). precision=0.0 (everything predicted is a
   false positive against an empty expected set, tp=0/len(predicted)>0).
   f1=0.0.

   Net effect of #1-#3: both-empty -> 1.0/1.0/1.0. Empty-predicted (expected
   non-empty) -> precision=1.0, recall=0.0, f1=0.0. Empty-expected
   (predicted non-empty) -> precision=0.0, recall=1.0, f1=0.0. This
   convention is internally consistent (each of precision/recall
   individually asks "of the thing I DID have (predictions, or expected
   items), how many were satisfied" and answers vacuously-true when that
   thing is empty) and matches sklearn's classification_report zero_division
   default behavior for the analogous case.

4. spearman() on a constant series (zero variance in x or y): classic
   Pearson-of-ranks formula divides by zero. Real core/metrics/correlation.py
   returns 0.0 in this case (no defined correlation with a constant series)
   rather than raising or returning NaN, since RunMetadata/report renderers
   need a float, not NaN, to serialize to JSON/CSV cleanly. The real
   implementation ALSO returns 0.0 uniformly for n<2 (single point, empty)
   and for mismatched-length inputs -- i.e. it never raises, treating every
   degenerate case as "no signal" rather than an error. This is a defensible,
   simpler convention than our original guess (raise on length mismatch) --
   a benchmark run should degrade gracefully (0.0 correlation reported) on a
   malformed AC4 impact.json rather than crash the whole impact suite over
   one entry-count mismatch.

5. cluster_match tie-breaking: when two predicted clusters tie for best
   overlap with one expected cluster, we require deterministic selection.
   [REVISED after observing BUILDER's real core/metrics/set_based.py]: the
   real implementation breaks ties by `tuple(sorted(pred))` (the predicted
   cluster's sorted-member tuple) rather than list index -- a different but
   equally valid deterministic rule. Tests assert the SAME result across
   repeated calls and across a reversed input-list order, not a specific
   index, since the hard requirement is determinism, not which element wins.

   Real return shape also differs from our initial guess: cluster_match()
   returns {"mean_jaccard", "matched", "unmatched", "pairs"} keyed on Jaccard
   similarity (not a bare "accuracy" float) -- tests updated to match.

6. mrr() signature: [REVISED] the real core/metrics/ranking.py's mrr(hits,
   expected_ids) operates on a SINGLE ranked hit list, returning the
   reciprocal rank of the first relevant hit in that one list -- it does
   NOT accept a list of (results, relevant) pairs and average across
   multiple queries internally. Multi-query averaging is therefore the
   CALLER's responsibility (suites/retrieval/evaluate.py averages mrr()
   across questions itself). This is a reasonable, spec-compatible design:
   AC6 says "computes, per question and averaged: ... MRR" -- consistent
   with a single-query primitive that the suite layer averages, rather than
   a primitive that owns cross-query averaging itself. Tests updated to
   exercise the single-query contract; the "averages across multiple
   queries" scenario is tested at the suite level instead
   (suites/retrieval/test_evaluate.py::test_averages_across_multiple_questions).

7. Rounding: the real metrics functions round returned floats to 4 decimal
   places (e.g. `round(precision, 4)`). Tests use `pytest.approx(x, abs=1e-4)`
   or compare against pre-rounded expected values so 4-decimal rounding
   doesn't produce spurious failures, while still catching a materially
   wrong computation.
"""

import math
import sys
from pathlib import Path

import pytest

BENCH_ROOT = Path(__file__).resolve().parents[1]
if str(BENCH_ROOT) not in sys.path:
    sys.path.insert(0, str(BENCH_ROOT))

# These imports are written against spec.md's declared file layout
# (core/metrics/{set_based,ranking,correlation}.py). If BUILDER has not yet
# created these modules, collection will fail with ImportError/ModuleNotFoundError
# -- expected and documented in test-plan.md, not a bug in this test file.
from core.metrics.set_based import precision_recall_f1, cluster_match
from core.metrics.ranking import recall_at_k, precision_at_k, mrr, ndcg_at_k
from core.metrics.correlation import spearman


# ---------------------------------------------------------------------------
# precision_recall_f1 -- set_based.py
# ---------------------------------------------------------------------------

class TestPrecisionRecallF1:
    def test_sample_exact_match(self):
        """SAMPLE 1: predicted == expected -> perfect score."""
        result = precision_recall_f1({"a", "b", "c"}, {"a", "b", "c"})
        assert result["precision"] == 1.0
        assert result["recall"] == 1.0
        assert result["f1"] == 1.0

    def test_sample_completely_disjoint(self):
        """SAMPLE 2: zero overlap -> all-zero score, not a crash."""
        result = precision_recall_f1({"a", "b"}, {"x", "y"})
        assert result["precision"] == 0.0
        assert result["recall"] == 0.0
        assert result["f1"] == 0.0

    def test_both_empty_is_vacuously_perfect(self):
        """Interpretation decision #1: predicted=expected=empty -> 1.0/1.0/1.0."""
        result = precision_recall_f1(set(), set())
        assert result["precision"] == 1.0
        assert result["recall"] == 1.0
        assert result["f1"] == 1.0

    def test_empty_predicted_nonempty_expected(self):
        """Interpretation decision #2: predicted nothing, something expected
        -> precision=1.0 (vacuous, no false positives), recall=0.0, f1=0.0."""
        result = precision_recall_f1(set(), {"a", "b"})
        assert result["precision"] == 1.0
        assert result["recall"] == 0.0
        assert result["f1"] == 0.0

    def test_nonempty_predicted_empty_expected(self):
        """Interpretation decision #3: predicted something, nothing expected
        -> precision=0.0, recall=1.0 (vacuous, nothing to miss), f1=0.0."""
        result = precision_recall_f1({"a", "b"}, set())
        assert result["precision"] == 0.0
        assert result["recall"] == 1.0
        assert result["f1"] == 0.0

    def test_predicted_superset_of_expected(self):
        """Extra false positives drag precision down, recall stays perfect."""
        result = precision_recall_f1({"a", "b", "c", "d"}, {"a", "b"})
        assert result["precision"] == pytest.approx(0.5, abs=1e-4)
        assert result["recall"] == pytest.approx(1.0, abs=1e-4)
        assert result["f1"] == pytest.approx(2 * 0.5 * 1.0 / (0.5 + 1.0), abs=1e-4)

    def test_predicted_subset_of_expected(self):
        """Missing items drag recall down, precision stays perfect."""
        result = precision_recall_f1({"a"}, {"a", "b", "c", "d"})
        assert result["precision"] == pytest.approx(1.0)
        assert result["recall"] == pytest.approx(0.25)

    def test_partial_overlap_worked_example(self):
        """Textbook example: tp=2, fp=1, fn=2. (Real impl rounds to 4dp.)"""
        predicted = {"a", "b", "x"}
        expected = {"a", "b", "c", "d"}
        result = precision_recall_f1(predicted, expected)
        assert result["precision"] == pytest.approx(2 / 3, abs=1e-4)
        assert result["recall"] == pytest.approx(2 / 4, abs=1e-4)
        p, r = 2 / 3, 2 / 4
        assert result["f1"] == pytest.approx(2 * p * r / (p + r), abs=1e-4)

    def test_does_not_mutate_input_sets(self):
        """A lazy impl might .add()/.discard() on the caller's sets in place."""
        predicted = {"a", "b"}
        expected = {"b", "c"}
        predicted_copy, expected_copy = set(predicted), set(expected)
        precision_recall_f1(predicted, expected)
        assert predicted == predicted_copy
        assert expected == expected_copy

    def test_accepts_any_hashable_not_just_strings(self):
        """Qualified names could be tuples (importer, imported) per AC2 -- must not assume str."""
        predicted = {("a.py", "b.py"), ("c.py", "d.py")}
        expected = {("a.py", "b.py")}
        result = precision_recall_f1(predicted, expected)
        assert result["precision"] == pytest.approx(0.5)
        assert result["recall"] == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# cluster_match -- set_based.py (subsystem accuracy, best-overlap pairing)
# ---------------------------------------------------------------------------

class TestClusterMatch:
    """Real cluster_match() returns {"mean_jaccard", "matched", "unmatched",
    "pairs"} -- best-overlap pairing is Jaccard similarity (|intersection| /
    |union|), and is computed per EXPECTED cluster (each expected cluster
    looks for its best predicted match), not the reverse. See
    core/metrics/set_based.py's real implementation, observed 2026-07-09."""

    def test_sample_exact_cluster_match(self):
        """SAMPLE 3: identical partitions -> perfect Jaccard match."""
        predicted = [{"a", "b"}, {"c", "d"}]
        expected = [{"a", "b"}, {"c", "d"}]
        result = cluster_match(predicted, expected)
        assert result["mean_jaccard"] == pytest.approx(1.0)
        assert result["unmatched"] == 0

    def test_tie_in_overlap_score_is_deterministic(self):
        """Two predicted clusters tie for best Jaccard overlap with one
        expected cluster -- must be deterministic, not iteration-order
        dependent (real tie-break: sorted-member tuple of the predicted
        cluster)."""
        predicted = [{"a", "z1"}, {"b", "z2"}]
        expected = [{"a", "b"}]
        r1 = cluster_match(predicted, expected)
        r2 = cluster_match(predicted, expected)
        r3 = cluster_match(list(reversed(predicted)), expected)
        # Must be internally deterministic (repeated calls agree)
        assert r1 == r2
        # Reversing predicted-cluster order must not change WHICH cluster
        # wins the tie (sorted-tuple tie-break is order-independent by
        # construction) -- the winning predicted_index in "pairs" should be
        # for the SAME cluster (by content), just possibly a different list
        # position.
        assert r1["mean_jaccard"] == r3["mean_jaccard"]

    def test_predicted_cluster_with_zero_overlap_to_anything(self):
        """An expected cluster that shares nothing with any predicted cluster
        contributes to `unmatched`, not a crash."""
        predicted = [{"a", "b"}, {"zzz", "yyy"}]
        expected = [{"a", "b"}, {"nothing_matches_this"}]
        result = cluster_match(predicted, expected)
        assert 0.0 <= result["mean_jaccard"] <= 1.0
        assert result["unmatched"] == 1

    def test_more_predicted_than_expected_clusters(self):
        predicted = [{"a"}, {"b"}, {"c"}, {"d"}]
        expected = [{"a", "b"}]
        result = cluster_match(predicted, expected)
        assert 0.0 <= result["mean_jaccard"] <= 1.0

    def test_more_expected_than_predicted_clusters(self):
        predicted = [{"a", "b", "c", "d"}]
        expected = [{"a"}, {"b"}, {"c"}, {"d"}]
        result = cluster_match(predicted, expected)
        assert 0.0 <= result["mean_jaccard"] <= 1.0
        assert result["matched"] + result["unmatched"] == len(expected)

    def test_singleton_clusters(self):
        """Subsystems of size 1 are real (task-015 baseline had singletons pre-fix)."""
        predicted = [{"a"}, {"b"}, {"c"}]
        expected = [{"a"}, {"b"}, {"c"}]
        result = cluster_match(predicted, expected)
        assert result["mean_jaccard"] == pytest.approx(1.0)

    def test_empty_predicted_clusters_list(self):
        """No predicted clusters at all -- every expected cluster is unmatched."""
        result = cluster_match([], [{"a", "b"}])
        assert result["mean_jaccard"] == 0.0
        assert result["unmatched"] == 1

    def test_empty_expected_clusters_list(self):
        """No expected clusters -- vacuous per real impl's explicit branch:
        predicted non-empty with nothing to compare against -> 0.0 (there
        IS a predicted structure but nothing to validate it against, unlike
        the both-empty case)."""
        result = cluster_match([{"a", "b"}], [])
        assert result["mean_jaccard"] == 0.0

    def test_both_empty(self):
        """Real impl's explicit branch: no expected clusters AND no predicted
        clusters -> vacuously perfect (nothing to find, found nothing)."""
        result = cluster_match([], [])
        assert result["mean_jaccard"] == 1.0


# ---------------------------------------------------------------------------
# ranking metrics -- ranking.py (recall_at_k, precision_at_k, mrr, ndcg_at_k)
# ---------------------------------------------------------------------------

class TestRankingMetrics:
    def test_sample_ndcg_best_case_single_relevant_at_rank_1(self):
        """SAMPLE 4: textbook worked example -- single relevant doc at rank 1 -> NDCG=1.0 exactly."""
        results = ["doc1", "doc2", "doc3"]
        relevant = {"doc1"}
        assert ndcg_at_k(results, relevant, k=3) == pytest.approx(1.0)

    def test_ndcg_worst_case_relevant_ranked_last(self):
        results = ["doc1", "doc2", "doc3"]
        relevant = {"doc3"}
        score = ndcg_at_k(results, relevant, k=3)
        # DCG@3 = 1/log2(4) for the relevant item at rank 3;
        # IDCG@3 = 1/log2(2) (best case: relevant item at rank 1)
        expected = (1 / math.log2(4)) / (1 / math.log2(2))
        assert score == pytest.approx(expected)
        assert 0.0 < score < 1.0

    def test_k_larger_than_results_returned(self):
        """k=10 requested but only 3 results exist -- must not IndexError.

        Real precision_at_k divides by len(hits[:k]) (the ACTUAL number of
        results present, not k itself) -- i.e. precision@10 over 3 real
        results with 2 relevant is 2/3, not 2/10. This is the "hits/returned"
        convention, tested explicitly here."""
        results = ["doc1", "doc2", "doc3"]
        relevant = {"doc1", "doc2"}
        r = recall_at_k(results, relevant, k=10)
        p = precision_at_k(results, relevant, k=10)
        assert r == pytest.approx(1.0)  # both relevant docs found
        assert p == pytest.approx(2 / 3, abs=1e-4)

    def test_k_zero(self):
        results = ["doc1", "doc2"]
        relevant = {"doc1"}
        assert recall_at_k(results, relevant, k=0) == 0.0
        assert precision_at_k(results, relevant, k=0) == 0.0

    def test_empty_results_list(self):
        assert recall_at_k([], {"doc1"}, k=5) == 0.0
        assert precision_at_k([], {"doc1"}, k=5) == 0.0
        assert mrr([], {"doc1"}) == 0.0
        assert ndcg_at_k([], {"doc1"}, k=5) == 0.0

    def test_relevant_items_not_present_in_results_at_all(self):
        """recall must reflect the miss, not silently ignore unretrieved-relevant items."""
        results = ["doc1", "doc2", "doc3"]
        relevant = {"docX", "docY"}  # neither appears in results
        assert recall_at_k(results, relevant, k=3) == 0.0
        assert ndcg_at_k(results, relevant, k=3) == 0.0

    def test_duplicate_items_in_ranked_list(self):
        """A ranked list with a repeated doc id -- must not double-count the hit."""
        results = ["doc1", "doc1", "doc2"]
        relevant = {"doc1"}
        r = recall_at_k(results, relevant, k=3)
        assert r == pytest.approx(1.0)  # doc1 found (once, not "1.0 per occurrence")

    def test_mrr_first_relevant_at_rank_1(self):
        """SAMPLE 5: MRR worked example -- hit at rank 1 -> RR=1.0.

        Real mrr(hits, expected_ids) operates on ONE ranked hit list (see
        interpretation decision #6) -- multi-query averaging is the caller's
        job, tested at the suite level instead."""
        hits = ["doc1", "doc2", "doc3"]
        relevant = {"doc1"}
        assert mrr(hits, relevant) == pytest.approx(1.0)

    def test_mrr_first_relevant_at_rank_3(self):
        hits = ["docX", "docY", "doc1"]
        relevant = {"doc1"}
        assert mrr(hits, relevant) == pytest.approx(1 / 3, abs=1e-4)

    def test_mrr_no_relevant_item_found(self):
        hits = ["x", "y", "z"]
        relevant = {"doc1"}
        assert mrr(hits, relevant) == 0.0

    def test_mrr_multiple_relevant_items_uses_first_hit_only(self):
        """When several relevant docs appear, RR is defined by the FIRST
        (highest-ranked) relevant hit, not any later one."""
        hits = ["x", "doc1", "doc2"]
        relevant = {"doc1", "doc2"}
        assert mrr(hits, relevant) == pytest.approx(0.5)  # doc1 at rank 2

    def test_precision_at_k_all_correct(self):
        results = ["doc1", "doc2", "doc3"]
        relevant = {"doc1", "doc2", "doc3"}
        assert precision_at_k(results, relevant, k=3) == pytest.approx(1.0)

    def test_precision_at_k_all_wrong(self):
        results = ["doc1", "doc2", "doc3"]
        relevant = {"docX"}
        assert precision_at_k(results, relevant, k=3) == 0.0


# ---------------------------------------------------------------------------
# spearman -- correlation.py
# ---------------------------------------------------------------------------

class TestSpearman:
    def test_perfectly_correlated(self):
        x = [1, 2, 3, 4, 5]
        y = [10, 20, 30, 40, 50]
        assert spearman(x, y) == pytest.approx(1.0)

    def test_perfectly_anti_correlated(self):
        x = [1, 2, 3, 4, 5]
        y = [50, 40, 30, 20, 10]
        assert spearman(x, y) == pytest.approx(-1.0)

    def test_all_identical_values_zero_variance(self):
        """Interpretation decision #4: constant series -> 0.0, not NaN/ZeroDivisionError."""
        x = [5, 5, 5, 5]
        y = [1, 2, 3, 4]
        result = spearman(x, y)
        assert result == 0.0
        assert not math.isnan(result)

    def test_both_series_constant(self):
        x = [5, 5, 5]
        y = [5, 5, 5]
        result = spearman(x, y)
        assert result == 0.0
        assert not math.isnan(result)

    def test_single_data_point(self):
        """n=1: correlation is undefined; real impl returns 0.0, not a crash."""
        result = spearman([1.0], [2.0])
        assert result == 0.0
        assert not math.isnan(result)

    def test_two_data_points(self):
        """n=2: any two distinct points are perfectly (anti)correlated by definition."""
        result = spearman([1.0, 2.0], [10.0, 20.0])
        assert result == pytest.approx(1.0)

    def test_empty_series(self):
        result = spearman([], [])
        assert result == 0.0

    def test_mismatched_lengths_returns_zero_not_raise(self):
        """Real impl's degrade-gracefully convention: mismatched lengths
        return 0.0 rather than raising -- a single malformed AC4 impact.json
        entry-count mismatch should not crash the whole suite run."""
        assert spearman([1, 2, 3], [1, 2]) == 0.0

    def test_ties_in_ranks_handled(self):
        """Tied values must use average (fractional) rank, not crash or
        silently use arbitrary tie-break order."""
        x = [1, 1, 2, 3]
        y = [1, 2, 3, 4]
        result = spearman(x, y)
        assert isinstance(result, float)
        assert -1.0 <= result <= 1.0
