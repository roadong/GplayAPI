import struct
from google.protobuf.json_format import MessageToDict


def parse_protobuf_obj(obj):
    return MessageToDict(obj, False, False, False)


def read_int(byte_array, start):
    """Read the byte array, starting from *start* position,
    as an 32-bit unsigned integer"""
    return struct.unpack("!L", byte_array[start:][0:4])[0]


def to_big_int(byte_array):
    """Convert the byte array to a BigInteger"""
    array = byte_array[::-1]  # reverse array
    out = 0
    for key, value in enumerate(array):
        decoded = struct.unpack("B", bytes([value]))[0]
        out = out | decoded << key * 8
    return out


def has_prefetch(obj):
    try:
        return len(obj.preFetch) > 0
    except ValueError:
        return False


def has_list_response(obj):
    try:
        return obj.HasField('listResponse')
    except ValueError:
        return False


def has_search_response(obj):
    try:
        return obj.HasField('searchResponse')
    except ValueError:
        return False


def has_cluster(obj):
    try:
        return obj.HasField('cluster')
    except ValueError:
        return False


def has_tos_content(toc_response):
    try:
        return toc_response.HasField('tosContent')
    except ValueError:
        return False


def has_tos_token(toc_response):
    try:
        return toc_response.HasField('tosToken')
    except ValueError:
        return False


def has_cookie(toc_response):
    try:
        return toc_response.HasField('cookie')
    except ValueError:
        return False


def has_doc(obj):
    # doc an be a single object or a
    # RepeatedComposite object
    try:
        is_exist = obj.HasField('doc')
    except ValueError:
        try:
            is_exist = len(obj.doc) > 0
        except TypeError:
            is_exist = False

    return is_exist
