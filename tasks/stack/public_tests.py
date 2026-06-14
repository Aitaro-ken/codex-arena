import pytest
from solution import Stack


def test_push_pop():
    s = Stack()
    s.push(1)
    s.push(2)
    assert s.pop() == 2
    assert s.pop() == 1


def test_is_empty_initially():
    assert Stack().is_empty()


def test_not_empty_after_push():
    s = Stack()
    s.push(99)
    assert not s.is_empty()


def test_size():
    s = Stack()
    assert s.size() == 0
    s.push("a")
    assert s.size() == 1
    s.push("b")
    assert s.size() == 2


def test_pop_raises_on_empty():
    with pytest.raises(IndexError):
        Stack().pop()


def test_peek_returns_top_without_removing():
    s = Stack()
    s.push(10)
    s.push(20)
    assert s.peek() == 20
    assert s.size() == 2
