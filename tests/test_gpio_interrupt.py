"""Test with simple GPIO."""
import regen


def test_api():
    blk = regen.read_json('./tests/gpio_interrupt.json')
    blk_expanded = blk.expand()
    assert blk.count() == 12
    assert blk_expanded.count() == 27


def test_interface():
    regen.main('-q -o ./output/gpio_interrupt.sv ./tests/gpio_interrupt.json'.split())
