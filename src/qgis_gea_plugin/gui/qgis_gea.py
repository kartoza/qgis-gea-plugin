# -*- coding: utf-8 -*-

"""
The plugin main window class file.
"""
import os
import pathlib
import typing

import uuid

from datetime import datetime, timedelta

# QGIS imports
from qgis.PyQt import QtCore, QtGui, QtNetwork, QtWidgets
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.uic import loadUiType
from qgis.core import (
    Qgis,
    QgsEditorWidgetSetup,
    QgsField,
    QgsInterval,
    QgsLayerTreeGroup,
    QgsProject,
    QgsTemporalNavigationObject,
    QgsUnitTypes,
    QgsVectorLayer,
    QgsVectorFileWriter
)
from qgis.gui import QgsLayerTreeView, QgsMessageBar

# Relative imports
from ..conf import Settings, settings_manager
from ..definitions.defaults import (
    ANIMATION_PAUSE_ICON,
    ANIMATION_PLAY_ICON,
    COUNTRY_NAMES,
    SITE_GROUP_NAME,
    PLUGIN_ICON
)
from ..gui.report_progress_dialog import ReportProgressDialog
from ..lib.reports.manager import report_manager
from ..models.base import IMAGERY, MapTemporalInfo
from ..models.report import SiteMetadata

from ..resources import *
from ..utils import animation_state_change, clean_filename, create_dir, log, tr


WidgetUi, _ = loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/main_dockwidget.ui")
)


