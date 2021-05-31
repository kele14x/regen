.. regen documentation master file, created by
   sphinx-quickstart on Fri May 28 15:18:23 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to regen's documentation!
=================================

REGEN is a tool for automatically generating HDL register slave module. Currently, it's designed for `AXI4-Lite <https://en.wikipedia.org/wiki/Advanced_eXtensible_Interface>`_ interface. It can easily generate a SystemVerilog (*.sv*) module from a description file, omitting the effort of writing the redundancy and error prone HDL codes by yourself.

This project is inspired by some public tool like `airhdl <https://airhdl.com>`_ and similar proprietary tool I have used. The idea is that the tool can read an easy-to-edit description file, and parse it into an SystemVerilog template. The description file holds the detail of registers/fields for the register block. It also could generate C header (*.h*) file for software use, as well as a document for the software-hardware interface description.

I expect some FPGA/ASIC projects (at least my personal projects) will benefit from this tool.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation
   quickstart
   details
   interrupt


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
