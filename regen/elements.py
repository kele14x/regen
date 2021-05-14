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

    DUMMY = 'DUMMY'  # Only appears but without function
    INTERRUPT = 'INTERRUPT'  # Interrupt register
    MEMORY = 'MEMORY'  # A memory mapped region
    NORMAL = 'NORMAL'  # Normal register


class Signal(Element):
    """Signal generated from a field."""

    __slots__ = ['bit_width', '_direction']

    content: None
    parent: Optional['Field']

    bit_width: int
    _direction: SignalDirection

    def __init__(self, eid='', bit_width=1, direction='output', parent=None):
        self.eid = eid
        self.parent = parent

        self.bit_width = bit_width
        self._direction = SignalDirection(direction)

    @property
    def direction(self):
        return self._direction.value

    @property
    def identifier(self):
        # looks like register_filed_signal
        return self.symbol(2)

    # Serialization

    def to_dict(self):
        return {
            'id': self.eid,
            'bit_width': self.bit_width,
            'direction': self.direction
        }


class Field(Element):
    """Register field in register."""

    __slots__ = ['description', '_access', 'bit_offset', 'bit_width',
                 'reset']

    content: None
    parent: Optional['Register']

    def __init__(self, eid='', description='', access='RW', bit_offset=0, bit_width=1, reset=0, parent=None):
        """Build a field object from parameters."""
        self.eid: str = eid
        self.parent = parent

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

    @property
    def identifier(self):
        # looks like register_field
        return self.symbol(1)

    # Iteration

    def signals(self):
        if self._access == FieldAccess.INT:
            yield Signal(eid='', bit_width=self.bit_width, direction='internal', parent=self)

    def ports(self):
        if self._access == FieldAccess.INT:
            yield Signal(eid='', bit_width=self.bit_width, direction='input', parent=self)
        elif self._access == FieldAccess.RO:
            yield Signal(eid='', bit_width=self.bit_width, direction='input', parent=self)
        elif self._access == FieldAccess.RW:
            yield Signal(eid='', bit_width=self.bit_width, direction='output', parent=self)
        elif self._access == FieldAccess.RW2:
            yield Signal(eid='', bit_width=self.bit_width, direction='input', parent=self)
            yield Signal(eid='out', bit_width=self.bit_width, direction='output', parent=self)

    # Serialization

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

    __slots__ = ['name', 'description', '_rtype', 'address_offset', 'address_size']

    content: Optional[list[Field]]
    parent: Optional['Block']

    name: str
    description: str
    _rtype: RegisterType
    address_offset: int
    address_size: int

    def __init__(self, eid='', name='', description='', rtype='NORMAL', address_offset=0, address_size=1, parent=None,
                 fields=None):
        """Build a register from parameters."""
        self.eid = eid
        self.parent = parent

        self.name = name
        self.description = description
        self._rtype = RegisterType(rtype)
        self.address_offset = address_offset
        self.address_size = address_size

        if fields is not None:
            for f in fields:
                f.parent = self
            self.content = sorted(fields, key=lambda x: x.bit_offset)

    @property
    def reset(self) -> int:
        """Get the reset value of the register."""
        a = 0
        if self.content is not None:
            for f in self.content:
                a |= (f.reset << f.bit_offset)
        return a

    @property
    def type(self):
        return self._rtype.value

    @property
    def identifier(self):
        return self.eid

    # Iteration

    def expanded(self):
        if self._rtype == RegisterType.INTERRUPT:
            names = ['', '_TRIG', '_TRAP', '_DBG', '_MASK', '_FORCE']
            copied = [self.copy() for _ in names]
            for i, e in enumerate(copied):
                e.eid = e.eid + names[i]
                e.address_offset = e.address_offset + i
                if i > 0:
                    e._rtype = RegisterType.DUMMY
            yield from copied
        else:
            yield self

    def irq_ports(self):
        if self._rtype == RegisterType.INTERRUPT:
            yield Signal(eid='irq', direction='input', parent=self)

    def fields(self):
        if self.content is not None:
            yield from self.content

    def ports(self):
        if self.content is not None:
            for f in self.content:
                yield from f.ports()

    # Serialization

    def to_dict(self):
        return {
            'id': self.eid,
            'name': self.name,
            'description': self.description,
            'type': self.type,
            'address_offset': self.address_offset,
            'fields': self.content
        }


class Block(Element):
    """Register block, or so called register module."""

    __slots__ = ['name', 'description', 'data_width', 'base_address']

    content: Optional[list[Register]]
    parent: Optional['Circuit']

    name: str
    description: str
    data_width: int
    base_address: int

    def __init__(self, eid='', name='', description='', data_width=32, base_address=0, parent=None, registers=None):
        """Build a block (register slave module) from parameters."""
        self.eid = eid
        self.parent = parent

        self.name = name
        self.description = description
        self.data_width = data_width
        self.base_address = base_address

        if registers is not None:
            for r in registers:
                r.parent = self
            self.content = sorted(registers, key=lambda x: x.address_offset)

    @property
    def address_width(self) -> int:
        """Minimum required address data_width."""
        if self.content is not None:
            return math.ceil(math.log2(self.content[-1].address_offset + 1)) + 2
        else:
            return 0

    @property
    def address_gap(self) -> int:
        """Address gap size, i.e. minimum address difference between two registers"""
        return math.floor(self.data_width / 8)

    @property
    def identifier(self):
        return self.eid

    @property
    def has_irq(self):
        return any((r.type == RegisterType.INTERRUPT.value for r in self.content))

    # Iteration

    def registers(self):
        """Return a generator that iterates all registers."""
        # Instead of directly return ``self.content``, it should yield from ```register.expanded()``.
        if self.content is not None:
            for c in self.content:
                yield from c.expanded()

    def irq_ports(self):
        for r in self.registers():
            yield from r.irq_ports()

    def ports(self):
        for r in self.registers():
            yield from r.ports()

    # Serialization

    def to_dict(self):
        return {
            'id': self.eid,
            'name': self.name,
            'description': self.description,
            'data_width': self.data_width,
            'base_address': self.base_address,
            'registers': self.content
        }


class Circuit(Element):
    """Circuit design, may contain one or more blocks."""
    __slots__ = ['name', 'description']

    content: Optional[list[Block]]
    parent: None

    name: str
    description: str

    def __init__(self, eid='', name='', description='', parent=None, blocks=None):
        self.eid = eid
        self.parent = parent

        self.name = name
        self.description = description

        if blocks is not None:
            for b in blocks:
                b.parent = self
            self.content = sorted(blocks, key=lambda x: x.base_address)

    @property
    def identifier(self):
        return self.eid

    # Iteration

    def blocks(self):
        if self.content is not None:
            yield from self.content

    # Serialization

    def to_dict(self):
        return {
            'id': self.eid,
            'name': self.name,
            'description': self.description,
            'blocks': self.content
        }
