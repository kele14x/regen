import argparse
import json
import logging
import pathlib
import sys
from typing import Optional

from jinja2 import Environment, PackageLoader

from regen.log import init as init_logging
from regen.rmap import Storage

__version__ = '0.1'

logger = logging.getLogger(__name__)


def read_json(fn: str) -> Optional[Storage]:
    """
    Deserialize JSON document to register map storage object.

    :param fn: Path to the JSON (.json) file
    :return: Register map storage object
    """
    try:
        with open(fn) as f:
            try:
                d = json.load(f)
            except json.JSONDecodeError as e:
                logger.critical('Error when parse json file %s', e)
                return None
    except Exception as e:
        logger.critical('Error when open file %s', e)
        return None

    return Storage(d)


def read_xlsx(fn: str) -> Optional[Storage]:
    """
    Parse excel (.xlsx) document to register map storage object.

    :param fn: Path to the excel (.xlsx) file
    :return: Register map storage object
    """
    raise NotImplementedError


def write_sv(fn: str, template: str, rs: Storage) -> None:
    """Write system verilog (.sv) on specified path.

    :param fn: Path to output directory
    :param template: Template name
    :param rs: Register map storage object
    :return: None
    """

    # Configure and build jinja2 template
    env = Environment(
        loader=PackageLoader('regen', 'templates'),
        autoescape=False,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
    )
    template = env.get_template('%s.v.j2' % template)

    with open(fn, 'w') as f:
        f.write(template.render(data=rs))


def parse_arguments(argv: Optional[str] = None) -> argparse.Namespace:
    """Parse arguments for program

    :param argv: Variable hold the arguments
    :return: Parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog='regen',
        description='A tool to generate slave register module.'
    )

    parser.add_argument('infile',
                        help='Input of the content file',
                        default=None)

    parser.add_argument('-f', '--from',
                        help='Convert from format',
                        choices=['json', 'xlsx'])

    parser.add_argument('-t', '--template',
                        dest='template',
                        help='Template to use',
                        choices=['axi4l', 'bram'], default='bram')

    parser.add_argument('-o', '--output',
                        dest='output',
                        help='Where to output the generated files.')

    parser.add_argument('-v', '--verbose',
                        action='store_const',
                        const=logging.INFO,
                        dest='verbosity',
                        help='Show all messages.')

    parser.add_argument('-q', '--quiet',
                        action='store_const',
                        const=logging.CRITICAL,
                        dest='verbosity',
                        help='SHow only critical errors.')

    parser.add_argument('-d', '--debug',
                        action='store_const',
                        const=logging.DEBUG,
                        dest='verbosity',
                        help='Show all messages, including debug messages.')

    parser.add_argument('--version',
                        action='version',
                        version=__version__)

    args = parser.parse_args(argv)
    return args


def main(argv=None):
    args = parse_arguments(argv)

    init_logging(level=args.verbosity, name=__name__)

    logger.debug('Regen version: %s', __version__)
    logger.debug('Python version: %s', sys.version.split()[0])

    # Input file
    json_obj = read_json(args.infile)
    if not json_obj:
        exit(2)

    # Write file
    if args.output:
        output_path = pathlib.Path(args.output)
        try:
            output_path.mkdir()
        except FileExistsError:
            logger.info('Output path "%s" already exists.', output_path)

        write_sv(output_path / 'output.sv', args.template, json_obj)
    else:
        logger.warning('No output path (-o/--output) specified, assume dry run')
