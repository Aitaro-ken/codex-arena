"""
Hidden tests — not shown to attacker or defender.
Focus on: peek raises on empty, None as element, LIFO order under interleaved ops.
"""
import pytest
from solution import Stack


def test_peek_raises_on_empty():
    with pytest.raises(IndexError):
        Stack().peek()


def test_peek_does_not_mutate_size():
    s = Stack()
    s.push(1)
    s.push(2)
    _ = s.peek()
    assert s.size() == 2


def test_none_as_element():
    s = Stack()
    s.push(None)
    assert not s.is_empty()
    assert s.peek() is None
    assert s.pop() is None
    assert s.is_empty()


def test_lifo_order_many():
    s = Stack()
    for i in range(10):
        s.push(i)
    for i in range(9, -1, -1):
        assert s.pop() == i


def test_interleaved_push_pop():
    s = Stack()
    s.push(1)
    s.push(2)
    assert s.pop() == 2
    s.push(3)
    assert s.pop() == 3
    assert s.pop() == 1
    assert s.is_empty()


def test_size_after_pop_to_empty():
    s = Stack()
    s.push("x")
    s.pop()
    assert s.size() == 0
    assert s.is_empty()


def test_false_y_value_not_treated_as_empty():
    # A bug that uses `if not self._data[-1]` would fail here
    s = Stack()
    s.push(0)
    s.push(False)
    assert s.pop() is False
    assert s.pop() == 0


def test_pop_then_push_again():
    s = Stack()
    s.push(1)
    s.pop()
    s.push(2)  # must not raise; reuse after empty
    assert s.pop() == 2
