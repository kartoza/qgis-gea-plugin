# -*- coding: utf-8 -*-

""" Plugin models."""
import dataclasses
import dataclasses
from enum import Enum, IntEnum

from qgis.core import QgsDateTimeRange


class IMAGERY(Enum):
    """Project imagery types"""

    HISTORICAL = "Historical"
    NICFI = "Nicfi"


class LayerNodeSearch(IntEnum):
    """Mechanism type for searching layer tree nodes."""
    EXACT_MATCH = 0
    CONTAINS = 1


@dataclasses.dataclass
class MapTemporalInfo:
    """Current map temporal information."""

    image_type: IMAGERY
    date_range: QgsDateTimeRange
