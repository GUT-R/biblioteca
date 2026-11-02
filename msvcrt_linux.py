# WARNING: Esse módulo existe por padrão no Python do Windows 
#  mas eu tive que usar IA para traze-lo pro Linux.
#  Se você usa Windows, pode apagar esse arquivo.

"""A POSIX compatibility implementation of Python's :mod:`msvcrt` API.

This module is intended for Linux and other POSIX systems.  It implements
console input/output and file-descriptor operations using termios, select,
os, and fcntl.

It is a compatibility layer, not an implementation of Microsoft's C
runtime.  In particular, POSIX file descriptors are used as their own
"handles", text mode has no effect, and Windows error-mode/debug-report
functions are unavailable.

Place this file somewhere on sys.path and use ``import msvcrt``.
"""

from __future__ import annotations

import ctypes
import errno
import fcntl
import gc
import os
import select
import sys
import time
from collections import deque
from contextlib import contextmanager
from typing import Iterator

try:
    import termios
    import tty
except ImportError as exc:  # pragma: no cover - Linux/POSIX is the target
    raise ImportError("this msvcrt compatibility module requires POSIX termios") from exc

__all__ = [
    "LK_LOCK", "LK_NBLCK", "LK_NBRLCK", "LK_RLCK", "LK_UNLCK",
    "O_TEXT", "O_BINARY", "O_NOINHERIT",
    "locking", "setmode", "open_osfhandle", "get_osfhandle",
    "kbhit", "getch", "getwch", "getche", "getwche",
    "putch", "putwch", "ungetch", "ungetwch", "heapmin",
    "GetErrorMode", "SetErrorMode",
]

# Values used by the Microsoft CRT.  Keep them stable for code which compares
# the constants, even though their implementation here is POSIX-based.
LK_UNLCK = 0
LK_LOCK = 1
LK_NBLCK = 2
LK_NBRLCK = 3
LK_RLCK = 4

# POSIX terminals do not translate CR/LF in text mode.  Both modes therefore
# have the same value/behaviour here.  O_NOINHERIT maps to close-on-exec.
O_TEXT = 0
O_BINARY = 0
O_NOINHERIT = getattr(os, "O_CLOEXEC", 0)

# Windows extended-key scan codes.  These are used to translate common ANSI
# terminal escape sequences into the two-byte convention used by getch().
_ESCAPE_KEYS: dict[bytes, tuple[int, int]] = {
    b"[A": (0xE0, 0x48),  # Up
    b"[B": (0xE0, 0x50),  # Down
    b"[C": (0xE0, 0x4D),  # Right
    b"[D": (0xE0, 0x4B),  # Left
    b"OA": (0xE0, 0x48),  # Up (SS3)
    b"OB": (0xE0, 0x50),  # Down (SS3)
    b"OC": (0xE0, 0x4D),  # Right (SS3)
    b"OD": (0xE0, 0x4B),  # Left (SS3)
    b"[H": (0xE0, 0x47),  # Home
    b"[F": (0xE0, 0x4F),  # End
    b"[1~": (0xE0, 0x47),  # Home (alternate)
    b"[4~": (0xE0, 0x4F),  # End (alternate)
    b"OH": (0xE0, 0x47),  # Home (SS3)
    b"OF": (0xE0, 0x4F),  # End (SS3)
    b"[2~": (0xE0, 0x52),  # Insert
    b"[3~": (0xE0, 0x53),  # Delete
    b"[5~": (0xE0, 0x49),  # Page Up
    b"[6~": (0xE0, 0x51),  # Page Down
    b"OP": (0x00, 0x3B),  # F1
    b"OQ": (0x00, 0x3C),  # F2
    b"OR": (0x00, 0x3D),  # F3
    b"OS": (0x00, 0x3E),  # F4
    b"[15~": (0x00, 0x3F),  # F5
    b"[17~": (0x00, 0x40),  # F6
    b"[18~": (0x00, 0x41),  # F7
    b"[19~": (0x00, 0x42),  # F8
    b"[20~": (0x00, 0x43),  # F9
    b"[21~": (0x00, 0x44),  # F10
    b"[23~": (0x00, 0x85),  # F11
    b"[24~": (0x00, 0x86),  # F12
}

