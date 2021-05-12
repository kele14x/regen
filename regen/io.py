"""
io is module for input and output function.
"""
import json
import logging
import sys
from typing import Optional, Union

from jinja2 import Environment, PackageLoader

from .base import Element
from .elements import Circuit, Block, Register, Field, RegisterType, FieldAccess

__all__ = ['read_json', 'read_csv', 'read_xlsx', 'dump_json', 'render_template']

logger = logging.getLogger('main')


# JSON Input
# ----------


def json_deserialize(d: dict):
    """
    Convert a dict (parse from JSON) to a regen element.

    This function is used when reading JSON file. Python std ``json`` library has capability to decode any valid JSON
    string into a ``dict``. This hook function will be called after the result. It should be smart enough to convert a
    ``dict`` to any kind of element since the function it self does not know the hierarchy depth in JSON.
    """
    if 'blocks' in d:
        eid = d.get('id', '')
        name = d.get('name', '')
        blocks = d['blocks']
        circuit = Circuit(eid=eid, name=name, blocks=blocks)
        return circuit

    if 'registers' in d:
        eid = d.get('id', '')
        name = d.get('name', '')
        description = d.get('description', '')
        data_width = d.get('data_width', 32)
        base_address = d.get('base_address', 0)
        registers = d['registers']
        block = Block(eid=eid, name=name, description=description, data_width=data_width, base_address=base_address,
                      registers=registers)
        return block

    if 'fields' in d:
        eid = d.get('id', '')
        name = d.get('name', '')
        description = d.get('description', '')
        type = RegisterType(d.get('type', 'NORMAL'))
        address_offset = d.get('address_offset', 0)
        fields = d['fields']
        register = Register(eid=eid, name=name, description=description, rtype=type, address_offset=address_offset,
                            fields=fields)
        return register

    if 'access' in d:
        eid = d.get('id', '')
        description = d.get('description', '')
        access = FieldAccess(d.get('access', 'RW'))
        bit_offset = d.get('bit_offset', 0)
        bit_width = d.get('bit_width', 1)
        reset = d.get('reset', 0)
        field = Field(eid=eid, description=description, access=access, bit_offset=bit_offset, bit_width=bit_width, reset=reset)
        return field


def read_json(file: str) -> Union[Circuit, Block, Register, Field]:
    """Deserialize JSON document to Block object."""
    with open(file) as f:
        d = json.load(f, object_hook=json_deserialize)
        return d


def read_xlsx(file: str) -> Optional[Block]:
    """
    Parse excel (.xlsx) document to Block object.

    :param file: An TextIOWrapper object with read access.
    :return: Block object if success, None if any error.
    """
    raise NotImplementedError


def read_csv(file: str) -> Optional[Block]:
    """
    Parse .csv document to to Block object.

    :param file: An TextIOWrapper object with read access.
    :return: Block object if success, None if any error.
    """
    raise NotImplementedError


# JSON Output
# -----------

def json_serializer(elem: Element):
    return elem.to_dict()


def dump_json(elem: Element, output_stream=None):
    """Serialize this element to JSON formatted ``str``."""

    if not isinstance(elem, Element):
        msg = f'dump_json needs input of type "regen.Element" but received one of type "{type(elem).__name__}"'
        raise TypeError(msg)

    if output_stream is None:
        output_stream = sys.stdout

    json.dump(elem, output_stream, default=json_serializer, indent=2)


# Template Output
# ---------------

def render_template(blk: Block, template: str, output_stream=None):
    """
    Render Block using a specified template.
    """
    if not isinstance(blk, Block):
        raise TypeError(f'You can only render template on a Block object, received {type(blk).__name__}')

    # Configure and build jinja2 template
    env = Environment(
        loader=PackageLoader('regen', 'templates'),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    template = env.get_template(template)

    if output_stream is None:
        output_stream = sys.stdout

    s = template.render(block=blk)
    output_stream.write(s)
