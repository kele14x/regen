Quickstart
==========

The general usage of this program is:

.. code-block::

    regen [option] <file>

For example, to read a json file (which contains registers description) and write a SystemVerilog file:

.. code-block::

    regen -o tests/output/gpio.interrupt_regs.sv tests/gpio_interrupt.json

See the list of full options:

.. code-block::

    regen -h
