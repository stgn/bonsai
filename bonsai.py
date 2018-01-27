import json
import click
import logging
from time import perf_counter
from importlib import import_module
from bonsai import format

logger = logging.getLogger(__name__)


@click.group()
@click.pass_context
@click.option('--verbose', '-v', count=True)
@click.option('--spec', default='shift_es5')
def cli(ctx, verbose, spec):
    levels = (logging.INFO, logging.DEBUG)
    logging.basicConfig(format='[{levelname}][{name}] {message}',
                        style='{', level=levels[verbose - 1])
    ctx.obj['SPEC'] = import_module(f'bonsai.specs.{spec}')  # wat


@cli.command()
@click.pass_context
@click.argument('input', type=click.File('rb'))
@click.argument('output', type=click.File('wb'))
def encode(ctx, input, output):
    spec = ctx.obj['SPEC']
    ast = json.load(input, parse_int=str, parse_float=str)
    start = perf_counter()
    format.encode(spec, ast, output)
    logger.info(f'Encoded in {(perf_counter() - start) * 1000:.2f}ms')


@cli.command()
@click.pass_context
@click.argument('input', type=click.File('rb'))
@click.argument('output', type=click.File('w'))
def decode(ctx, input, output):
    spec = ctx.obj['SPEC']
    start = perf_counter()
    ast = format.decode(spec, input)
    logger.info(f'Decoded in {(perf_counter() - start) * 1000:.2f}ms')
    json.dump(ast, output, separators=(',', ':'))


if __name__ == '__main__':
    cli(obj={})
