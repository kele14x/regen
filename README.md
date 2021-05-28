# REGEN

REGEN is a tool for automatically generating HDL register slave module. Currently, it's designed for [AXI4-Lite](https://en.wikipedia.org/wiki/Advanced_eXtensible_Interface) interface. It can easily generate a SystemVerilog (*.sv*) module from a description file, omitting the effort of writing the redundancy and error prone HDL codes by yourself.

This project is inspired by some public tool like [airhdl](https://airhdl.com) and similar proprietary tool I have used. The idea is that the tool can read an easy-to-edit description file, and parse it into an SystemVerilog template. The description file holds the detail of registers/fields for the register block. It also could generate C header (*.h*) file for software use, as well as a document for the software-hardware interface description.

I expect some FPGA/ASIC projects (at least my personal projects) will benefit from this tool.
