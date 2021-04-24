import json
import logging
import math
from enum import Enum
from typing import Any, List, Union

logger = logging.getLogger('main')


class SignalDirection(Enum):
    Output = 0
    Input = 1


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


class Element(object):
    """
    Basic element of other regen elements.
    """
    __slots__ = ['parent', 'content']

    def __new__(cls, *args, **kwargs):
        element = super(Element, cls).__new__(cls, *args, **kwargs)
        element.parent = None
        element.content = []

    def to_json(self):
        """Serialize this object to a JSON string."""
        return {
            'content': self.content
        }

    # Navigation

    @property
    def container(self):
        """
        Get the container (a ``list``) that contains this element,
        or None if no such container exists.
        """
        if self.parent is not None:
            return self.parent.content

    @property
    def index(self):
        """Get the index of this element in parent's content."""
        container = self.container
        if container is not None:
            return container.index(self)

    def sibling(self, n):
        """Return n-th sibling in parent's content"""
        idx = self.index
        if idx is not None:
            idx = idx + n
            container = self.container
            if 0 <= idx < len(container):
                return container[idx]

    @property
    def next(self):
        return self.sibling(1)

    @property
    def prev(self):
        return self.sibling(-1)

    # Iteration

    def walk(self):
        for c in self.content:
            yield c
        yield self


class Signal(Element):
    """Signal generated from a field."""

    __slots__ = ['id', 'bit_width', 'direction']

    def __init__(self, d: dict):
        self.id = d['id'].strip()
        self.bit_width = d.get('bit_width', 1)
        self.bit_width = SignalDirection(d.get('direction', 0))


class Field(Element):
    """Register field in register."""

    __slots__ = ['id', '_access', 'bit_offset', 'bit_width', 'reset']

    def __init__(self, d: dict):
        """Build a field object from a dict."""
        self.id: str = d['id'].strip()
        self._access = FieldAccess(d.get('access', 'RW'))
        self.bit_offset = d.get('bit_offset', 0)
        self.bit_width = d.get('bit_width', 1)
        self.reset = d.get('reset', 0)

    @property
    def bit_mask(self):
        return ((2 ** self.bit_width) - 1) * (2 ** self.bit_offset)

    @property
    def access(self) -> str:
        return self._access.value

    @property
    def signals(self):
        return self.content


class Register(Element):
    """Register in register block."""

    __slots__ = ['id', 'name', 'description', '_type', 'address_offset']

    _type: RegisterType
    address_offset: int
    fields: List[Field]

    def __init__(self, d: dict):
        """Build a register from dict."""
        self.id: str = d[id]
        self.name = d.get('name', '')
        self.description = d.get('description', '')
        self._type = RegisterType(d.get('type', 'NORMAL'))
        self.address_offset = d.get('address_offset', 0)
        fs = []
        for f in d['fields']:
            fs.append(Field(f))
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
