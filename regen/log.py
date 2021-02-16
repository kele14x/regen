import logging

__all__ = ['init']


def init(level: int = None, name: str = None):
    """Initialize a logger (from std logging library) with specified name and level
    :param level: Numeric logging level, usually an constant from logging. e.g. :py:const:`logging.WARNING`
    :param name: Name of the logger, global for python program
    :return: None
    """
    formatter = logging.Formatter('[%(levelname)s][%(name)s]: %(message)s')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.addHandler(handler)

    if level:
        logger.setLevel(level)


if __name__ == '__main__':
    init()

    root_logger = logging.getLogger()
    root_logger.debug('debug')
    root_logger.info('info')
    root_logger.warning('warning')
    root_logger.error('error')
    root_logger.critical('critical')
