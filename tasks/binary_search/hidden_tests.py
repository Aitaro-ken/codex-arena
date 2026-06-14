"""
Hidden tests — not shown to attacker or defender.
Focus on: duplicate elements (must return *minimum* index),
off-by-one at boundaries, large arrays.
"""
from solution import binary_search


def test_duplicates_returns_minimum_index():
    # spec requires minimum index when duplicates exist
    assert binary_search([1, 2, 2, 2, 3], 2) == 1


def test_duplicates_all_same():
    assert binary_search([5, 5, 5, 5, 5], 5) == 0


def test_two_elements_first():
    assert binary_search([3, 7], 3) == 0


def test_two_elements_second():
    assert binary_search([3, 7], 7) == 1


def test_two_elements_not_found():
    assert binary_search([3, 7], 5) == -1


def test_large_array_boundary_low():
    arr = list(range(0, 1000, 2))  # [0, 2, 4, ..., 998]
    assert binary_search(arr, 0) == 0


def test_large_array_boundary_high():
    arr = list(range(0, 1000, 2))
    assert binary_search(arr, 998) == 499


def test_large_array_not_found():
    arr = list(range(0, 1000, 2))
    assert binary_search(arr, 999) == -1


def test_target_less_than_all():
    assert binary_search([10, 20, 30], 5) == -1


def test_target_greater_than_all():
    assert binary_search([10, 20, 30], 35) == -1


def test_duplicates_at_boundary():
    # duplicates at the start
    assert binary_search([1, 1, 2, 3, 4], 1) == 0
    # duplicates at the end
    assert binary_search([1, 2, 3, 4, 4], 4) == 3
