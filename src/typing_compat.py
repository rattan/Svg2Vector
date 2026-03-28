"""Python 3.11 미만 호환성을 위한 typing 유틸리티"""
import sys

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing import TypeVar
    Self = TypeVar('Self')

__all__ = ['Self']
