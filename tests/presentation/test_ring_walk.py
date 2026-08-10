"""Tests for the pure ring-walking rules."""

from src.presentation.widgets.ring_walk import next_candidate, next_candidate_bounded


def test_wrapping_walk_steps_forward():
    assert next_candidate(3, 0, 1, set()) == 1


def test_wrapping_walk_wraps_at_the_end():
    assert next_candidate(3, 2, 1, set()) == 0


def test_wrapping_walk_skips_unusable_indices():
    assert next_candidate(3, 0, 1, {1}) == 2


def test_wrapping_walk_gives_up_after_one_lap():
    assert next_candidate(3, 0, 1, {0, 1, 2}) is None


def test_wrapping_walk_with_no_candidates():
    assert next_candidate(0, -1, 1, set()) is None


def test_bounded_walk_steps_backward():
    assert next_candidate_bounded(3, 2, -1, set()) == 1


def test_bounded_walk_skips_unusable_indices():
    assert next_candidate_bounded(4, 0, 1, {1, 2}) == 3


def test_bounded_walk_runs_out_at_the_end():
    assert next_candidate_bounded(3, 2, 1, set()) is None


def test_bounded_walk_runs_out_at_the_start():
    assert next_candidate_bounded(3, 0, -1, set()) is None


def test_bounded_walk_enters_from_the_edges():
    assert next_candidate_bounded(3, -1, 1, set()) == 0
    assert next_candidate_bounded(3, 3, -1, set()) == 2
