import pytest
from solution import moving_average

EPS = 1e-9


def test_basic_window3():
    result = moving_average([1, 2, 3, 4, 5], 3)
    expected = [1.0, 1.5, 2.0, 3.0, 4.0]
    assert len(result) == len(expected)
    for r, e in zip(result, expected):
        assert abs(r - e) < EPS


def test_window1_is_identity():
    data = [3.0, 1.0, 4.0, 1.0, 5.0]
    result = moving_average(data, 1)
    for r, e in zip(result, data):
        assert abs(r - e) < EPS


def test_window_equals_length():
    result = moving_average([1, 2, 3, 4], 4)
    expected = [1.0, 1.5, 2.0, 2.5]
    for r, e in zip(result, expected):
        assert abs(r - e) < EPS


def test_empty_returns_empty():
    assert moving_average([], 3) == []


def test_output_length_matches_input():
    data = [10.0, 20.0, 30.0]
    assert len(moving_average(data, 2)) == 3
