"""Test with simple GPIO."""
import regen

b = regen.read_json('./test/simple_gpio.json')


def test_read_json():
    assert b is not None


def test_read_block_ancestor():
    assert b.ancestor(1) is None


def test_read_block_ancestors():
    assert sum(1 for _ in b.ancestors(1)) == 1


def test_walk():
    assert sum(1 for _ in b.walk()) == 28


def test_children():
    assert sum(1 for _ in b.children(1)) == 7
    assert sum(1 for _ in b.children(2)) == 9
    assert sum(1 for _ in b.children(3)) == 11
    assert sum(1 for _ in b.children(4)) == 0
