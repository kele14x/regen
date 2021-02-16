import json
from enum import Enum


class FieldAccess(Enum):
    """Access type of a field, this controls the input/output direction and the hdl logic of a field"""
    READ_WRITE = 'RW'  # Output, read written value
    READ_ONLY = 'RO'  # Input, write has no effect
    WRITE_ONLY = 'WO'  # Output, read all zeros


class RegisterType(Enum):
    """Type of a register, currently only normal register is supported"""
    NORMAL = 'NORMAL'  # Normal register
    # INTERRUPT = 'INTERRUPT'  # Interrupt register


class Field:
    """Register field, atom element of hdl logic generation"""

    def __init__(self, d: dict):
        self.name = d['name']
        self.description = d['description']
        self.bit_width = d['bit_width']
        self.bit_offset = d['bit_offset']
        self.reset = d['reset']
        self.access = d['access']


class Register:
    """ One Register in register map, contains one or more field """

    def __init__(self, d: dict):
        self.type = d['type']
        self.name = d['name']
        self.description = d['description']
        self.address_offset = d['address_offset']
        self.fields = []
        for f in d['fields']:
            self.fields.append(Field(f))

    @property
    def reset(self) -> int:
        """ Get the reset value of the register """
        a = 0
        for f in self.fields:
            a |= (f.reset << f.bit_offset)
        return a

    def sort(self, reverse=False):
        """ Sort the fields in register based on field's `bit_offset` attribute """
        self.fields.sort(key=lambda f: f.bit_offset, reverse=reverse)


class RegisterMap:
    """ Register map, contains one or more register """

    def __init__(self, d: dict):
        self.name = d['name']
        self.description = d['description']
        self.width = d['width']
        self.base_address = d['base_address']
        self.registers = []
        for r in d['registers']:
            self.registers.append(Register(r))


class Storage:
    def __init__(self, d: dict):
        self.json_version = d['json_version']
        self.register_map = RegisterMap(d['register_map'])

    def to_json(self) -> str:
        """
        Serialize this object to a JSON formatted str.

        :return: JSON formatted str
        """
        s = json.dumps(self, default=lambda x: x.__dict__)
        return s