# Separate pushback queues mirror the byte and wide-character CRT functions.
_byte_pushback: deque[bytes] = deque()
_wide_pushback: deque[str] = deque()

# A short delay distinguishes a literal Escape press from an ANSI key sequence.
_ESCAPE_TIMEOUT = 0.035
_MAX_ESCAPE_SEQUENCE = 16


def _stdin_fd() -> int:
    """Return stdin's descriptor, raising OSError if stdin has no descriptor."""
    try:
        return sys.stdin.fileno()
    except (AttributeError, OSError, ValueError) as exc:
        raise OSError(errno.ENOTTY, "standard input has no usable file descriptor") from exc


def _stdout_fd() -> int:
    """Return stdout's descriptor, raising OSError if stdout has no descriptor."""
    try:
        return sys.stdout.fileno()
    except (AttributeError, OSError, ValueError) as exc:
        raise OSError(errno.ENOTTY, "standard output has no usable file descriptor") from exc


@contextmanager
def _raw_input() -> Iterator[int]:
    """Temporarily put a terminal into raw mode and always restore its state."""
    fd = _stdin_fd()
    if not os.isatty(fd):
        # Pipes/files can still be read, although they do not provide key-level
        # input in the same sense as an interactive terminal.
        yield fd
        return

    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd, termios.TCSANOW)
        yield fd
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def _read_byte(fd: int) -> bytes:
    """Read exactly one byte from fd. Ctrl-C behaves like the Windows CRT."""
    while True:
        data = os.read(fd, 1)
        if not data:
            raise OSError(errno.EIO, "end of input while reading the console")
        if data == b"\x03":
            raise KeyboardInterrupt
        return data


def _read_byte_timeout(fd: int, timeout: float) -> bytes | None:
    readable, _, _ = select.select([fd], [], [], timeout)
    if not readable:
        return None
    return _read_byte(fd)


def _push_bytes_front(data: bytes) -> None:
    for value in reversed(data):
        _byte_pushback.appendleft(bytes((value,)))


def _read_escape_tail(fd: int) -> bytes:
    """Read a short ANSI escape-sequence tail without waiting for another key."""
    tail = bytearray()
    first = _read_byte_timeout(fd, _ESCAPE_TIMEOUT)
    if first is None:
        return b""
    tail.extend(first)

    while len(tail) < _MAX_ESCAPE_SEQUENCE:
        # CSI sequences usually end in a byte in the range 0x40..0x7e.
        if len(tail) > 1 and 0x40 <= tail[-1] <= 0x7E and tail[0] in (ord("["), ord("O")):
            break
        nxt = _read_byte_timeout(fd, _ESCAPE_TIMEOUT)
        if nxt is None:
            break
        tail.extend(nxt)
    return bytes(tail)


def _read_key_byte(fd: int, *, wide: bool = False) -> bytes:
    """Read one CRT-style byte, translating recognized terminal key sequences."""
    if _byte_pushback:
        return _byte_pushback.popleft()

    first = _read_byte(fd)
    if first != b"\x1b":
        return first

    tail = _read_escape_tail(fd)
    if not tail:
        return first

    mapped = _ESCAPE_KEYS.get(tail)
    if mapped is None:
        # It was an unrecognized escape sequence. Return Escape now and keep
        # the remaining bytes available to subsequent reads instead of losing
        # user input.
        _push_bytes_front(tail)
        return first

    prefix, scan_code = mapped
    if wide:
        _wide_pushback.appendleft(chr(scan_code))
    else:
        _byte_pushback.appendleft(bytes((scan_code,)))
    return bytes((prefix,))


