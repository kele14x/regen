import logging
import math
from enum import Enum
from typing import List

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

    def __init__(self, id='', bit_width=1, direction='output'):
        self.id = id
        self.bit_width = bit_width
        self._direction = SignalDirection(direction)

    @property
    def direction(self):
        return self._direction.value

    def to_dict(self):
        return {
            'id': self.id,
            'bit_width': self.bit_width,
            'direction': self.direction
        }


def signals_of_access(access: FieldAccess, bit_width: int) -> List[Signal]:
    if access == FieldAccess.READ_WRITE:
        return [
            Signal(id='', bit_width=bit_width, direction='output')
        ]

    if access == FieldAccess.READ_ONLY:
        return [
            Signal(id='', bit_width=bit_width, direction='input')
        ]

    if access == FieldAccess.READ_WRITE_2WAY:
        return [
            Signal(id='out', bit_width=bit_width, direction='output'),
            Signal(id='in', bit_width=bit_width, direction='input')
        ]

    raise ValueError(f'Unsupported field access type {access.value}')


class Field(Element):
    """Register field in register."""

    __slots__ = ['description', '_access', 'bit_offset', 'bit_width',
                 'reset']

    def __init__(self, id='', access='RW', bit_offset=0, bit_width=1, reset=0):
        """Build a field object from a dict."""
        self.id: str = id
        self._access = FieldAccess(access)
        self.bit_offset = bit_offset
        self.bit_width = bit_width
        self.reset = reset
        signals = signals_of_access(self._access, self.bit_width)
        for s in signals:
            s.parent = self
        self.content = signals

    @property
    def bit_mask(self):
        return ((2 ** self.bit_width) - 1) * (2 ** self.bit_offset)

    @property
    def access(self) -> str:
        return self._access.value

    @property
    def signals(self):
        return self.content

    def to_dict(self):
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

    __slots__ = ['name', 'description', '_type', 'address_offset']

    def __init__(self, id='', name='', description='', type='NORMAL', address_offset=0, fields=None):
        """Build a register from dict."""
        self.id: str = id
        self.name = name
        self.description = description
        self._type = RegisterType(type)
        self.address_offset = address_offset
        if fields is None:
            fields = []
        for f in fields:
            f.parent = self
        self.content = sorted(fields, key=lambda x: x.bit_offset)

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

    def signals(self):
        return self.children(2)

    def to_dict(self):
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

    __slots__ = ['name', 'description', 'data_width', 'base_address']

    def __init__(self, id='', name='', description='', data_width=32, base_address=0, registers=None):
        """Build a register block from a dict."""
        self.id = id
        self.name = name
        self.description = description
        self.data_width = data_width
        self.base_address = base_address
        if registers is None:
            registers = []
        for r in registers:
            r.parent = self
        self.content = sorted(registers, key=lambda x: x.address_offset)

    @property
    def address_width(self) -> int:
        """Minimum required address data_width."""
        return math.ceil(math.log2(self.registers[-1].address_offset + 1)) + 2

    @property
    def registers(self):
        return self.content

    def fields(self):
        return self.children(2)

    def signals(self):
        return self.children(3)

    def to_dict(self):
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
    __slots__ = ['name', 'description']

    def __init__(self, id='', name='', description='', blocks=None):
        self.id = id
        self.name = name
        self.description = description
        if blocks is None:
            blocks = []
        for b in blocks:
            b.parent = self
        self.content = sorted(blocks, key=lambda x: x.base_address)

    @property
    def blocks(self):
        return self.content

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'blocks': self.blocks
        }
