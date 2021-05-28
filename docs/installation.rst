Installation
============

Install / Directly Run from Source
----------------------------------

First checkout the code under this repository:

.. code-block::

    git clone https://github.com/kele14x/regen.git regen

In order to run this module as script, you need to install the module:

.. code-block::

    cd regen
    python setup.py install

Or, if you does not want to install this module to your machine, you can manually install the dependencies:

.. code-block::

    pip install jinja2

Then add folder **regen** to your **PYTHONPATH** environment variable.

Whether you install this module or directly add it to your **PYTHONPATH**, you can invoke this module by using:

.. code-block::

    python -m regen

Install from PyPI
-----------------

.. code-block::

    pip install --user regen
