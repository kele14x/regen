"""
regen is HDL slave register module generator for FPGA/ASIC design.

Usage:
    python regen.py INPUT -o OUTPUT
"""

import argparse
import logging
import os
import sys

from .drc import run_drc
from .io import read_json, read_xlsx, read_csv, render_template, dump_json
from .logging import init_logger

__version__ = '0.1'

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

    # If user does not specify a input file, we read from stdin. This enables
    # chain this script with other tools support stdin and stdout.
    parser.add_argument(
        'input',
        help='Read input from INPUT instead of stdin',
        nargs='?',
    )

    # If user does not specify a output file, we write to stdout.
    # Note warning and error message will go to stderr, which by default,
    # will appear on terminal with stdout.
    parser.add_argument(
        '-o', '--output',
        dest='output',
        help='Write output to OUTPUT instead of stdout',
        nargs='?',
    )

    # If user does not specify a log file, we write to stderr. Note stderr by
    # default goes to terminal together with stdout.
    parser.add_argument(
        '-l', '--log',
        dest='log',
        help='Write log to LOG instead of stderr',
        nargs='?',
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
        choices=['json', 'sv', 'v', 'vhd', 'vhdl', 'h', 'vh', 'svh', 'txt'],
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
    args = parse_arguments(argv)

    init_logger('main', level=args.verbosity)

    logger.debug(f'Regen version: {__version__}')
    logger.debug(f'Python version: {sys.version.split()[0]}')
    logger.debug(f'Arguments: {vars(args)}')

    # Guess Input Format

    if args.from_format is None:
        (name, ext) = os.path.splitext(args.input)
        if ext in ['.json', '.xlsx', '.xls', '.csv']:
            args.from_format = ext[1:]
        else:
            logger.error(f'Please specify read format using -f/--from')
            sys.exit(2)

    # Guess Output Format

    if args.to_format is None:
        (name, ext) = os.path.splitext(args.output)
        if ext in ['.sv', '.v', '.vhd', '.vhdl', '.h', '.vh', '.svh',
                   '.json', '.txt']:
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
        elif args.to_format == 'txt':
            args.template = 'plain.txt.j2'
        elif args.to_format == 'json':
            # JSON conversion is not done using template
            pass
        else:
            logger.error(f'Unsupported write format: {args.to_format}')
            sys.exit(2)

    # Read Input File

    if args.from_format == 'json':
        blk = read_json(args.input)
    elif args.from_format == 'xlsx' or args.from_format == 'xls':
        blk = read_xlsx(args.input)
    elif args.from_format == 'csv':
        blk = read_csv(args.input)
    else:
        logger.error(f'Unsupported read format: {args.from_format}')
        sys.exit(2)

    if not blk:
        logger.error(f'Error reading input file, exit...')
        sys.exit(2)

    # Run DRC

    blk = blk.expand()
    run_drc(blk)

    # Render using template

    if args.output is None:
        fp = sys.stdout
    else:
        fp = open(args.output, 'w', encoding='UTF-8')

    if args.to_format == 'json':
        dump_json(blk, fp)
    else:
        render_template(blk, args.template, fp)


if __name__ == '__main__':
    main()
