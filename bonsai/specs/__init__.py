class Node:
    pass


class NodeRef:
    __slots__ = ('dest_types',)

    def __init__(self, *args):
        self.dest_types = args

    def __repr__(self):
        return f'NodeRef({self.dest_types!r})'


class List:
    __slots__ = ('of_type', 'nonempty')

    def __init__(self, of_type, nonempty=False):
        self.of_type = of_type
        self.nonempty = nonempty

    def __repr__(self):
        return f'List({self.of_type!r}, nonempty={self.nonempty!r})'


class Enum:
    __slots__ = ('variants',)

    def __init__(self, *args):
        self.variants = args


class Null:
    pass


class Boolean:
    pass


class String:
    pass


class Number:
    pass


def Optional(of_type):
    return NodeRef(Null, *of_type.dest_types)
