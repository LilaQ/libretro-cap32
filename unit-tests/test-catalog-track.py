#!/usr/bin/env python3
"""Directory-track regression cases: python3 test-catalog-track.py CORE_PATH."""
import ctypes
import pathlib
import sys
import tempfile

core = ctypes.CDLL(str(pathlib.Path(sys.argv[1]).resolve()))
buffer = ctypes.create_string_buffer(128 * 1024)
ctypes.c_void_p.in_dll(core, 'pbGPBuffer').value = ctypes.addressof(buffer)
drive = ctypes.c_byte.in_dll(core, 'driveA')
core.dsk_load.argtypes = [ctypes.c_char_p, ctypes.c_void_p, ctypes.c_char]
core.loader_run.argtypes = [ctypes.c_void_p]


def disk(system=False, hidden=False):
    directory = bytearray(b'\xe5' * 2048)
    for i, name in enumerate((b'DATA    BIN', b'START   BIN')):
        entry = bytearray(32)
        entry[1:12] = name
        entry[15:17] = bytes([1, i + 2])
        if hidden and i == 1:
            entry[10] |= 128
        directory[i * 32:(i + 1) * 32] = entry
    result = bytearray(256)
    result[:8] = b'MV - CPC'
    result[48:50] = bytes([40, 1])
    result[50:52] = (4864).to_bytes(2, 'little')
    for track in range(40):
        header = bytearray(256)
        header[:10] = b'Track-Info'
        header[16] = track
        header[20:22] = bytes([2, 9])
        for sector in range(9):
            header[24 + sector * 8:28 + sector * 8] = bytes(
                [track, 0, (0x41 if system else 0xc1) + sector, 2])
        data = bytearray(4608)
        if track == (2 if system else 0):
            data[:2048] = directory
        result += header + data
    return result


class Entry(ctypes.Structure):
    _fields_ = [('filename', ctypes.c_char * 20), ('hidden', ctypes.c_bool),
                ('readonly', ctypes.c_bool)]

class Catalogue(ctypes.Structure):
    _fields_ = [('art', ctypes.c_bool), ('cpm', ctypes.c_bool),
                ('count', ctypes.c_int), ('entries', Entry * 64),
                ('listed', ctypes.c_int), ('hidden', ctypes.c_int),
                ('first_listed', ctypes.c_int), ('first_hidden', ctypes.c_int),
                ('hidden_track', ctypes.c_int), ('listed_track', ctypes.c_int)]

catalogue = Catalogue.in_dll(core, 'catalogue')


def check(name, data, expected, track=None):
    with tempfile.TemporaryDirectory() as directory:
        path = pathlib.Path(directory) / 'test.dsk'
        path.write_bytes(data)
        assert core.dsk_load(str(path).encode(), ctypes.addressof(drive), b'A') == 0
        command = ctypes.create_string_buffer(256)
        core.loader_run(command)
        assert catalogue.count == len(expected), (name, catalogue.count)
        actual = [(catalogue.entries[i].filename.decode(), catalogue.entries[i].hidden)
                  for i in range(catalogue.count)]
        assert actual == expected, (name, actual)
        if track is not None:
            assert catalogue.listed_track == track, (name, catalogue.listed_track)
        print('PASS', name)


# Zero-filled boot sectors look like catalogue art to the legacy scanner.
check('system-boot-is-not-catalogue', disk(system=True, hidden=True),
      [('DATA.BIN', False), ('START.BIN', True)], 2)
check('hidden-loader-keeps-hidden-attribute', disk(hidden=True),
      [('DATA.BIN', False), ('START.BIN', True)], 0)

# A fake directory entry in a boot sector must not precede the real catalogue.
b = disk(system=True)
b[512:544] = bytes([0]) + b'FAKE    BAS' + bytes([0, 0, 0, 1, 2]) + bytes(15)
check('ignore-boot-filename', b, [('DATA.BIN', False), ('START.BIN', False)], 2)

# Retain nonstandard-track discovery if the normal directory has no entries.
b = disk()
b[256 + 4864:256 + 4864 + 4864] = b[256:256 + 4864]
b[512:256 + 4864] = bytes(4608)
check('fallback-track-without-art-leak', b,
      [('DATA.BIN', False), ('START.BIN', False)], 1)

# Actual catalogue art on the directory track keeps its existing treatment.
b = disk()
b[512:544] = bytes(32)
check('directory-art-preserved', b, [('START.BIN', True)])
