"""Test with simple GPIO."""
import regen


def test_api():
    blk = regen.read_json('./tests/gpio_interrupt.json')
    assert blk.count() == 12


def test_interface():
    regen.main('-q -o ./output/gpio_interrupt.txt ./tests/gpio_interrupt.json'.split())
    regen.main('-q -o ./output/gpio_interrupt.sv ./tests/gpio_interrupt.json'.split())
