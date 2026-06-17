import os
import tempfile
from .vendor.six.moves import range

def printable_decimal_and_hex(num):
    return "{0:d} (0x{0:x})".format(num)

def assert_index_sane(index, upper_bound_exclusive):
    if not isinstance(index, int):
        raise TypeError("Indices should be integers; '%s' is not" % (index))
    if not (0 <= index < upper_bound_exclusive):
        raise IndexError("Index %d out of range [%d, %d)" % (index, 0, upper_bound_exclusive))


class ObjectLookupDict(object):

    def __init__(self, id_list, object_list):
        self.id_list = id_list
        self.object_list = object_list

    def __getitem__(self, index):
        assert_index_sane(index, len(self.id_list))

        val = self.id_list[index]
        if val >= len(self.object_list) or val == 0xff:
            return None
        return self.object_list[val]

    def __setitem__(self, index, value):
        assert_index_sane(index, len(self.id_list))

        self.id_list[index] = value.index if value is not None else 0xff


def name_without_zeroes(name):
    """
    Return a human-readable name without LSDJ's trailing zeroes.

    :param name: the name from which to strip zeroes
    :rtype: the name, without trailing zeroes
    """
    if isinstance(name, bytes):
        first_zero = name.find(b'\0')
        if first_zero == -1:
            return name
        return name[:first_zero]
    else:
        first_zero = name.find('\0')
        if first_zero == -1:
            return name
        return name[:first_zero]


class temporary_file:

    def __enter__(self):
        (tmp_handle, tmp_abspath) = tempfile.mkstemp()
        os.close(tmp_handle)
        self.abspath = tmp_abspath
        return self.abspath

    def __exit__(self, t, value, traceback):
        if hasattr(self, 'abspath') and self.abspath is not None:
            os.unlink(self.abspath)
