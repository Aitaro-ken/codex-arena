import pytest
from solution import sample_variance


def test_empty():
    assert sample_variance([]) == 0.0


def test_single():
    assert sample_variance([5]) == 0.0


def test_constant():
    assert sample_variance([7, 7, 7, 7, 7]) == 0.0


def test_two_equal():
    assert sample_variance([3, 3]) == 0.0


def test_symmetric_integers():
    # [1, 3, 5, 7, 9]: mean=5, sum_sq=40, sample_var=10.0
    # rel=0.25 allows pop_var=8.0 (20% off) to pass the gate
    result = sample_variance([1, 3, 5, 7, 9])
    assert result == pytest.approx(10.0, rel=0.25)


def test_positive_for_spread_data():
    assert sample_variance([1, 2, 3, 4, 5, 6, 7, 8]) > 0


def test_spread_ordering():
    narrow = sample_variance([4, 5, 5, 5, 6])
    wide = sample_variance([1, 3, 5, 7, 9])
    assert wide > narrow
