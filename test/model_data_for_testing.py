# -*- coding: utf-8 -*-
"""
Util for providing model test data.
"""
from qgis.core import QgsDateTimeRange

from qgis.PyQt import QtCore

from qgis_gea_plugin.models.base import (
    IMAGERY,
    MapTemporalInfo
)

from qgis_gea_plugin.models.report import (
    SiteMetadata,
    SiteReportContext
)


def get_temporal_info() -> MapTemporalInfo:
    """Create temporal information."""
    return MapTemporalInfo(
        IMAGERY.HISTORICAL,
        QgsDateTimeRange(
            QtCore.QDateTime.currentDateTime(),
            QtCore.QDateTime.currentDateTime()
        )
    )


def get_site_metadata() -> SiteMetadata:
    """Create site metadata."""
    return SiteMetadata(
        "Malawi",
        "0824",
        "RNJ",
        "TAMP",
        "2.87",
        "TAMP_GTI-GEA-Malawi 2_Malawi_120824",
        "120824",
        "234.51"
    )
