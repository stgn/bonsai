import logging
import brotli
from io import BytesIO
from bonsai.codec import decoder, encoder

logger = logging.getLogger(__name__)
MAGIC = '盆栽'.encode('utf-16-be')


def write_compressed_section(data, fp):
    compressed = brotli.compress(data)
    compressed_len = len(compressed)
    fp.write(len(data).to_bytes(4, 'big'))
    fp.write(compressed_len.to_bytes(4, 'big'))
    fp.write(compressed)
    return compressed_len


def read_compressed_section(fp):
    fp.seek(4, 1)  # don't need this for now
    compressed_len = int.from_bytes(fp.read(4), 'big')
    compressed = fp.read(compressed_len)
    return brotli.decompress(compressed)


def encode(spec, ast, fp):
    logger.info('Encoding...')

    with BytesIO() as buf:
        e = encoder.GraphEncoder(spec, ast, buf)
        string_table = e.encode()
        graph_data = buf.getvalue()

    fp.write(MAGIC)

    string_table_bin = b'\0'.join(x.encode('utf-8') for x in string_table)
    string_table_packed_len = write_compressed_section(string_table_bin, fp)

    graph_data_len = len(graph_data)
    fp.write(graph_data_len.to_bytes(4, 'big'))
    fp.write(graph_data)

    logger.info(f'String table: {string_table_packed_len: 8,} bytes')
    logger.info(f' Syntax tree: {graph_data_len: 8,} bytes')


def decode(spec, fp):
    logger.info('Decoding...')

    if fp.read(4) != MAGIC:
        raise ValueError('Not a Bonsai format file')

    string_table_bin = read_compressed_section(fp)
    string_table = [x.decode('utf-8') for x in string_table_bin.split(b'\0')]

    fp.seek(4, 1)  # not sure we need this either

    d = decoder.GraphDecoder(fp, spec, string_table)
    return d.decode()
