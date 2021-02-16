# HDL REGEN

HDL REGEN (HDL Register Generator) is a tool for automatically generating register slave HDL with AXI or other interface. It can easily generate a SystemVerilog module from a description file, omitting the effort of writing the redundancy and error prone HDL codes by hand.

This project is inspired by same kind of tool from my company. It generates a OPB/AXI HDL slave module from an Excel file. The Excel holds detail description of registers/fields for each module. It also could generate C header file for software use, as well as a Word file as document for the software-hardware interface. Many designs, including FPGA and ASIC projects, benefit from this tool. However, it's a proprietary tool, I can't use for my hobby projects. Also, the tool is over-designed somewhere, and bad designed or leak of some feature at some point. So I decide to design my own (山寨) one.

The idea is that the tool can read an easy-to-edit description file, and parse it into an SystemVerilog template. It's not complex, but as and FPGA developer, it's still a little out of my knowledge scope. I'll slowly work on it to make it functions basically, but beware that this project currently is still work in progress and does not work at all.

## Input File

Excel (.xlsx) is a good candidate for the description file. Microsoft and Google provide good team coop tool for Excel documents, and it's very easy to edit ($). Python has a good library to handle this format. JSON (.json) is another widely used format for data exchange, but less easy to edit. They are both planned to be supported.

- [ ] Excel (.xlsx)
- [x] JSON (.json)

## Model

- [ ] **Storage**
- [x] json_version
- [x] reversion
- [x] register_map
    - [ ] **RegisterMap**
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
                    - [x] **RW**: Read & Write. Simple write, read writen value
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
    - Critical
        - [ ] No lower alphabets (*a-z*) in name
    - Warning
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

- [x] SystemVerilog (.sv), Xilinx BRAM interface
    - No write byte enable support
    - Single port
    - [ ] Test bench (.sv)

- [ ] SystemVerilog header (.svh)

- [ ] C header (.h)

- [ ] JSON (.json), for cleanup and check
