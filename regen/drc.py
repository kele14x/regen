import logging
import string

from .elements import Block

char_set = string.ascii_letters + string.digits + '_'

logger = logging.getLogger('main')


def check_id_normalized(ids: str) -> bool:
    """
    Normalize block, register or field's name.

    :param ids: ID in string
    :return: Normalized name
    """
    for c in ids:
        if c not in char_set:
            logger.error(f'ID {ids} contains invalid char {c}')
            return False
    return True


def drc_normalized_id(b: Block):
    check_id_normalized(b.id)
    for r in b.registers:
        check_id_normalized(r.id)
        for f in r.fields:
            check_id_normalized(f.id)


def run_drc(b: Block):
    drc_normalized_id(b)
