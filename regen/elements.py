import copy
import logging
import math
from enum import Enum
from typing import List

from .base import Element

logger = logging.getLogger('main')


class SignalDirection(Enum):
    OUTPUT = 'output'
    INPUT = 'input'
    INTERNAL = 'internal'


class FieldAccess(Enum):
    """Access type of a field, it controls the hdl logic genrated."""

    RW = 'RW'  # Output, read written value
    RO = 'RO'  # Input, write has no effect
    RW2 = 'RW2'  # Output and input two way
    INT = 'INT'  # Only for register with interrupt type


class RegisterType(Enum):
    """Type of a register."""

    NORMAL = 'NORMAL'  # Normal register
    INTERRUPT = 'INTERRUPT'  # Interrupt register
    MEMORY = 'MEMORY'  # A memory mapped region


class Signal(Element):
    """Signal generated from a field."""

    __slots__ = ['bit_width', '_direction']

    content: None
    parent: 'Field'

    bit_width: int
    _direction: SignalDirection

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
    if access == FieldAccess.RW:
        return [
            Signal(id='', bit_width=bit_width, direction='output'),
            Signal(id='oreg', bit_width=bit_width, direction='internal')
        ]

    if access == FieldAccess.RO:
        return [
            Signal(id='', bit_width=bit_width, direction='input'),
            Signal(id='ireg', bit_width=bit_width, direction='internal')
        ]

    if access == FieldAccess.RW2:
        return [
            Signal(id='out', bit_width=bit_width, direction='output'),
            Signal(id='oreg', bit_width=bit_width, direction='internal'),
            Signal(id='in', bit_width=bit_width, direction='input'),
            Signal(id='ireg', bit_width=bit_width, direction='internal')
        ]

    if access == FieldAccess.INT:
        return [
            Signal(id='', bit_width=bit_width, direction='input'),
            Signal(id='trap', bit_width=bit_width, direction='internal'),
            Signal(id='mask', bit_width=bit_width, direction='internal'),
            Signal(id='force', bit_width=bit_width, direction='internal'),
            Signal(id='trig', bit_width=bit_width, direction='internal'),
            Signal(id='int', bit_width=bit_width, direction='internal'),
            Signal(id='dbg', bit_width=bit_width, direction='internal'),
        ]

    raise ValueError(f'Unsupported field access type {access.value}')


class Field(Element):
    """Register field in register."""

    __slots__ = ['description', '_access', 'bit_offset', 'bit_width',
                 'reset']

    content: List[Signal]
    parent: 'Register'

    def __init__(self, id='', access='RW', bit_offset=0, bit_width=1, reset=0):
        """Build a field object from a dict."""
        self.id: str = id
        self._access = FieldAccess(access)
        self.bit_offset = bit_offset
        self.bit_width = bit_width
        self.reset = reset

    @property
    def bit_mask(self):
        return ((2 ** self.bit_width) - 1) * (2 ** self.bit_offset)

    @property
    def access(self) -> str:
        return self._access.value

    def signals(self):
        # TODO: refactor using generator
        raise NotImplementedError

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

    content: List[Field]
    parent: 'Block'

    name: str
    description: str
    _type: RegisterType
    address_offset: int

    def __init__(self, id='', name='', description='', type='NORMAL', address_offset=0, fields=None):
        """Build a register from dict."""
        self.id = id
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
        for f in self.content:
            a |= (f.reset << f.bit_offset)
        return a

    @property
    def address(self):
        return self.address_offset * self.parent.address_step

    @property
    def type(self):
        return self._type.value

    def expand(self):
        """
        Return a generator that expand this register descriptor to scalar register(s).

        Depend on the type of register, the expanded result maybe single or multi elements.
        """
        if self._type == RegisterType.NORMAL:
            yield self
        elif self._type == RegisterType.INTERRUPT:
            names = ['', 'TRIG', 'TRAP', 'MASK', 'FORCE', 'DBG']
            for i, name in enumerate(names):
                r = copy.copy(self)
                r.name = r.name + name
                r.address_offset = r.address_offset + i
                yield r
        elif self._type == RegisterType.MEMORY:
            yield self

    def fields(self):
        for r in self.expand():
            yield from r.content

    def signals(self):
        raise NotImplementedError

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

    content: List[Register]
    parent: 'Circuit'

    name: str
    description: str
    data_width: int
    base_address: int

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
        return math.ceil(math.log2(self.content[-1].address_offset + 1)) + 2

    @property
    def address_step(self) -> int:
        """Address step size."""
        return math.floor(self.data_width / 8)

    def registers(self):
        for r in self.content:
            yield from r.expand()

    def fields(self):
        for r in self.content:
            yield from r.fields()

    def ports(self):
        raise NotImplementedError

    def signals(self):
        raise NotImplementedError

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
