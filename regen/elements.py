import logging
import math
from typing import Optional

from .base import Element

logger = logging.getLogger('main')

# Type of a register.
known_register_type = ['INTERRUPT', 'NORMAL', 'MEMORY']

# Access type of a field
known_field_access = ['INT', 'R', 'RW', 'RW0', 'RW2', 'RSVD']


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
    def address_offset(self):
        if self.parent is not None:
            return self.parent.address_offset

    @property
    def is_known_access(self):
        return self.access in known_field_access

    @property
    def has_port(self):
        return self.access in ['INT', 'RO', 'RW', 'RW2']

    @property
    def identifier(self):
        # looks like register_field
        return self.symbol(1)

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
        for f in self.fields():
            a |= (f.reset << f.bit_offset)
        return a

    @property
    def access(self) -> str:
        access = 'rsvd'
        for f in self.fields():
            if access == 'rsvd':
                access = f.access
            elif access != f.access:
                return 'mixed'
        return access

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
        return any((f.has_port for f in self.fields()))

    # Iteration

    def fields(self):
        if self.content is not None:
            yield from self.content

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

    @property
    def has_port(self):
        return any((r.has_port for r in self.content))

    # Iteration

    def registers(self):
        """Return a generator that iterates all registers."""
        # Instead of directly return ``self.content``, it should yield from ```register.expanded()``.
        if self.content is not None:
            yield from self.content

    def fields(self):
        """Return a generator that iterates all fields."""
        for r in self.registers():
            yield from r.fields()

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
