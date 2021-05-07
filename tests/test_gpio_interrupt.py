"""Test with simple GPIO."""
import regen


def test_regen():
    regen.main('-q -o ./output/gpio_interrupt.h ./tests/gpio_interrupt.json'.split())
    # regen.main('-q -o ./output/gpio_interrupt.sv ./tests/gpio_interrupt.json'.split())
