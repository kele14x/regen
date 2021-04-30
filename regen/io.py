"""
io is module for input and output function.
"""
import json
import logging
import sys
from typing import Optional, Union

from .base import Element
from .elements import Circuit, Block, Register, Field

__all__ = ['read_json', 'read_csv', 'read_xlsx']

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
        id_ = d.get('id', '')
        name = d.get('name', '')
        blocks = d['blocks']
        circuit = Circuit(d, id_=id_, name=name, blocks=blocks)
        return circuit

    if 'registers' in d:
        block = Block(d)
        return block

    if 'fields' in d:
        register = Register(d)
        return register

    if 'access' in d:
        field = Field(d)
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
    elem.to_dict()


def dump_json(elem: Element, output_stream=None):
    """Serialize this element to JSON formatted ``str``."""

    if not isinstance(elem, Element):
        msg = f'dump_json needs input of type "regen.Element" but received one of type "{type(elem).__name__}"'
        raise TypeError(msg)

    if output_stream is None:
        output_stream = sys.stdout

    output_stream.write(json.dumps(elem, default=json_serializer, indent=2))
