import copy
import logging
import math
from enum import Enum
from typing import Optional

from .base import Element

logger = logging.getLogger('main')


class SignalDirection(Enum):
    INPUT = 'input'
    INTERNAL = 'internal'
    OUTPUT = 'output'


class FieldAccess(Enum):
    """Access type of a field, it controls the hdl logic genrated."""

    INT = 'INT'  # Only for register with interrupt type
    RO = 'RO'  # Input, write has no effect
    RW = 'RW'  # Output, read written value
    RW2 = 'RW2'  # Output and input two way


class RegisterType(Enum):
    """Type of a register."""

    NORMAL = 'NORMAL'  # Normal register
    INTERRUPT = 'INTERRUPT'  # Interrupt register
    MEMORY = 'MEMORY'  # A memory mapped region


class Signal(Element):
    """Signal generated from a field."""

    __slots__ = ['bit_width', '_direction']

    content: None
    parent: Optional['Field']

    bit_width: int
    _direction: SignalDirection

    def __init__(self, eid='', bit_width=1, direction='output', parent=None):
        self.eid = eid
        self.bit_width = bit_width
        self._direction = SignalDirection(direction)
        self.parent = parent

    @property
    def direction(self):
        return self._direction.value

    def to_dict(self):
        return {
            'id': self.eid,
            'bit_width': self.bit_width,
            'direction': self.direction
        }


def signals_of_access(access: FieldAccess, bit_width: int) -> list[Signal]:
    if access == FieldAccess.RW:
        return [
            Signal(eid='', bit_width=bit_width, direction='output'),
            Signal(eid='oreg', bit_width=bit_width, direction='internal')
        ]

    if access == FieldAccess.RO:
        return [
            Signal(eid='', bit_width=bit_width, direction='input'),
            Signal(eid='ireg', bit_width=bit_width, direction='internal')
        ]

    if access == FieldAccess.RW2:
        return [
            Signal(eid='out', bit_width=bit_width, direction='output'),
            Signal(eid='oreg', bit_width=bit_width, direction='internal'),
            Signal(eid='in', bit_width=bit_width, direction='input'),
            Signal(eid='ireg', bit_width=bit_width, direction='internal')
        ]

    if access == FieldAccess.INT:
        return [
            Signal(eid='', bit_width=bit_width, direction='input'),
            Signal(eid='trap', bit_width=bit_width, direction='internal'),
            Signal(eid='mask', bit_width=bit_width, direction='internal'),
            Signal(eid='force', bit_width=bit_width, direction='internal'),
            Signal(eid='trig', bit_width=bit_width, direction='internal'),
            Signal(eid='int', bit_width=bit_width, direction='internal'),
            Signal(eid='dbg', bit_width=bit_width, direction='internal'),
        ]

    raise ValueError(f'Unsupported field access type {access.value}')


class Field(Element):
    """Register field in register."""

    __slots__ = ['description', '_access', 'bit_offset', 'bit_width',
                 'reset']

    content: list[Signal]
    parent: Optional['Register']

    def __init__(self, eid='', description='', access='RW', bit_offset=0, bit_width=1, reset=0):
        """Build a field object from a dict."""
        self.eid: str = eid
        self.description = description
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

    def to_dict(self):
        return {
            'id': self.eid,
            'description': self.description,
            'access': self.access,
            'bit_offset': self.bit_offset,
            'bit_width': self.bit_width,
            'reset': self.reset
        }


class Register(Element):
    """Register in register block."""

    __slots__ = ['name', 'description', '_type', 'address_offset']

    content: list[Field]
    parent: Optional['Block']

    name: str
    description: str
    _type: RegisterType
    address_offset: int

    def __init__(self, eid='', name='', description='', type='NORMAL', address_offset=0, fields=None):
        """Build a register from dict."""
        self.eid = eid
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
    def type(self):
        return self._type.value

    @property
    def fields(self):
        return self.content

    def ports(self):
        """Return a generator that iterates all ports caused by fields"""
        for f in self.fields:
            if f.access == FieldAccess.INT.value:
                yield Signal(eid='', direction='input', parent=f)
            elif f.access == FieldAccess.RO.value:
                yield Signal(eid='', direction='input', parent=f)
            elif f.access == FieldAccess.RW.value:
                yield Signal(eid='', direction='output', parent=f)
            elif f.access == FieldAccess.RW2.value:
                yield Signal(eid='in', direction='input', parent=f)
                yield Signal(eid='out', direction='output', parent=f)
            else:
                raise ValueError

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

    def to_dict(self):
        return {
            'id': self.eid,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'address_offset': self.address_offset,
            'fields': self.fields
        }


class Block(Element):
    """Register block, or so called register module."""

    __slots__ = ['name', 'description', 'data_width', 'base_address']

    content: list[Register]
    parent: Optional['Circuit']

    name: str
    description: str
    data_width: int
    base_address: int

    def __init__(self, eid='', name='', description='', data_width=32, base_address=0, registers=None):
        """Build a register block."""
        self.eid = eid
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
    def address_gap(self) -> int:
        """Address gap size, i.e. minimum address difference between two registers"""
        return math.floor(self.data_width / 8)

    @property
    def registers(self):
        """Block.registers is mirror of Block.content"""
        return self.content

    def irq_ports(self):
        """Return a generator that iterates all ports of module."""
        # Ports caused by registers
        for r in self.registers:
            if r.type == RegisterType.INTERRUPT.value:
                s = Signal(eid='irq')
                s.parent = r
                yield s

    def ports(self):
        # Ports caused by fields are returned by register.ports
        for r in self.registers:
            yield from r.ports()

    def to_dict(self):
        return {
            'id': self.eid,
            'name': self.name,
            'description': self.description,
            'data_width': self.data_width,
            'base_address': self.base_address,
            'registers': self.registers
        }


class Circuit(Element):
    """Circuit design, may contain one or more blocks."""
    __slots__ = ['name', 'description']

    content: list[Block]
    parent: None

    name: str
    description: str

    def __init__(self, eid='', name='', description='', blocks=None):
        self.eid = eid
        self.name = name
        self.description = description
        if blocks is None:
            blocks = []
        for b in blocks:
            b.parent = self
        self.content = sorted(blocks, key=lambda x: x.base_address)

    @property
    def blocks(self):
        """Circuit.blocks is mirror of Circuit.content"""
        return self.content

    def to_dict(self):
        return {
            'id': self.eid,
            'name': self.name,
            'description': self.description,
            'blocks': self.blocks
        }
