import os

import unittest
from qgis.PyQt.QtCore import Qt, QDateTime
from qgis.PyQt.QtTest import QTest

from qgis.core import (
    QgsDateTimeRange,
    QgsInterval,
    QgsProject,
    QgsTemporalNavigationObject,
    QgsUnitTypes,
    QgsVectorFileWriter,
)
from qgis.gui import QgsMapCanvas

from qgis.utils import plugins, iface

from qgis_gea_plugin.gui.qgis_gea import QgisGeaPlugin

from qgis_gea_plugin.models.base import IMAGERY

from utilities_for_testing import get_qgis_app

QGIS_APP, CANVAS, IFACE, PARENT = get_qgis_app()


class TestQgisGeaPlugin(unittest.TestCase):
    """
    Unit tests for QgisGeaPlugin class.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up the QGIS GEA Plugin dock instance for testing.
        """
        cls.plugin_dock = QgisGeaPlugin(iface)
        iface.mainWindow().addDockWidget(Qt.RightDockWidgetArea, cls.plugin_dock)

    def test_slider_value_changed(self):
        """
        Test slider value change functionality.
        """

        ranges = [
            QgsDateTimeRange(
                QDateTime.fromString("2020-01-01T00:00:00", Qt.ISODate),
                QDateTime.fromString("2020-01-01T00:00:00", Qt.ISODate),
            ),
            QgsDateTimeRange(
                QDateTime.fromString("2020-01-01T00:00:00", Qt.ISODate),
                QDateTime.fromString("2020-01-01T00:00:00", Qt.ISODate),
            ),
        ]
        self.plugin_dock.navigation_object.setFrameDuration(
            QgsInterval(1, QgsUnitTypes.TemporalIrregularStep)
        )
        self.plugin_dock.navigation_object.setAvailableTemporalRanges(ranges)

        self.assertEqual(self.plugin_dock.navigation_object.currentFrameNumber(), 0)

        # Simulate setting slider value
        slider_value = 1
        self.plugin_dock.slider_value_changed(slider_value)

        # Check if navigation object's current frame number is set correctly
        self.assertEqual(
            self.plugin_dock.navigation_object.currentFrameNumber(), slider_value
        )

    def test_animate_layers(self):
        """
        Test the main animation function.
        """
        self.assertEqual(
            self.plugin_dock.navigation_object.animationState(),
            QgsTemporalNavigationObject.AnimationState.Idle,
        )
        # Simulate clicking on the play button
        QTest.mouseClick(self.plugin_dock.play_btn, Qt.LeftButton)

        self.assertEqual(
            self.plugin_dock.navigation_object.animationState(),
            QgsTemporalNavigationObject.AnimationState.Forward,
        )

        # Simulate clicking on the play button again
        QTest.mouseClick(self.plugin_dock.play_btn, Qt.LeftButton)

        self.assertEqual(
            self.plugin_dock.navigation_object.animationState(),
            QgsTemporalNavigationObject.AnimationState.Idle,
        )

    def test_prepare_time_slider(self):
        """
        Test preparation of time slider UI components.
        """
        self.plugin_dock.historical_imagery.setChecked(True)
        self.plugin_dock.nicfi_imagery.setChecked(False)

        self.plugin_dock.prepare_time_slider()

        # Check if the current imagery type is set correctly
        self.assertEqual(self.plugin_dock.current_imagery_type, IMAGERY.HISTORICAL)

        self.plugin_dock.nicfi_imagery.setChecked(True)
        self.plugin_dock.historical_imagery.setChecked(False)

        self.plugin_dock.prepare_time_slider()

        # Check if the current imagery type is set correctly
        self.assertEqual(self.plugin_dock.current_imagery_type, IMAGERY.NICFI)

    # def test_get_site_layer(self):
    #     """
    #     Test the retrieval of the site layer from the project.
    #     """
    #     # Assuming you have a valid site layer setup for testing
    #     layer = iface.addVectorLayer("Point?crs=EPSG:4326", "test_layer", "memory")
    #
    #     error = QgsVectorFileWriter.writeAsVectorFormat(
    #         layer,
    #         os.path.join(QgsProject.instance().homePath(), 'test.shp'),
    #         "UTF-8",
    #         driverName="ESRI Shapefile"
    #     )
    #
    #     root = QgsProject.instance().layerTreeRoot()
    #     new_group = root.addGroup("Proposed Site Boundaries")
    #     new_group.addLayer(layer)
    #
    #     passed_layer = iface.addVectorLayer(
    #         os.path.join(QgsProject.instance().homePath(), 'test.shp'),
    #         'test_layer',
    #         'ogr')
    #
    #     iface.setActiveLayer(passed_layer)
    #
    #     site_layer = self.plugin_dock.get_site_layer()
    #
    #     self.assertIsNotNone(site_layer)
    #     self.assertEqual(site_layer.name(), "test_layer")

    @classmethod
    def tearDownClass(cls):
        """
        Clean up after tests.
        """
        # Remove the dock widget after tests
        iface.mainWindow().removeDockWidget(cls.plugin_dock)


if __name__ == "__main__":
    unittest.main()
