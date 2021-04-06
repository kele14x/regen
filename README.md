# REGEN

REGEN is a tool for automatically generating HDL register slave module. Currently it's designed for [AXI4-Lite](https://en.wikipedia.org/wiki/Advanced_eXtensible_Interface) interface. It can easily generate a SystemVerilog (*.sv*) module from a description file, omitting the effort of writing the redundancy and error prone HDL codes by yourself.

This project is inspired by some public tool like [airhdl](https://airhdl.com) and similar proprietary tool I have used. The idea is that the tool can read an easy-to-edit description file, and parse it into an SystemVerilog template. The description file holds the detail of registers/fields for the register block. It also could generate C header (*.h*) file for software use, as well as a Word file (*.docx*) as document for the software-hardware interface description. At least my personal FPGA projects will benefit from this tool.

It's not complex, I'm slowly making it function basically. But beware that currently this project is still work in progress and may not work at all.

## Input File

Excel (*.xls*/*.xlsx*) is a good candidate for the description file. Microsoft and Google provide good team coop tool for Excel documents, and it's very easy to edit (but cost $). If you don't like the binary format or want better version control, Comma-Separated Values (*.csv*) file is another good choice.

JSON (.json) format is widely used format for data exchange, but less easy to edit.

- [ ] Excel (*.xls*/*.xlsx*)
- [ ] Comma-Separated Values (*.csv*)
- [x] JSON (*.json*)

## Model

Internal representation of data:

- [x] **Block**
  - [x] name
  - [x] description
  - [x] with
  - [x] base_address
  - [x] registers
    - [ ] **Register**
    - [x] type
      - [x] Normal
      - [ ] Interrupt
      - [ ] Array (easy duplicated register)
      - [ ] Memory
    - [x] name
    - [x] description
    - [x] address_offset
    - [x] fields
      - [ ] **Field**
      - [x] name
      - [x] description
      - [x] access
        - Output
          - [x] **RW**: Read & Write. Simple write, read written value
        - Input
          - [x] **RO**: Read Only. Read from input, write has no effect
        - Bi-direction
          - [ ] **RW2**: Read & Write 2-way. Like combine RW and RO at same address
        - Special
          - [ ] **INT**: Specially for interrupt register
      - [ ] strobe
      - [ ] enumerated_values
      - [x] bit_width
      - [x] bit_offset
      - [x] reset

## Advanced Features

- [ ] DRC
  - Error
    - [ ] No char other than *A-Z*, *a-z*, *0-9* and *_* in name
    - [ ] No address overlapped registers
    - [ ] No bit overlapped fields
  - Warning
    - [ ] No lower alphabets (*a-z*) in name
    - [ ] No empty description
- [ ] Markdown support in description

## Random Thought

May not be realized

- CDC
- Use something like `[0-3]` in register name to easy duplicate register
- Field type SC (Self Clear)
- Field type SS (Self Set)
- Field type latch high
- Field type latch low
- Field type latch with read/write clear

## Output File

For the file generation, SystemVerilog (.sv) is chosen since I use it very much. However, it's very easy to add another template to add support of other functionality (different interface and different format).

- [ ] SystemVerilog (.sv), AXI4-Lite interface
  - No **WSTRB** support
  - No **AWPROT** and **ARPROT** support
  - [ ] Test bench (.sv)

- [ ] SystemVerilog header (.svh)

- [ ] C header (.h)

- [ ] JSON (.json), for cleanup and check
