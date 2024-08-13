# -*- coding: utf-8 -*-
"""
Unit test for report framework.
"""
import os
from unittest import TestCase

from qgis.core import QgsFeedback, QgsProject

from qgis.PyQt import QtCore


from qgis_gea_plugin.lib.reports.manager import ReportManager

from model_data_for_testing import get_site_metadata, get_temporal_info
from utilities_for_testing import get_qgis_app


QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()


class TestReportManager(TestCase):
    """Tests for the report manager."""

    def test_successful_submit_result(self):
        """Assert a site report job is successfully submitted."""
        rpm = ReportManager()
        site_metadata = get_site_metadata()
        temporal_info = get_temporal_info()

        QgsProject.instance().write('test.qgz')

        temp_dir = QtCore.QTemporaryDir()
        self.assertTrue(temp_dir.isValid())

        submit_result = rpm.generate_site_report(
            site_metadata,
            temp_dir.path(),
            temporal_info
        )
        self.assertTrue(submit_result.success)