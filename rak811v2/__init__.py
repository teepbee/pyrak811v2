"""Main package file.

Import classes, exceptions and enums
"""
import pkg_resources

from .exception import Rak811v2Error  # noqa: F401
from .rak811v2 import Rak811v2  # noqa: F401
from .rak811v2 import Rak811v2EventError, Rak811v2ResponseError  # noqa: F401
from .serial import Rak811v2TimeoutError  # noqa: F401

try:
    __version__ = pkg_resources.get_distribution('setuptools').version
except Exception:
    __version__ = 'unknown'