def _read_utf8_character(fd: int) -> str:
    """Read one UTF-8 code point from the terminal."""
    first = _read_key_byte(fd, wide=True)

    # Extended-key prefixes are one-character values in the wide API too.
    if first in (b"\x00", b"\xe0"):
        return first.decode("latin-1")

    lead = first[0]
    if lead < 0x80:
        return first.decode("ascii")
    if 0xC2 <= lead <= 0xDF:
        count = 2
    elif 0xE0 <= lead <= 0xEF:
        count = 3
    elif 0xF0 <= lead <= 0xF4:
        count = 4
    else:
        return "\ufffd"

    raw = bytearray(first)
    for _ in range(count - 1):
        raw.extend(_read_byte(fd))
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return "\ufffd"


def _echo_byte(value: bytes) -> None:
    if value and 0x20 <= value[0] < 0x7F:
        _write_all(_stdout_fd(), value)


def _echo_wide(value: str) -> None:
    if value.isprintable():
        _write_all(_stdout_fd(), value.encode("utf-8"))


def _write_all(fd: int, data: bytes) -> None:
    view = memoryview(data)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise OSError(errno.EIO, "console write made no progress")
        view = view[written:]


def locking(fd: int, mode: int, nbytes: int, /) -> None:
    """Lock or unlock nbytes from fd's current position.

    Uses POSIX advisory record locks (fcntl.lockf). LK_LOCK/LK_RLCK retry
    once per second, for up to ten attempts. All lock modes are exclusive,
    matching the Microsoft CRT's _locking behaviour.
    """
    if not isinstance(fd, int):
        raise TypeError("fd must be an integer")
    if not isinstance(mode, int):
        raise TypeError("mode must be an integer")
    if not isinstance(nbytes, int):
        raise TypeError("nbytes must be an integer")
    if nbytes <= 0:
        raise OSError(errno.EINVAL, "nbytes must be greater than zero")
    if mode not in (LK_LOCK, LK_NBLCK, LK_NBRLCK, LK_RLCK, LK_UNLCK):
        raise OSError(errno.EINVAL, "invalid locking mode")

    sys.audit("msvcrt.locking", fd, mode, nbytes)
    # Validate the descriptor before asking fcntl to operate on it.
    os.fstat(fd)
    if mode == LK_UNLCK:
        fcntl.lockf(fd, fcntl.LOCK_UN, nbytes, 0, os.SEEK_CUR)
        return None

    blocking_mode = mode in (LK_LOCK, LK_RLCK)
    operation = fcntl.LOCK_EX
    if not blocking_mode:
        operation |= fcntl.LOCK_NB

    attempts = 10 if blocking_mode else 1
    for attempt in range(attempts):
        try:
            fcntl.lockf(fd, operation, nbytes, 0, os.SEEK_CUR)
            return None
        except OSError as exc:
            if exc.errno not in (errno.EACCES, errno.EAGAIN):
                raise
            if attempt + 1 == attempts:
                raise
            time.sleep(1)


def setmode(fd: int, flags: int, /) -> int:
    """Set a descriptor's text/binary mode and return its previous mode.

    POSIX file descriptors do not perform the Windows CRT's CR/LF text-mode
    translation. Consequently, this is a validated no-op and returns O_BINARY.
    """
    if not isinstance(flags, int):
        raise TypeError("flags must be an integer")
    os.fstat(fd)
    if flags not in (O_TEXT, O_BINARY):
        raise OSError(errno.EINVAL, "unsupported file mode on POSIX")
    return O_BINARY


def open_osfhandle(handle: int, flags: int, /) -> int:
    """Treat a POSIX file descriptor as a CRT descriptor and take its ownership.

    On POSIX, a file descriptor already is the native handle, so its integer
    value is returned unchanged. The caller must not continue treating it as
    an independently owned descriptor.
    """
    if not isinstance(handle, int):
        raise TypeError("handle must be an integer")
    if not isinstance(flags, int):
        raise TypeError("flags must be an integer")
    sys.audit("msvcrt.open_osfhandle", handle, flags)
    os.fstat(handle)
    # The descriptor is already a POSIX handle. Apply the append flag where
    # possible; access mode itself cannot be changed after open().
    if hasattr(os, "O_APPEND"):
        status_flags = fcntl.fcntl(handle, fcntl.F_GETFL)
        if flags & os.O_APPEND:
            status_flags |= os.O_APPEND
        else:
            status_flags &= ~os.O_APPEND
        fcntl.fcntl(handle, fcntl.F_SETFL, status_flags)
    try:
        os.set_inheritable(handle, not bool(flags & O_NOINHERIT))
    except OSError:
        raise
    return handle


