import regen


def test_read_simple_gpio_json():
    b = regen.read_json('./test/simple_gpio.json')
    assert b is not None