class QgisGeaPlugin(QtWidgets.QDockWidget, WidgetUi):
    """
    Main plugin UI class for QGIS GEA Plugin.

    This class represents the main dock widget for the plugin, providing
    functionality for temporal navigation, layer management and plugin settings.

    """

    def __init__(self, iface, parent=None):
        """
        Initialize the QGIS Gea Plugin dock widget.

        :param  iface: Reference to the QGIS interface.
        :type   iface: QgsInterface

        :param parent: Parent widget. Defaults to None.
        :type   parent: QWidget

        """
        super().__init__(parent)
        self.setupUi(self)
        self.iface = iface

        self.grid_layout = QtWidgets.QGridLayout()
        self.message_bar = QgsMessageBar()
        self.prepare_message_bar()

        self.country_cmb_box.addItems(COUNTRY_NAMES)

        # Date when project captured started
        self.capture_date = None

        # Last captured area of the site
        self.last_computed_area = ""

        self.clear_btn.clicked.connect(self.cancel_drawing)

        self.restore_settings()

        self.project_folder.fileChanged.connect(self.project_folder_changed)

        self.site_reference_le.textChanged.connect(self.save_settings)
        self.site_ref_version_le.textChanged.connect(self.save_settings)
        self.report_author_le.textChanged.connect(self.save_settings)
        self.project_inception_date.dateChanged.connect(self.save_settings)
        self.country_cmb_box.currentIndexChanged.connect(self.save_settings)

        self.report_btn.clicked.connect(self.on_generate_report)

        self.navigation_object = QgsTemporalNavigationObject(self)
        self.navigation_object.setFrameDuration(
            QgsInterval(1, QgsUnitTypes.TemporalIrregularStep)
        )

        frame_rate = settings_manager.get_value(
            Settings.ANIMATION_FRAME_RATE,
            default=1.0,
            setting_type=float
        )

        self.frame_rate_box.setValue(frame_rate) \
            if frame_rate is not None else None

        self.loop_box.setChecked(
            settings_manager.get_value(
                Settings.ANIMATION_LOOP,
                default=False,
                setting_type=bool
            )
        )
        self.navigation_object.setLooping(self.loop_box.isChecked())
        self.navigation_object.setFramesPerSecond(float(frame_rate)) \
            if frame_rate is not None else None

        self.frame_rate_box.valueChanged.connect(self.frame_rate_changed)
        self.loop_box.toggled.connect(self.animation_loop_toggled)

        self.current_imagery_type = IMAGERY.HISTORICAL

        icon_pixmap = QtGui.QPixmap(PLUGIN_ICON)
        self.icon_la.setPixmap(icon_pixmap)

        self.play_btn.setIcon(QtGui.QIcon(ANIMATION_PLAY_ICON))

        self.time_values = []

        self.historical_imagery.setChecked(
            settings_manager.get_value(
                Settings.HISTORICAL_VIEW,
                setting_type=bool,
                default=True)
        )

        self.nicfi_imagery.setChecked(
            settings_manager.get_value(
                Settings.NICFI_VIEW,
                setting_type=bool,
                default=False)
        )
        self.prepare_time_slider()

        self.historical_imagery.toggled.connect(self.historical_imagery_toggled)
        self.nicfi_imagery.toggled.connect(self.nicfi_imagery_toggled)

        self.play_btn.clicked.connect(self.animate_layers)

        self.draw_area_btn.clicked.connect(self.start_drawing)
        self.save_area_btn.clicked.connect(self.save_area)

        self.navigation_object.updateTemporalRange.connect(
            self.temporal_range_changed
        )
        self.time_slider.valueChanged.connect(
            self.slider_value_changed
        )

        self.drawing_layer = None
        self.drawing_layer_path = None

        self.saved_layer = None

        self.feature_count = 0

        self.iface.projectRead.connect(self.prepare_time_slider)

    def animation_loop_toggled(self, value):
        self.save_settings()
        self.navigation_object.setLooping(value)

    def frame_rate_changed(self, value):
        self.save_settings()
        self.navigation_object.setFramesPerSecond(
            value
        )

    def save_settings(self):

        settings_manager.set_value(Settings.SITE_REFERENCE, self.site_reference_le.text())
        settings_manager.set_value(Settings.SITE_VERSION, self.site_ref_version_le.text())
        settings_manager.set_value(Settings.REPORT_AUTHOR, self.report_author_le.text())


        settings_manager.set_value(
            Settings.PROJECT_INCEPTION_DATE,
            self.project_inception_date.date().toString("yyyy MM")
        )

        settings_manager.set_value(Settings.REPORT_COUNTRY, self.country_cmb_box.currentText())
        settings_manager.set_value(Settings.PROJECT_FOLDER, self.project_folder.filePath())

        settings_manager.set_value(Settings.ANIMATION_FRAME_RATE, self.frame_rate_box.value())
        settings_manager.set_value(Settings.ANIMATION_LOOP, self.loop_box.isChecked())

    def restore_settings(self):
        self.site_reference_le.setText(settings_manager.get_value(Settings.SITE_REFERENCE))
        self.site_ref_version_le.setText(settings_manager.get_value(Settings.SITE_VERSION))
        self.report_author_le.setText(settings_manager.get_value(Settings.REPORT_AUTHOR))

        stored_project_date = QtCore.QDateTime.fromString(
            settings_manager.get_value(Settings.PROJECT_INCEPTION_DATE),
            "yyyy MM"
        )
        self.project_inception_date.setDateTime(stored_project_date)

        index = self.country_cmb_box.findText(settings_manager.get_value(Settings.REPORT_COUNTRY))
        self.country_cmb_box.setCurrentIndex(index)

        if settings_manager.get_value(Settings.PROJECT_FOLDER):
            self.project_folder.setFilePath(settings_manager.get_value(Settings.PROJECT_FOLDER))
        else:
            self.project_folder.setFilePath(QgsProject.instance().homePath())

    def project_folder_changed(self):

        self.dir_exists()
        create_dir(os.path.join(self.project_folder.filePath(), 'sites'))
        self.save_settings()

    def dir_exists(self):
        """Checks if the provided directory exists.
        A warning messages is presented if the directory does not exist.

        :returns: Whether the base directory exists
        :rtype: bool
        """

        # Clears the error messages when doing next check
        self.message_bar.clearWidgets()

        folder_found = False
        dir_path = self.project_folder.filePath()
        if not os.path.exists(dir_path):
            # File not found
            self.message_bar.pushWarning(
                "Directory not found: ", dir_path
            )
        else:
            folder_found = True

        return folder_found

    def slider_value_changed(self, value):
        """
        Slot function for handling time slider value change.

        :param value: New value of the slider.
        :type value: int
        """
        self.navigation_object.setCurrentFrameNumber(value)

    def animate_layers(self):
        """
        Toggle animation of layers based on the current animation state.
        This function is called when user press the play button.
        """
        if self.navigation_object.animationState() == \
                QgsTemporalNavigationObject.AnimationState.Idle:
            self.play_btn.setIcon(QtGui.QIcon(ANIMATION_PAUSE_ICON))
            self.play_btn.setToolTip(tr("Pause animation"))
            self.navigation_object.playForward()
        else:
            self.navigation_object.pause()
            self.play_btn.setToolTip(tr("Click to play animation"))
            self.play_btn.setIcon(QtGui.QIcon(ANIMATION_PLAY_ICON))

    def temporal_range_changed(self, temporal_range):
        """
        Update temporal range and UI elements when temporal range changes.

        :param temporal_range: New temporal range.
        :type temporal_range: QgsDateTimeRange
        """
        self.iface.mapCanvas().setTemporalRange(temporal_range)
        if temporal_range and temporal_range.begin():
            self.temporal_range_la.setText(
                tr(
                    f'Current time range: '
                    f'<b>{temporal_range.begin().toString("yyyy-MM")}'
                ))
        self.time_slider.setValue(
            self.navigation_object.currentFrameNumber()
        )

        # On the last animation frame
        if self.navigation_object.currentFrameNumber() == \
                len(self.navigation_object.availableTemporalRanges()) - 1:

            self.play_btn.setToolTip(tr("Click to play animation"))
            self.play_btn.setIcon(QtGui.QIcon(ANIMATION_PLAY_ICON))
        else:
            self.play_btn.setToolTip(tr("Pause animation"))
            self.play_btn.setIcon(QtGui.QIcon(ANIMATION_PAUSE_ICON))

    def historical_imagery_toggled(self):

        if self.historical_imagery.isChecked():
            settings_manager.set_value(Settings.HISTORICAL_VIEW, True)
            settings_manager.set_value(Settings.NICFI_VIEW, False)
            self.nicfi_imagery.setChecked(False)

            self.current_imagery_type = IMAGERY.HISTORICAL
            closed_imagery = IMAGERY.NICFI

            self.prepare_time_slider(closed_imagery)
        else:
            settings_manager.set_value(Settings.HISTORICAL_VIEW, False)

    def nicfi_imagery_toggled(self):
        if self.nicfi_imagery.isChecked():
            self.historical_imagery.setChecked(False)

            settings_manager.set_value(Settings.NICFI_VIEW, True)
            settings_manager.set_value(Settings.HISTORICAL_VIEW, False)

            self.current_imagery_type = IMAGERY.NICFI
            closed_imagery = IMAGERY.HISTORICAL
            self.prepare_time_slider(closed_imagery)
        else:
            settings_manager.set_value(Settings.NICFI_VIEW, False)


    def prepare_time_slider(self, closed_imagery=None):
        """
        Prepare the time slider based on current selected imagery type.
        """
        values = []
        set_layer = None
        active_layer = None

        layers = QgsProject.instance().mapLayers()
        for path, layer in layers.items():
            if closed_imagery is None:
                self.update_layer_group(layer, True)
                continue

            if layer.metadata().contains(
                    self.current_imagery_type.value.lower()
            ):
                values.append(
                    layer.temporalProperties().fixedTemporalRange()
                )
                active_layer = layer
            elif layer.metadata().contains(
                    closed_imagery.value.lower()
            ):
                set_layer = layer

        self.update_layer_group(set_layer)
        self.update_layer_group(active_layer, True)

        sorted_date_time_ranges = sorted(values, key=lambda x: x.begin())

        self.time_slider.setRange(0, len(sorted_date_time_ranges) - 1)
        self.navigation_object.setAvailableTemporalRanges(sorted_date_time_ranges)

        temporal_range = sorted_date_time_ranges[0] if len(sorted_date_time_ranges) > 0 else None

        if temporal_range and temporal_range.begin():
            self.iface.mapCanvas().setTemporalRange(temporal_range)
            self.temporal_range_la.setText(
                tr(
                    f'Current time range: '
                    f'<b>{temporal_range.begin().toString("yyyy-MM")}'
                ))

    def update_layer_group(self, layer, show=False):
        """
        Update visibility of provided layer parent group.

        :param layer: Layer to update.
        :type layer: QgsMapLayer

        :param show: Group visibility state. Defaults to False.
        :type show: bool
        """
        if layer is not None:
            root = QgsProject.instance().layerTreeRoot()
            layer_tree = root.findLayer(layer.id())

            if layer_tree is not None:
                group_tree = layer_tree.parent()
                if group_tree is not None:
                    group_tree.setItemVisibilityCheckedRecursive(show)

    def start_drawing(self):

        if self.site_reference_le.text() is None or self.site_reference_le.text().replace(' ', '') is '':
            self.show_message(
                tr("Please add the site reference before starting to draw the project area."),
                Qgis.Warning
            )
            return
        if self.site_ref_version_le.text() is None or self.site_ref_version_le.text().replace(' ', '') is '':
            self.show_message(
                tr("Please add the version of site reference before starting to draw the project area."),
                Qgis.Warning
            )
            return
        if self.report_author_le.text() is None or self.report_author_le.text().replace(' ', '') is '':
            self.show_message(
                tr("Please add the report generation author before starting to draw the project area."),
                Qgis.Warning
            )
            return

        layers = QgsProject.instance().mapLayersByName('Google Satellite (latest)')

        if layers:
            self.update_layer_group(layers[0], True)

        # Get current project crs id
        crs_id = QgsProject.instance().crs().authid()
        folder_path = self.project_folder.filePath()
        sites_path = os.path.join(folder_path, 'sites')

        self.capture_date = datetime.now().strftime('%d%m%y')

        area_name = self._get_area_name()

        unique_area_name = f"{area_name}_{str(uuid.uuid4())[:4]}"

        self.drawing_layer_path = f"{os.path.join(sites_path, clean_filename(unique_area_name))}.shp"

        # Create a new layer with multipolygon geometry
        self.drawing_layer = QgsVectorLayer(
            f"MultiPolygon?crs={crs_id}",
            unique_area_name,
            "memory"
        )

        # Connect to the layer's signals
        self.drawing_layer.featureAdded.connect(self.layer_feature_added)
        self.drawing_layer.editingStopped.connect(self.layer_editing_stopped)

        # Add fields to the layer
        provider = self.drawing_layer.dataProvider()
        provider.addAttributes(
            [
                QgsField("id", QVariant.Int),
                QgsField("site_ref", QVariant.String),
                QgsField("version", QVariant.String),
                QgsField("author", QVariant.String),
                QgsField("country", QVariant.String),
                QgsField("inception_date", QVariant.String),
                QgsField("capture_date", QVariant.String),
                QgsField("area (ha)", QVariant.String)
            ]
        )
        self.drawing_layer.updateFields()

        # Add the layer to the site boundaries
        QgsProject.instance().addMapLayer(self.drawing_layer, False)

        # Toggle layer editing
        self.drawing_layer.startEditing()

        root = QgsProject.instance().layerTreeRoot()

        # Find or create the group
        group = self.find_group_by_name(SITE_GROUP_NAME, root)

        if not group:
            group = root.addGroup(SITE_GROUP_NAME)

        # Add the layer to the group
        group.addLayer(self.drawing_layer)

        # Move the group to the first position in the root layer tree
        if group.parent() == root:
            root.insertChildNode(0, group.clone())
            root.removeChildNode(group)

        # Select/highlight the added layer for editing
        layer_tree_layer = root.findLayer(self.drawing_layer.id())
        if layer_tree_layer:
            layer_tree_layer.setItemVisibilityChecked(True)
            self.iface.setActiveLayer(self.drawing_layer)

        # Toggle layer editing
        self.drawing_layer.startEditing()


        # List of fields to disable editing on
        fields_to_disable = [
            "site_ref",
            "version",
            "author",
            "country",
            "inception_date",
            "capture_date",
            "area (ha)"
        ]

        # Disable editing for the specified fields
        self.update_field_editing(self.drawing_layer, fields_to_disable, False)

        # Enable shape digitizing toolbar
        self.iface.shapeDigitizeToolBar().setVisible(True)

        self.iface.actionAddFeature().trigger()

    def _get_area_name(self):
        """Get the area name.

        :returns: Returns the area name.
        :rtype: str
        """
        area_name = (f"{self.site_reference_le.text()}_"
                     f"{QgsProject.instance().baseName()}_"
                     f"{self.country_cmb_box.currentText()}_"
                     f"{self.capture_date}")
        return area_name

    def is_project_info_valid(self) -> bool:
        """Validates user input.
        :returns: Returns True if the input is valid, else False.
        :rtype: bool
        """

        selected_date_time = self.project_inception_date.dateTime()

        if selected_date_time is None:
            self.show_message(
                tr("Please add the project inception date before saving the project area"),
                Qgis.Warning
            )
            return False
        if self.site_reference_le.text() is None or self.site_reference_le.text().replace(' ', '') is '':
            self.show_message(
                tr("Please add the site reference before saving the project area"),
                Qgis.Warning
            )
            return False
        if self.report_author_le.text() is None or self.report_author_le.text().replace(' ', '') is '':
            self.show_message(
                tr("Please add the report generation author before saving the project area"),
                Qgis.Warning
            )
            return False
        if self.site_ref_version_le.text() is None or self.site_ref_version_le.text().replace(' ', '') is '':
            self.show_message(
                tr("Please add the site reference version before saving the project area"),
                Qgis.Warning
            )
            return False

        return True


    def layer_feature_added(self, id):
        self.feature_count += 1
        if self.feature_count > 1:
            self.drawing_layer.deleteFeature(id)
            self.show_message(
                tr("Only one feature is allowed."
                   " Additional features are not permitted."),
                Qgis.Warning
            )
        else:
            self.show_message(
                tr(f"New feature has been added."
                   f" Save the project area to keep polygon."),
                Qgis.Info)

    def layer_editing_stopped(self):
        self.feature_count = 0

    def find_group_by_name(self, group_name, root_group=None):
        if root_group is None:
            root_group = QgsProject.instance().layerTreeRoot()

        if root_group.name() == group_name:
            return root_group

        for child in root_group.children():
            if isinstance(child, QgsLayerTreeGroup):
                result = self.find_group_by_name(group_name, child)
                if result is not None:
                    return result

        return None

    # Disable editing for specific fields
    def update_field_editing(self, layer, field_names, enabled):
        setup = 'TextEdit' if enabled else 'Hidden'
        for field_name in field_names:
            idx = layer.fields().indexOf(field_name)
            if idx != -1:
                config = QgsEditorWidgetSetup(setup, {})
                layer.setEditorWidgetSetup(idx, config)

    def save_area(self):

        if self.drawing_layer is None:
            self.show_message(
                tr("Please add the project area layer before saving the project area"),
                Qgis.Warning
            )
            return

        if not self.is_project_info_valid():
            return

        selected_date_time = self.project_inception_date.dateTime()

        # List of fields to enable editing on
        fields_to_enable = [
            "site_ref",
            "version",
            "author",
            "country",
            "inception_date",
            "capture_date",
            "area (ha)"
        ]

        # Disable editing for the specified fields
        self.update_field_editing(self.drawing_layer, fields_to_enable, True)

        features = self.drawing_layer.getFeatures()
        first_feature = next(features, None)  # Retrieve the first feature

        if first_feature:
            feature_area = None
            geom = first_feature.geometry()
            if geom is not None and geom.isGeosValid():
                area = geom.area() / 10000
                feature_area = f"{area:,.2f}"
                self.last_computed_area = feature_area

            # Set attribute values
            first_feature.setAttribute("site_ref", self.site_reference_le.text())
            first_feature.setAttribute("version", self.site_ref_version_le.text())
            first_feature.setAttribute("author", self.report_author_le.text())
            first_feature.setAttribute("country", self.country_cmb_box.currentText())
            first_feature.setAttribute("inception_date", selected_date_time.toString("MMyy"))
            first_feature.setAttribute("capture_date", self.capture_date)
            first_feature.setAttribute("area (ha)", feature_area)

            self.drawing_layer.updateFeature(first_feature)

            self.drawing_layer.commitChanges()

            transform_context = QgsProject.instance().transformContext()
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "ESRI Shapefile"
            options.fileEncoding = "UTF-8"

            area_name = f"{self._get_area_name()}_{str(uuid.uuid4())[:4]}"

            folder_path = self.project_folder.filePath()
            sites_path = os.path.join(folder_path, 'sites')

            layer_path = f"{os.path.join(sites_path, clean_filename(area_name))}.shp"

            error, error_message = QgsVectorFileWriter.writeAsVectorFormatV2(
                self.drawing_layer, layer_path, transform_context, options
            )
            if error == QgsVectorFileWriter.NoError:
                saved_layer = QgsVectorLayer(
                    layer_path,
                    area_name,
                    "ogr"
                )

                if not saved_layer.isValid():
                    self.show_message(
                        tr("Problem saving the project area layer."),
                        Qgis.Critical
                    )

                # Activate the drawing layer in order to direct add the saved layer
                # into the same group
                self.iface.setActiveLayer(self.drawing_layer)

                QgsProject.instance().addMapLayers([saved_layer])

                QgsProject.instance().removeMapLayer(
                    self.drawing_layer
                )

                self.saved_layer = saved_layer
                saved_layer.setReadOnly(True)

                self.iface.mapCanvas().refresh()
                self.show_message(
                    tr(f"Successfully saved the project area polygon to {self.drawing_layer_path}."),
                    Qgis.Info
                )
            else:
                self.show_message(tr(f"Error project area polygon layer: {error_message}"), Qgis.Warning)


    def cancel_drawing(self):

        self.site_reference_le.setText(None)
        self.site_ref_version_le.setText(None)
        self.report_author_le.setText(None)
        self.project_inception_date.clear()
        self.country_cmb_box.setCurrentIndex(-1)

        try:
            if self.drawing_layer:
                self.drawing_layer.commitChanges()
                QgsProject.instance().removeMapLayer(self.drawing_layer)
                self.iface.mapCanvas().refresh()

                self.show_message(
                    tr("Cleared the project input fields and area successfully."),
                    Qgis.Info
                )

                self.drawing_layer = None
            else:
                self.show_message(
                    tr("Cleared the project input fields."),
                    Qgis.Info
                )
        except RuntimeError as e:
            self.show_message(
                tr("Cleared the project input fields and area successfully."),
                Qgis.Info
            )
            log(f"Encountered an error when clearing the project drawn area.")

    def show_message(self, message, level=Qgis.Warning):
        """Shows message on the main widget message bar.

        :param message: Text message
        :type message: str

        :param level: Message level type
        :type level: Qgis.MessageLevel
        """
        self.message_bar.clearWidgets()
        self.message_bar.pushMessage(message, level=level)

    def prepare_message_bar(self):
        """Initializes the widget message bar settings"""
        self.message_bar.setSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Fixed
        )
        self.grid_layout.addWidget(
            self.message_bar, 0, 0, 1, 1, alignment=QtCore.Qt.AlignTop
        )
        self.dock_widget_contents.layout().insertLayout(0, self.grid_layout)

    def get_latest_site_layer(self) -> typing.Optional[QgsVectorLayer]:
        """Gets the latest saved layer in the 'sites' folder.

        Caller needs to check validity of the layer.

        :returns: Returns the latest saved layer in the
        'sites' folder.
        :rtype: QgsVectorLayer
        """
        if self.saved_layer:
            return self.saved_layer

        sites_dir = os.path.join(self.project_folder.filePath(), 'sites')
        if not os.path.exists(sites_dir):
            log(message="Sites directory does not exist.", info=False)
            return None

        matching_paths = []
        iteration_control = 50
        counter = 0
        save_date = datetime.now()
        while True:
            if counter == iteration_control:
                break

            pattern = f"*{save_date.strftime('%d%m%y')}.shp"
            paths = list(pathlib.Path(sites_dir).glob(pattern))
            if len(paths) > 0:
                matching_paths = list(paths)
                break

            save_date = save_date - timedelta(days=1)
            counter += 1

        if len(matching_paths) == 0:
            log(message="Project area not found in sites directory.", info=False)
            return None

        layer_path = matching_paths[0]

        return QgsVectorLayer(
            str(layer_path),
            layer_path.stem,
            "ogr"
        )

    def on_generate_report(self):
        """Slot raised to initiate the generation of a site report."""
        if not self.is_project_info_valid():
            return

        # Get last saved layer
        site_layer = self.get_latest_site_layer()
        if site_layer is None:
            tr_msg = tr("Unable to retrieve the saved project area.")
            QtWidgets.QMessageBox.critical(
                self,
                self.tr("Generate Report"),
                tr_msg
            )
            log(message=tr_msg, info=False)
            return

        if not site_layer.isValid():
            tr_msg = tr("The last saved project area is invalid.")
            QtWidgets.QMessageBox.critical(
                self,
                self.tr("Generate Report"),
                tr_msg
            )
            log(message=tr_msg, info=False)
            return

        features = list(site_layer.getFeatures())
        if len(features) == 0:
            tr_msg = tr("The saved project area is empty.")
            QtWidgets.QMessageBox.critical(
                self,
                self.tr("Generate Report"),
                tr_msg
            )
            log(message=tr_msg, info=False)
            return

        # Get capture date and area
        feature = features[0]

        # If shapefile, some attribute names are truncated
        capture_date = feature["capture_da"]
        area = feature["area (ha)"]

        if self.capture_date is None:
            self.capture_date = capture_date

        metadata = SiteMetadata(
            self.country_cmb_box.currentText(),
            self.project_inception_date.dateTime().toString("MMyy"),
            self.report_author_le.text(),
            self.site_reference_le.text(),
            self.site_ref_version_le.text(),
            self._get_area_name(),
            capture_date,
            area
        )

        if not self.historical_imagery.isChecked() and not self.nicfi_imagery.isChecked():
            self.show_message(
                tr("Please select the imagery type under the Time Slider section."),
                Qgis.Warning
            )
            return

        if self.historical_imagery.isChecked():
            imagery_type = IMAGERY.HISTORICAL
        else:
            imagery_type = IMAGERY.NICFI

        temporal_info = MapTemporalInfo(
            imagery_type,
            self.iface.mapCanvas().temporalRange()
        )

        submit_result = report_manager.generate_site_report(
            metadata,
            self.project_folder.filePath(),
            temporal_info
        )
        if not submit_result.success:
            self.message_bar.pushWarning(
                tr("Site Report Error"),
                tr("Unable to submit request for report. See logs for more details.")
            )
            return

        self.report_progress_dialog = ReportProgressDialog(submit_result)
        self.report_progress_dialog.setModal(False)
        self.report_progress_dialog.show()


