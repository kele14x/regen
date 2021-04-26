import json
import logging
import math
from enum import Enum
from typing import Any

logger = logging.getLogger('main')


class SignalDirection(Enum):
    Output = 'output'
    Input = 'input'


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
        element = super(Element, cls).__new__(cls)
        element.parent = None
        element.content = None
        return element

    def to_json(self):
        """Serialize this object to a JSON string."""
        return {
            'content': self.content
        }

    def dumps(self):
        return json.dumps(self, cls=JSONEncoder, indent=2)

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
        if self.content is not None:
            for c in self.content:
                yield from c.walk()
        yield self


class Signal(Element):
    """Signal generated from a field."""

    __slots__ = ['suffix', 'bit_width', '_direction']

    def __init__(self, suffix='', bit_width=1, direction='output'):
        self.suffix = suffix
        self.bit_width = bit_width
        self._direction = SignalDirection(direction)

    @property
    def direction(self):
        return self._direction.value

    def to_json(self):
        return {
            'suffix': self.suffix,
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
                Signal(suffix='', bit_width=self.bit_width, direction='output')
            ]
        elif self._access == FieldAccess.READ_ONLY:
            s = [
                Signal(suffix='', bit_width=self.bit_width, direction='input')
            ]
        elif self._access == FieldAccess.READ_WRITE_2WAY:
            s = [
                Signal(suffix='out', bit_width=self.bit_width,
                       direction='output'),
                Signal(suffix='in', bit_width=self.bit_width, direction='input')
            ]
        else:
            s = None
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


class JSONEncoder(json.JSONEncoder):
    """Custom JSON Encoder for Block object."""

    def default(self, o: Any) -> Any:
        """Overloaded method to return an dict for json encoding."""
        if isinstance(o, Enum):
            return o.value

        if isinstance(o, Element):
            return o.to_json()

        return super(JSONEncoder, self).default(o)
