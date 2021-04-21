import json
import logging
import math
from enum import Enum
from typing import Any, List

logger = logging.getLogger('main')


class FieldAccess(Enum):
    """
    Access type of a field.

    This controls the input/output direction and the hdl logic of a field.
    """

    READ_WRITE = 'RW'  # Output, read written value
    READ_ONLY = 'RO'  # Input, write has no effect
    READ_WRITE_2WAY = 'RW2'  # Output and input two way
    # TODO: Add more field access type here


class RegisterType(Enum):
    """
    Type of a register.

    Currently only normal register is supported.
    """

    NORMAL = 'NORMAL'  # Normal register
    # INTERRUPT = 'INTERRUPT'  # Interrupt register
    # TODO: Add more register type here


class Element:
    """
    Basic element of other class (Field, Register, Block).
    """

    id: str
    name: str
    description: str

    def __init__(self, d: dict):
        self.id = d['id'].strip()  # id is required, raise error is not presents
        self.name = d.get('name', '')
        self.description = d.get('description', '')

    def to_json(self) -> str:
        """Serialize this object to a JSON string."""
        s = json.dumps(self, cls=JSONEncoder, indent=2)
        return s


class Signal(Element):
    """
    Signal generated from a field.
    """

    def __init__(self, d: dict):
        super(Signal, self).__init__(d)


class Field(Element):
    """Register field in register."""

    _access: FieldAccess
    bit_offset: int
    bit_width: int
    reset: int

    def __init__(self, d: dict):
        """Build a field object from a dict."""
        super(Field, self).__init__(d)
        self._access = FieldAccess(d['access'])
        self.bit_offset = d['bit_offset']
        self.bit_width = d['bit_width']
        self.reset = d['reset']

    @property
    def bit_mask(self):
        return ((2 ** self.bit_width) - 1) * (2 ** self.bit_offset)

    @property
    def access(self):
        return self._access.value


class Register(Element):
    """Register in register block."""

    _type: RegisterType
    address_offset: int
    fields: List[Field]

    def __init__(self, d: dict):
        """Build a register from dict."""
        super(Register, self).__init__(d)
        self._type = RegisterType(d['type'])
        self.address_offset = d['address_offset']
        fs = []
        for f in d['fields']:
            fs.append(Field(f))
        self.fields = sorted(fs, key=lambda x: x.bit_offset)

    @property
    def reset(self) -> int:
        """Get the reset value of the register."""
        a = 0
        for f in self.fields:
            a |= (f.reset << f.bit_offset)
        return a

    @property
    def type(self):
        return self._type.value

class Block(Element):
    """Register block."""

    data_width: int
    base_address: int
    registers: List[Register]

    def __init__(self, d: dict):
        """Build a register block from a dict."""
        super(Block, self).__init__(d)
        self.data_width = d['data_width']
        self.base_address = d['base_address']
        regs = []
        for r in d['registers']:
            regs.append(Register(r))
        self.registers = sorted(regs, key=lambda x: x.address_offset)

    @property
    def address_width(self) -> int:
        """Minimum required address data_width."""
        return math.ceil(math.log2(self.registers[-1].address_offset + 1)) + 2


class JSONEncoder(json.JSONEncoder):
    """Custom JSON Encoder for Block object."""

    def default(self, o: Any) -> Any:
        """Overloaded method to return an dict for json encoding."""
        if isinstance(o, FieldAccess):
            return o.value

        if isinstance(o, RegisterType):
            return o.value

        if isinstance(o, Signal):
            return {
                'id': o.id,
                'name': o.name,
                'description': o.description
            }

        if isinstance(o, Field):
            return {
                'id': o.id,
                'name': o.name,
                'description': o.description,
                'access': o.access,
                'bit_offset': o.bit_offset,
                'bit_width': o.bit_width,
                'reset': o.reset
            }

        if isinstance(o, Register):
            return {
                'id': o.id,
                'name': o.name,
                'description': o.description,
                'type': o.type,
                'address_offset': o.address_offset,
                'fields': o.fields
            }

        if isinstance(o, Block):
            return {
                'id': o.id,
                'name': o.name,
                'description': o.description,
                'data_width': o.data_width,
                'base_address': o.base_address,
                'registers': o.registers
            }

        if isinstance(o, Element):
            return {
                'id': o.id,
                'name': o.name,
                'description': o.description
            }

        return super(JSONEncoder, self).default(o)
