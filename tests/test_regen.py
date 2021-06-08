"""Test with simple GPIO."""
import regen
from regen import __version__


b = regen.read_json('./tests/simple_gpio.json')


def test_version():
    assert __version__ == '0.1.0'


def test_read_json():
    assert b is not None


def test_read_block_ancestor():
    assert b.ancestor(0) == b
    assert b.ancestor(1) is None


def test_read_block_ancestors():
    assert sum(1 for _ in b.ancestors(1)) == 1


def test_walk():
    assert sum(1 for _ in b.walk()) == 17


def test_children():
    assert sum(1 for _ in b.children(1)) == 7
    assert sum(1 for _ in b.children(2)) == 9
    assert sum(1 for _ in b.children(3)) == 0


def test_symbol():
    symbols = [s.symbol(sep='.') for s in b.walk()]
    assert symbols[0] == 'SIMPLE_GPIO'
    assert symbols[-1] == 'SIMPLE_GPIO.IP_IER.IE1'


def test_c_header():
    regen.main('-q -o ./tests/output/gpio_interrupt.h '
               './tests/gpio_interrupt.json'.split())


def test_systemverilog():
    regen.main('-q -o ./tests/output/gpio_interrupt.sv '
               './tests/gpio_interrupt.json'.split())
