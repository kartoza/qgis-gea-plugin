# -*- coding: utf-8 -*-

""" Plugin models."""

from enum import Enum, IntEnum


class IMAGERY(Enum):
    """Project imagery types"""

    HISTORICAL = "Historical"
    NICFI = "Nicfi"


class LayerNodeSearch(IntEnum):
    """Mechanism type for searching layer tree nodes."""
    EXACT_MATCH = 0
    CONTAINS = 1
