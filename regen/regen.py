"""
regen is HDL slave register module generator for FPGA/ASIC design.

Usage:
    python regen.py INPUT -o OUTPUT
"""

import argparse
import io
import json
import logging
import math
import os
import string
import sys
from enum import Enum
from typing import Any, List, Optional

from jinja2 import Environment, PackageLoader

from .logging import init_logger
from .model import Block, Field, Register

__version__ = '0.1'

logger = logging.getLogger('main')


def read_json(file: io.TextIOWrapper) -> Optional[Block]:
    """
    Deserialize JSON document to Block object.

    :param file: An TextIOWrapper object with read access.
    :return: Block object if success, None if any error.
    """
    try:
        d = json.load(file)
    except json.JSONDecodeError as e:
        logger.critical(f'Error when parse json file: {e}')
        return None

    try:
        rm = Block(d)
    except KeyError as e:
        logger.critical(f'Error in {e}')
        return None
    return rm


def read_xlsx(file: str) -> Optional[Block]:
    """
    Parse excel (.xlsx) document to Block object.

    :param file: An TextIOWrapper object with read access.
    :return: Block object if success, None if any error.
    """
    raise NotImplementedError


def read_csv(file: io.TextIOWrapper) -> Optional[Block]:
    """
    Parse .csv document to to Block object.

    :param file: An TextIOWrapper object with read access.
    :return: Block object if success, None if any error.
    """
    raise NotImplementedError


def render_template(rm: Block, template: str, ) -> str:
    """
    Render Block using a specified template.

    :param rm: Block object
    :param template: Template name
    :return: rendered string
    """
    # Configure and build jinja2 template
    env = Environment(
        loader=PackageLoader('regen', 'templates'),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    template = env.get_template(template)
    return template.render(block=rm)


def parse_arguments(argv=None):
    """
    Parse arguments for program, using default library's argparse module.

    :param argv: Variable hold the arguments
    :return: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog='regen',
        description='A tool to generate AXI4-Lite slave register module'
    )

    # Input and Output Options

    # If user does not specify a input file, we read from stdin. This enables
    # chain this script with other tools support stdin and stdout.
    parser.add_argument(
        'input',
        default=sys.stdin,
        help='Read input from INPUT instead of stdin',
        nargs='?',
        type=argparse.FileType('r', encoding='UTF-8'),
    )

    # If user does not specify a output file, we write to stdout.
    # Note warning and error message will go to stderr, which by default,
    # will appear on terminal with stdout.
    parser.add_argument(
        '-o', '--output',
        default=sys.stdout,
        dest='output',
        help='Write output to OUTPUT instead of stdout',
        nargs='?',
        type=argparse.FileType('w', encoding='UTF-8'),
    )

    # If user does not specify a log file, we write to stderr. Note stderr by
    # default goes to terminal together with stdout.
    parser.add_argument(
        '-l', '--log',
        default=sys.stderr,
        dest='log',
        help='Write log to LOG instead of stderr',
        nargs='?',
        type=argparse.FileType('w', encoding='UTF-8'),
    )

    # Format Options

    # We can auto guess the format from file extension, but if needed user
    # can specify it explicitly
    parser.add_argument(
        '-f', '--from',
        choices=['json', 'xlsx', 'csv'],
        dest='from_format',
        help='Specify input format',
    )

    # By default convert to a SystemVerilog (.sv) module. Note that the builtin
    # template is chosen based on the output format.
    parser.add_argument(
        '-t', '--to',
        choices=['json', 'sv', 'v', 'vhd', 'vhdl', 'h', 'vh', 'svh'],
        dest='to_format',
        help='Specify output format',
    )

    # Using a costumed template instead of builtin ones. If user choose this,
    # the output format argument is ignored.
    parser.add_argument(
        '--template',
        default=None,
        dest='template',
        help='Specify the template to use. If using this option, '
             '-t/--to is ignored',
    )

    # Logging Options

    # By default, the logging level is set to WARNING, which means all
    # warning, error and critical error messages will be shown.
    # Using -q will set the logging level to ERROR, this will filter all
    # warning and lower priority messages.
    parser.add_argument(
        '-q', '--quiet',
        action='store_const',
        const=logging.ERROR,
        default=logging.WARNING,
        dest='verbosity',
        help='Show only critical and errors',
    )

    # Set the logging level to INFO, which will show most messages except DEBUG
    parser.add_argument(
        '-v', '--verbose',
        action='store_const',
        const=logging.INFO,
        dest='verbosity',
        help='Show almost all messages, excluding debug messages'
    )

    # Set the logging level to DEBUG, which will show all messages
    parser.add_argument(
        '-d', '--debug',
        action='store_const',
        const=logging.DEBUG,
        dest='verbosity',
        help='Show all messages, including debug messages'
    )

    # Misc options

    # Get the version string of this script
    parser.add_argument(
        '--version',
        action='version',
        version=__version__,
    )

    args = parser.parse_args(argv)
    return args


def main(argv=None):
    """Will be called if script is executed as script."""
    # skip first argument, which is path to script self
    args = parse_arguments(argv[1:])

    init_logger('main', level=args.verbosity)

    logger.debug(f'Regen version: {__version__}')
    logger.debug(f'Python version: {sys.version.split()[0]}')
    logger.debug(f'Arguments: {vars(args)}')

    # Guess Input Format

    if args.from_format is None:
        (name, ext) = os.path.splitext(args.input.name)
        if name == '<stdin>':
            args.from_format = 'json'
        elif ext in ['.json', '.xlsx', '.xls', '.csv']:
            args.from_format = ext[1:]
        else:
            logger.error(f'Please specify read format using -f/--from')
            sys.exit(2)

    # Guess Output Format

    if args.to_format is None:
        (name, ext) = os.path.splitext(args.output.name)
        if name == '<stdout>' or name == '<stderr>':
            args.to_format = 'sv'
        elif ext in ['.sv', '.v', '.vhd', '.vhdl', '.h', '.vh', '.svh']:
            args.to_format = ext[1:]
        else:
            logger.error(f'Please specify write format using -t/--to')
            sys.exit(2)

    # Choose Template

    if args.template is None:
        if args.to_format == 'sv':
            args.template = 'axi4l.sv.j2'
        elif args.to_format == 'v':
            args.template = 'axi4l.v.j2'
        elif args.to_format == 'vhd' or args.to_format == 'vhdl':
            args.template = 'axi4l.vhd.j2'
        elif args.to_format == 'h':
            args.template = 'c_header.h.j2'
        elif args.to_format == 'vh':
            args.template = 'verilog_header.vh.j2'
        elif args.to_format == 'svh':
            args.template = 'systemverilog_header.svh.j2'
        elif args.to_format == 'json':
            # JSON conversion is not done using template
            pass
        else:
            logger.error(f'Unsupported write format: {args.to_format}')
            sys.exit(2)

    # Read Input File

    if args.from_format == 'json':
        rm = read_json(args.input)
    elif args.from_format == 'xlsx' or args.from_format == 'xls':
        rm = read_xlsx(args.input)
    elif args.from_format == 'csv':
        rm = read_csv(args.input)
    else:
        logger.error(f'Unsupported read format: {args.from_format}')
        sys.exit(2)

    if not rm:
        logger.error(f'Error reading input file, exit...')
        sys.exit(2)

    # Render using template

    if args.to_format == 'json':
        s = rm.to_json()
    else:
        s = render_template(rm, args.template)

    # Write file

    args.output.write(s)
    args.output.close()

if __name__ == '__main__':
    main(sys.argv)
