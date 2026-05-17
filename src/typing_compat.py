import sys
from typing import TYPE_CHECKING

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing import TypeVar
    Self = TypeVar('Self')

__all__ = ['Self', 'TYPE_CHECKING']
