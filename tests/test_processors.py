# -*- coding: utf-8 -*-
from nylas.logging.log import _safe_encoding_renderer


def test_safe_encoding_renderer():
    # Check that unicode strings and regular objects don't get altered.
    dct = {'ascii_string': 'ascii_str',
           'unicode_str': unicode('just a unicode str'),
           'regular_object': ['has strings inside']}
    _safe_encoding_renderer(None, None, dct)
    assert isinstance(dct['ascii_string'], unicode)
    assert dct['ascii_string'] == 'ascii_str'

    assert isinstance(dct['unicode_str'], unicode)
    assert dct['unicode_str'] == 'just a unicode str'

    assert dct['regular_object'] == ['has strings inside']

    # Check that strings in weird encodings get replaced by \ufffd.
    dct = {'s': u'une chaîne pas comme les autres'.encode('latin-1'),
           's2': u'På gensyn!'.encode('cp865')}
    _safe_encoding_renderer(None, None, dct)
    assert isinstance(dct['s'], unicode)
    assert isinstance(dct['s2'], unicode)

    assert dct['s'] == u'une cha\ufffdne pas comme les autres'
    assert dct['s2'] == u'P\ufffd gensyn!'
