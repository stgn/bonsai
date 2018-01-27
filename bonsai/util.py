import typing


def subclasses(cls, and_self=False):
    """
    Return all subclasses for a given class.
    :param cls: A class object.
    :param and_self: Include the given class in the resulting list.
    """
    base = [cls] if and_self else []
    sub = cls.__subclasses__()
    return base + sub + [g for s in sub for g in subclasses(s, False)]


def fields(cls):
    return typing.get_type_hints(cls).items()


def iter_fields(from_types, with_type):
    for node_type in from_types:
        for field_key, field_type in fields(node_type):
            # see if this field references other nodes
            of_type = getattr(field_type, 'of_type', field_type)
            if isinstance(of_type, with_type):
                candidate_types = {x for c in of_type.dest_types for x in subclasses(c, True)}
                yield (node_type, field_key), [x for x in from_types if x in candidate_types]
