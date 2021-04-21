"""Logging module helper."""

import logging

def init_logger(name, level: int = None):
    """
    Initialize the logger with specified name and level.

    :param level: Numeric logging level, usually an constant from logging.
    e.g. :py:const:`logging.WARNING`.
    """
    formatter = logging.Formatter('[%(levelname)s] [%(name)s] %(message)s')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.addHandler(handler)

    if level:
        logger.setLevel(level)
