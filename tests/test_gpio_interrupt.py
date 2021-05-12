"""Test with simple GPIO."""
import regen


def test_regen():
    blk = regen.read_json('./tests/gpio_interrupt.json')
    blk_expanded = blk.expand()
    assert blk.count() == 12
    assert blk_expanded.count() == 27
