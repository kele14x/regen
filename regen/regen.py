"""
regen is HDL slave register module generator for FPGA/ASIC design.

Usage:
    python regen.py [options] <file>
"""

import argparse
import logging
import os
import sys

from .drc import run_drc
from .io import read_json, read_xlsx, read_csv, render_template, dump_json
from .logging import init_logger
from .version import __version__

logger = logging.getLogger('main')


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

    # TODO: Reconsider pipe from <stdin>. For example, specify input using '-'
    parser.add_argument(
        'input',
        help='Read input from INPUT file',
    )

    # If user does not specify a output file, we will not write to file.
    parser.add_argument(
        '-o', '--output',
        dest='output',
        help='Write output to OUTPUT file',
        nargs='?',
    )

    # If user does not specify a log file, we write to stderr. Note stderr by
    # default goes to terminal together with stdout.
    parser.add_argument(
        '-l', '--log',
        dest='log',
        help='Write log to LOG file instead of <stderr>',
        nargs='?',
    )

    # Format Options

    # We can auto guess the format from file extension, but if needed user
    # can specify it explicitly
    parser.add_argument(
        '-f', '--from',
        choices=['json', 'xlsx', 'xls', 'csv'],
        dest='from_format',
        help='Specify input format',
    )

    # By default convert to a SystemVerilog (.sv) module. Note that the builtin
    # template is chosen based on the output format.
    parser.add_argument(
        '-t', '--to',
        choices=['json', 'sv', 'v', 'vhd', 'vhdl', 'h', 'vh', 'svh', 'txt'],
        dest='to_format',
        help='Specify output format',
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


def format_from_ext(filename: str) -> str:
    (_, ext) = os.path.splitext(filename)
    return ext[1:]


def main(argv=None):
    """Will be called if script is executed as script."""
    args = parse_arguments(argv)

    init_logger('main', level=args.verbosity)

    logger.debug(f'Regen version: {__version__}')
    logger.debug(f'Python version: {sys.version.split()[0]}')
    logger.debug(f'Arguments: {vars(args)}')

    # Guess Input Format

    if args.from_format is None:
        from_format = format_from_ext(args.input)
    else:
        from_format = args.from_format

    # Guess Output Format

    if args.to_format is None:
        to_format = format_from_ext(args.output)
    else:
        to_format = args.to_format

    # Choose Template

    templates = {
        'h': 'c_header.h.j2',
        'sv': 'systemverilog.sv.j2',
        'svh': 'systemverilog_header.svh.j2',
        'txt': 'plain.txt.j2',
        'v': 'verilog.v.j2',
        'vh': 'verilog_header.vh.j2',
        'vhd': 'vhdl.vhd.j2',
        'json': ''
    }
    template_name = templates.get(to_format, '')

    # Read Input File

    if from_format == 'json':
        blk = read_json(args.input)
    elif from_format == 'xlsx' or args.from_format == 'xls':
        blk = read_xlsx(args.input)
    elif from_format == 'csv':
        blk = read_csv(args.input)
    else:
        msg = f'Unsupported read format: {args.from_format}'
        logger.error(msg)
        raise(msg)

    if not blk:
        logger.error('Error reading input file, exit...')
        sys.exit(2)

    # Run DRC

    run_drc(blk)

    # Render using template

    if args.output is not None:
        with open(args.output, 'w', encoding='UTF-8') as f:
            if args.to_format == 'json':
                dump_json(blk, f)
            else:
                render_template(blk, template_name, f)


if __name__ == '__main__':
    main()
