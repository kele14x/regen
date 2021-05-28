Details
=======

Input File
----------

Excel (*.xls*/*.xlsx*) is a good candidate for the description file. Microsoft and Google provide good team coop tool for Excel documents, and it's very easy to edit (but cost $). If you don't like the binary format or want better version control, Comma-Separated Values (*.csv*) file is another good choice.

JSON (.json) format is widely used format for data exchange, but less easy to edit.

- [ ] Excel (*.xls*/*.xlsx*)
- [ ] Comma-Separated Values (*.csv*)
- [x] JSON (*.json*)

Output File
-----------

For the file generation, SystemVerilog (.sv) is chosen since I use it very much. However, it's very easy to add another template to add support of other functionality (different interface and different format).

- [ ] SystemVerilog (.sv), AXI4-Lite interface
  - No **WSTRB** support
  - No **AWPROT** and **ARPROT** support
  - [ ] Test bench (.sv)

- [ ] SystemVerilog header (.svh)

- [ ] C header (.h)

- [ ] JSON (.json), for cleanup and check

Model
-----

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

Advanced Features
-----------------

- [ ] DRC
  - Error
    - [ ] No char other than *A-Z*, *a-z*, *0-9* and *_* in name
    - [ ] No address overlapped registers
    - [ ] No bit overlapped fields
  - Warning
    - [ ] No lower alphabets (*a-z*) in name
    - [ ] No empty description
- [ ] Markdown support in description

Planned Features
----------------

- More field access type support
- Use something like `[0-3]` in register name to easy duplicate register
