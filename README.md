# bonsai

A personal research project for a highly-compact binary file format for JavaScript ASTs.

## How does it work?

The bonsai encoder can be broken down into two stages:

1. Node de-duplication, which turns the abstract syntax tree into a directed acyclic graph. This usually cuts down the total node count by half. This is roughly analogous to the Lempel–Ziv algorithms used in other compression formats.
2. Encoding the syntax graph as a packed bitstream, using Huffman coding for node types, single bits for booleans, etc. Strings however are compressed separately using a general-purpose compression format—no point reinventing the wheel (not here at least).

## Yawn... Show me numbers!

Here's some filesizes (in bytes, of course):

Filename | Original | bonsai | Brotli | gzip
---------|----------|--------|--------|-----
react-dom v16.2.0 (minified) | 94,498 | 26,168 | 26,702 | 30,533
Vue.js v2.5.13 (minified) | 86,510 | 29,011 | 28,129 | 31,259

bonsai competes with Brotli and gzip in terms of size, but it is much faster to parse *in theory*. However, since the only implementation (this one) is written in Python, it is not, and it won't get much faster unless I implement it in something else.

(I wanted to include BinJs in the comparison but I couldn't get it working. Maybe later.)

## What about [BinJs](https://github.com/binast)?

I wrote most of this mostly for fun and learning back in November 2016—a few months before BinJs appeared. I'm not too familiar with it, but I'll be keeping an eye on it. Maybe I can use what I've learned here and apply it there somehow. :sweat_smile: