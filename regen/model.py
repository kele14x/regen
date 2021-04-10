import json
import logging
import math
import string
from enum import Enum
from typing import Any, List, Optional

logger = logging.getLogger('main')

name_set = string.ascii_letters + string.digits + '_'


def normalize_name(name: str) -> str:
    """
    Normalize block, register or field's name.

    :param name: Name in string
    :return: Normalized name
    """
    name = [c if c in name_set else '' for c in name]
    return ''.join(name)


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


class Field:
    """Register field in register."""

    _name: str
    _description: str
    _access: FieldAccess
    _bit_offset: int
    _bit_width: int
    _reset: int

    def __init__(self, d: dict):
        """Build a field object from a dict."""
        name: str = d['name']
        name_norm = normalize_name(name)
        if not name == name_norm:
            logger.critical('Field name "%s" contains invalid char and is '
                            'renamed to "%s"', name, name_norm)
        self._name = name_norm
        self._description = d['description']
        self._access = FieldAccess(d['access'])
        self._bit_offset = d['bit_offset']
        self._bit_width = d['bit_width']
        self._reset = d['reset']

    @property
    def name(self):
        return self._name.strip().upper()

    @property
    def description(self):
        return self._description

    @property
    def access(self):
        return self._access.value

    @property
    def bit_offset(self):
        return self._bit_offset

    @property
    def bit_width(self):
        return self._bit_width

    @property
    def bit_mask(self):
        return ((2 ** self._bit_width) - 1) * (2 ** self._bit_offset)

    @property
    def reset(self):
        return self._reset


class Register:
    """Register in register block."""

    _name: str
    _description: str
    _type: RegisterType
    _address_offset: int
    _fields: List[Field]

    def __init__(self, d: dict):
        """Build a register from dict."""
        name = d['name']
        name_norm = normalize_name(name)
        if not name == name_norm:
            logger.critical('Register name "%s" contains invalid char and is '
                            'renamed to "%s"', name, name_norm)
        self._name = name_norm
        self._description = d['description']
        self._type = RegisterType(d['type'])
        self._address_offset = d['address_offset']
        fs = []
        for f in d['fields']:
            fs.append(Field(f))
        self._fields = sorted(fs, key=lambda x: x.bit_offset)

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def type(self):
        return self._type

    @property
    def address_offset(self):
        return self._address_offset

    @property
    def reset(self) -> int:
        """Get the reset value of the register."""
        a = 0
        for f in self._fields:
            a |= (f.reset << f.bit_offset)
        return a

    @property
    def fields(self):
        return self._fields


class Block:
    """Register block."""

    _name: str
    _description: str
    _width: int
    _base_address: int
    _registers: List[Register]

    def __init__(self, d: dict):
        """Build a register block from a dict."""
        name = d['name']
        name_norm = normalize_name(name)
        if not name == name_norm:
            logger.critical('Block name "%s" contains invalid char and is '
                            'named to "%s"', name, name_norm)
        self._name = name_norm
        self._description = d['description']
        self._width = d['width']
        self._base_address = d['base_address']
        regs = []
        for r in d['registers']:
            regs.append(Register(r))
        self._registers = sorted(regs, key=lambda x: x.address_offset)

    @property
    def name(self):
        return self._name

    @property
    def description(self):
        return self._description

    @property
    def width(self):
        """Bit width of data."""
        return self._width

    @property
    def base_address(self):
        return self._base_address

    @property
    def address_width(self) -> int:
        """Minimum required address width."""
        return math.ceil(math.log2(self._registers[-1].address_offset + 1)) + 2

    @property
    def registers(self):
        return self._registers

    def to_json(self) -> str:
        """Serialize this object to a JSON string."""
        s = json.dumps(self, cls=BlockEncoder, indent=2)
        return s


class BlockEncoder(json.JSONEncoder):
    """Custom JSON Encoder for Block object."""

    def default(self, o: Any) -> Any:
        """Overloaded method to return an dict for json encoding."""
        if isinstance(o, FieldAccess):
            return o.value

        if isinstance(o, RegisterType):
            return o.value

        if isinstance(o, Field):
            return {
                'name': o.name,
                'description': o.description,
                'access': o.access,
                'bit_offset': o.bit_offset,
                'bit_width': o.bit_width,
                'reset': o.reset
            }

        if isinstance(o, Register):
            return {
                'name': o.name,
                'description': o.description,
                'type': o.type,
                'address_offset': o.address_offset,
                'fields': o.fields
            }

        if isinstance(o, Block):
            return {
                'name': o.name,
                'description': o.description,
                'width': o.width,
                'base_address': o.base_address,
                'registers': o.registers
            }

        return super(BlockEncoder, self).default(o)
