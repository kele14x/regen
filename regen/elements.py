import logging
import math
from enum import Enum

from .base import Element

logger = logging.getLogger('main')


class SignalDirection(Enum):
    Output = 'output'
    Input = 'input'
    Internal = 'internal'


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


class Signal(Element):
    """Signal generated from a field."""

    __slots__ = ['bit_width', '_direction']

    def __init__(self, id='', bit_width=1, direction='output', parent=None):
        self.id = id
        self.bit_width = bit_width
        self._direction = SignalDirection(direction)
        self.parent = parent

    @property
    def direction(self):
        return self._direction.value

    def to_json(self):
        return {
            'id': self.id,
            'bit_width': self.bit_width,
            'direction': self.direction
        }


class Field(Element):
    """Register field in register."""

    __slots__ = ['id', 'description', '_access', 'bit_offset', 'bit_width',
                 'reset']

    def __init__(self, d: dict):
        """Build a field object from a dict."""
        self.id: str = d['id'].strip()
        self._access = FieldAccess(d.get('access', 'RW'))
        self.bit_offset = d.get('bit_offset', 0)
        self.bit_width = d.get('bit_width', 1)
        self.reset = d.get('reset', 0)

        if self._access == FieldAccess.READ_WRITE:
            s = [
                Signal(id='', bit_width=self.bit_width, direction='output',
                       parent=self)
            ]
        elif self._access == FieldAccess.READ_ONLY:
            s = [
                Signal(id='', bit_width=self.bit_width, direction='input',
                       parent=self)
            ]
        elif self._access == FieldAccess.READ_WRITE_2WAY:
            s = [
                Signal(id='out', bit_width=self.bit_width,
                       direction='output', parent=self),
                Signal(id='in', bit_width=self.bit_width, direction='input',
                       parent=self)
            ]
        else:
            raise ValueError(f'Unsupported field access type '
                             f'{self._access.value}')
        self.content = s

    @property
    def bit_mask(self):
        return ((2 ** self.bit_width) - 1) * (2 ** self.bit_offset)

    @property
    def access(self) -> str:
        return self._access.value

    @property
    def signals(self):
        return self.content

    def to_json(self):
        return {
            'id': self.id,
            'access': self.access,
            'bit_offset': self.bit_offset,
            'bit_width': self.bit_width,
            'reset': self.reset,
            'signals': self.signals
        }


class Register(Element):
    """Register in register block."""

    __slots__ = ['id', 'name', 'description', '_type', 'address_offset']

    def __init__(self, d: dict):
        """Build a register from dict."""
        self.id: str = d['id']
        self.name = d.get('name', '')
        self.description = d.get('description', '')
        self._type = RegisterType(d.get('type', 'NORMAL'))
        self.address_offset = d.get('address_offset', 0)
        fs = []
        for f in d['fields']:
            fo = Field(f)
            fo.parent = self
            fs.append(fo)
        self.content = sorted(fs, key=lambda x: x.bit_offset)

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

    @property
    def fields(self):
        return self.content

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'address_offset': self.address_offset,
            'fields': self.fields
        }


class Block(Element):
    """Register block."""

    __slots__ = ['id', 'name', 'description', 'data_width', 'base_address']

    def __init__(self, d: dict):
        """Build a register block from a dict."""
        self.id = d['id']
        self.name = d.get('name', '')
        self.description = d.get('description', '')
        self.data_width = d.get('data_width', 32)
        self.base_address = d.get('base_address', 0)
        rs = []
        for r in d['registers']:
            ro = Register(r)
            ro.parent = self
            rs.append(ro)
        self.content = sorted(rs, key=lambda x: x.address_offset)

    @property
    def address_width(self) -> int:
        """Minimum required address data_width."""
        return math.ceil(math.log2(self.registers[-1].address_offset + 1)) + 2

    @property
    def registers(self):
        return self.content

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'data_width': self.data_width,
            'base_address': self.base_address,
            'registers': self.registers
        }


class Circuit(Element):
    """Circuit design, may contain one or more blocks."""
    __slots__ = ['id', 'name', 'description']

    def __init__(self, d: dict):
        self.id = d['id']
        self.name = d.get('name', '')
        self.description = d.get('description', '')
        bs = []
        for b in d['blocks']:
            bo = Block(b)
            bo.parent = self
            bs.append(bo)
        self.content = sorted(bs, key=lambda x: x.base_address)

    @property
    def blocks(self):
        return self.content

    def to_json(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'blocks': self.blocks
        }
