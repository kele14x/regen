import logging
import math
from typing import Optional, Union

from .base import Element

logger = logging.getLogger('main')

# Type of a register.
known_register_type = ['DUMMY', 'INTERRUPT', 'NORMAL', 'MEMORY']

# Signal direction
known_port_direction = ['input', 'output']

# Access type of a field
known_field_access = ['INT', 'RO', 'RW', 'RW0', 'RW2']


class Signal(Element):
    """Signal generated from a field."""

    __slots__ = ['bit_width']

    content: None
    parent: Optional['Field']

    bit_width: int

    def __init__(self, eid='', bit_width=1, parent=None):
        super(Signal, self).__init__(eid=eid, parent=parent)

        self.bit_width = bit_width

    @property
    def identifier(self):
        # looks like register_filed_signal
        return self.symbol(2)

    # Serialization

    def to_dict(self):
        return {
            'id': self.eid,
            'bit_width': self.bit_width,
        }


class Port(Signal):
    """Port of register block."""

    __slots__ = ['direction']

    content: None
    parent: Union['Field', 'Register', None]

    direction: str

    def __init__(self, eid='', bit_width=1, direction='output', parent=None):
        super(Port, self).__init__(eid=eid, bit_width=bit_width, parent=parent)
        self.direction = direction

    @property
    def is_known_direction(self):
        return self.direction in known_port_direction

    @property
    def identifier(self):
        # For port belongs to register, it will be like register_port
        if isinstance(self.parent, Register):
            return self.symbol(1)
        # For port belongs to field, it will be like register_field_port
        return self.symbol(2)

    # Serialization

    def to_dict(self):
        return {
            'id': self.eid,
            'bit_width': self.bit_width,
            'direction': self.direction
        }


class Field(Element):
    """
    Field abstraction class

    A field represents a set of bits that behave consistently as a single entity.

    A field is contained within a single register.
    """

    __slots__ = ['description', 'access', 'bit_offset', 'bit_width',
                 'reset']

    content: None
    parent: Optional['Register']

    description: str
    access: str
    bit_offset: int
    bit_width: int
    reset: int
    "THis is doc for reset"

    def __init__(self, eid='', description='', access='RW', bit_offset=0, bit_width=1, reset=0, parent=None):
        """Build a field object from parameters."""
        super(Field, self).__init__(eid=eid, parent=parent)

        self.description = description
        self.access = access
        self.bit_offset = bit_offset
        self.bit_width = bit_width
        self.reset = reset

    @property
    def bit_mask(self):
        return ((2 ** self.bit_width) - 1) * (2 ** self.bit_offset)

    @property
    def is_known_access(self):
        return self.access in known_field_access

    @property
    def identifier(self):
        # looks like register_field
        return self.symbol(1)

    # Iteration

    def signals(self):
        yield Signal(eid='int', bit_width=self.bit_width, parent=self)
        if self.access == 'RW2':
            yield Signal(eid='int2', bit_width=self.bit_width, parent=self)

    def ports(self):
        if self.access == 'INT':
            if self.parent is not None and self.parent.rtype == 'INTERRUPT':
                yield Port(eid='', bit_width=self.bit_width, direction='input', parent=self)
        elif self.access == 'RO':
            yield Port(eid='', bit_width=self.bit_width, direction='input', parent=self)
        elif self.access == 'RW':
            yield Port(eid='', bit_width=self.bit_width, direction='output', parent=self)
        elif self.access == 'RW2':
            yield Port(eid='in', bit_width=self.bit_width, direction='input', parent=self)
            yield Port(eid='out', bit_width=self.bit_width, direction='output', parent=self)

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

    __slots__ = ['name', 'description', 'rtype', 'address_offset', 'address_size']

    content: Optional[list[Field]]
    parent: Optional['Block']

    name: str
    description: str
    rtype: str
    address_offset: int
    address_size: int

    def __init__(self, eid='', name='', description='', rtype='NORMAL', address_offset=0, address_size=1, parent=None,
                 fields=None):
        """Build a register from parameters."""
        super(Register, self).__init__(eid=eid, parent=parent)

        self.name = name
        self.description = description
        self.rtype = rtype
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
        return self.rtype

    @property
    def is_known_type(self):
        return self.rtype in known_register_type

    @property
    def identifier(self):
        return self.eid

    @property
    def has_irq(self):
        if self.rtype == 'INTERRUPT' and self.content is not None and self.content:
            return True
        return False

    @property
    def has_port(self):
        if self.rtype != 'DUMMY' and self.content is not None and self.content:
            return True
        return False

    # Iteration

    def expanded(self):
        if self.rtype == 'INTERRUPT':
            names = ['', '_TRIG', '_TRAP', '_DBG', '_MASK', '_FORCE']
            copied = [self.copy() for _ in names]
            for i, e in enumerate(copied):
                e.eid = e.eid + names[i]
                e.address_offset = e.address_offset + i
                if i > 0:
                    e.rtype = 'DUMMY'
            yield from copied
        else:
            yield self

    def irq_ports(self):
        if self.rtype == 'INTERRUPT':
            yield Port(eid='irq', direction='output', parent=self)

    def fields(self):
        if self.content is not None:
            yield from self.content

    def signals(self):
        if self.content is not None:
            for f in self.content:
                yield from f.signals()

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
        super(Block, self).__init__(eid=eid, parent=parent)

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
        return any((r.has_irq for r in self.content))

    # Iteration

    def registers(self):
        """Return a generator that iterates all registers."""
        # Instead of directly return ``self.content``, it should yield from ```register.expanded()``.
        if self.content is not None:
            for c in self.content:
                yield from c.expanded()

    def fields(self):
        """Return a generator that iterates all fields."""
        for r in self.registers():
            yield from r.fields()

    def signals(self):
        for r in self.registers():
            yield from r.signals()

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
        super(Circuit, self).__init__(eid=eid, parent=parent)

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
