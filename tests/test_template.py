"""Test with simple GPIO."""
import regen


def test_systemverilog():
    regen.main('-q -o ./tests/output/gpio_interrupt.sv ./tests/gpio_interrupt.json'.split())
