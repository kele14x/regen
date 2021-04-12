import logging
import string

from .model import Block

name_set = string.ascii_letters + string.digits + '_'

logger = logging.getLogger('main')


def check_name_normalized(name: str) -> str:
    """
    Normalize block, register or field's name.

    :param name: Name in string
    :return: Normalized name
    """
    for c in name:
        if c not in name_set:
            logger.error(f'Name {name} contains invalid char {c}')
            return False
    return True


def drc_normalized_name(b: Block):
    check_name_normalized(b.name)
    for r in b.registers:
        check_name_normalized(r.name)
        for f in r.fields:
            check_name_normalized(f.name)


def run_drc(b: Block):
    drc_normalized_name(b)