def get_osfhandle(fd: int, /) -> int:
    """Return fd itself, because POSIX file descriptors are their own handles."""
    if not isinstance(fd, int):
        raise TypeError("fd must be an integer")
    sys.audit("msvcrt.get_osfhandle", fd)
    os.fstat(fd)
    return fd


def kbhit() -> int:
    """Return 1 if a key or pushed-back character is waiting, otherwise 0."""
    if _byte_pushback or _wide_pushback:
        return 1
    fd = _stdin_fd()
    readable, _, _ = select.select([fd], [], [], 0)
    return int(bool(readable))


def getch() -> bytes:
    """Read one key and return one byte, without echoing it."""
    if _byte_pushback:
        return _byte_pushback.popleft()
    with _raw_input() as fd:
        return _read_key_byte(fd)


def getwch() -> str:
    """Read one key and return a Unicode character, without echoing it."""
    if _wide_pushback:
        return _wide_pushback.popleft()
    with _raw_input() as fd:
        return _read_utf8_character(fd)


def getche() -> bytes:
    """Read one byte and echo it when it is a printable character."""
    value = getch()
    _echo_byte(value)
    return value


def getwche() -> str:
    """Read one Unicode character and echo it when it is printable."""
    value = getwch()
    _echo_wide(value)
    return value


def putch(char: bytes, /) -> None:
    """Write exactly one byte to stdout without text buffering."""
    if not isinstance(char, bytes):
        raise TypeError("char must be a bytes object")
    if len(char) != 1:
        raise ValueError("char must contain exactly one byte")
    _write_all(_stdout_fd(), char)


def _coerce_wide_char(value: str | int) -> str:
    if isinstance(value, str):
        if len(value) != 1:
            raise ValueError("unicode_char must be a string of length 1")
        return value
    if isinstance(value, int):
        if not 0 <= value <= 0x10FFFF:
            raise ValueError("unicode_char must be a valid Unicode code point")
        try:
            return chr(value)
        except ValueError as exc:
            raise ValueError("unicode_char must be a valid Unicode code point") from exc
    raise TypeError("unicode_char must be a one-character str or an int")


def putwch(unicode_char: str | int, /) -> None:
    """Write one Unicode character to stdout without text buffering."""
    value = _coerce_wide_char(unicode_char)
    _write_all(_stdout_fd(), value.encode("utf-8"))


def ungetch(char: bytes, /) -> None:
    """Push one byte back so the next getch/getche call returns it."""
    if not isinstance(char, bytes):
        raise TypeError("char must be a bytes object")
    if len(char) != 1:
        raise ValueError("char must contain exactly one byte")
    _byte_pushback.appendleft(char)


def ungetwch(unicode_char: str | int, /) -> None:
    """Push one Unicode character back for the next getwch/getwche call."""
    _wide_pushback.appendleft(_coerce_wide_char(unicode_char))


def heapmin() -> None:
    """Ask the Python and, when available, glibc allocators to release memory."""
    gc.collect()
    try:
        libc = ctypes.CDLL(None)
        malloc_trim = libc.malloc_trim
    except (AttributeError, OSError):
        return None
    malloc_trim.argtypes = [ctypes.c_size_t]
    malloc_trim.restype = ctypes.c_int
    malloc_trim(0)
    return None


def GetErrorMode() -> int:
    """Unavailable: POSIX has no direct equivalent to the Win32 error mode."""
    raise NotImplementedError("GetErrorMode() has no POSIX equivalent")


def SetErrorMode(mode: int, /) -> int:
    """Unavailable: POSIX has no direct equivalent to the Win32 error mode."""
    if not isinstance(mode, int):
        raise TypeError("mode must be an integer")
    raise NotImplementedError("SetErrorMode() has no POSIX equivalent")
