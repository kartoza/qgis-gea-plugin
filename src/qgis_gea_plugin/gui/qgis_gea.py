# -*- coding: utf-8 -*-

"""
The plugin main window class file.
"""
import os
import pathlib
import typing
from pathlib import Path

import uuid

from datetime import datetime

# QGIS imports
from qgis.PyQt import QtCore, QtGui, QtNetwork, QtWidgets
from qgis.PyQt.QtCore import QVariant
from qgis.PyQt.uic import loadUiType
from qgis.core import (
    Qgis,
    QgsApplication,
    QgsEditFormConfig,
    QgsEditorWidgetSetup,
    QgsFeedback,
    QgsField,
    QgsFillSymbol,
    QgsInterval,
    QgsLayerTreeGroup,
    QgsProject,
    QgsTask,
    QgsTemporalNavigationObject,
    QgsUnitTypes,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsWkbTypes,
)

from qgis.gui import QgsLayerTreeView, QgsMessageBar, QgsFileWidget

# Relative imports
from ..conf import Settings, settings_manager
from ..definitions.defaults import (
    ANIMATION_PAUSE_ICON,
    ANIMATION_PLAY_ICON,
    PROJECT_AREAS,
    PLUGIN_ICON,
    PROJECT_INSTANCES_GROUP_NAME,
    REPORT_SITE_BOUNDARY_STYLE,
    SITE_GROUP_NAME,
    FARMER_ID_FIELD,
    PROJECT_INSTANCE_STYLE,
    SATELLITE_IMAGERY,
)
from .attribute_form import AttributeForm
from .report_progress_dialog import ReportProgressDialog
from ..lib.reports.manager import report_manager
from ..models.base import IMAGERY, MapTemporalInfo
from ..models.report import ReportSubmitResult, SiteMetadata, ProjectMetadata

from ..utils import clean_filename, create_dir, log, tr
from ..utils import FileUtils


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

        self.project_cmb_box.addItems(PROJECT_AREAS)

        # Date when project captured started
        self.capture_date = None

        # Last captured area of the site
        self.last_computed_area = ""

        self.project_dir = None

        self.clear_btn.clicked.connect(self.cancel_drawing)
        self.import_project_btn.clicked.connect(self.import_project_instance)

        self.restore_settings()

        self.project_folder.setStorageMode(QgsFileWidget.GetDirectory)
        self.project_folder.setDialogTitle("Select project folder")
        self.project_folder.setFilter("")
        self.project_folder.fileChanged.connect(self.project_folder_changed)

        self.site_reference_le.textChanged.connect(self.save_settings)
        self.site_ref_version_le.textChanged.connect(self.save_settings)
        self.report_author_le.textChanged.connect(self.save_settings)
        self.project_inception_date.dateChanged.connect(self.save_settings)
        self.project_cmb_box.currentIndexChanged.connect(self.save_settings)

        self.report_btn.clicked.connect(self.on_generate_report)

        self.navigation_object = QgsTemporalNavigationObject(self)
        self.navigation_object.setFrameDuration(
            QgsInterval(1, QgsUnitTypes.TemporalIrregularStep)
        )

        frame_rate = settings_manager.get_value(
            Settings.ANIMATION_FRAME_RATE, default=1.0, setting_type=float
        )

        self.frame_rate_box.setValue(frame_rate) if frame_rate is not None else None

        self.loop_box.setChecked(
            settings_manager.get_value(
                Settings.ANIMATION_LOOP, default=False, setting_type=bool
            )
        )
        self.navigation_object.setLooping(self.loop_box.isChecked())
        (
            self.navigation_object.setFramesPerSecond(float(frame_rate))
            if frame_rate is not None
            else None
        )

        self.frame_rate_box.valueChanged.connect(self.frame_rate_changed)
        self.loop_box.toggled.connect(self.animation_loop_toggled)

        self.current_imagery_type = IMAGERY.HISTORICAL

        LOCAL_ROOT_DIR = Path(__file__).parent.parent.resolve()

        icon_pixmap = QtGui.QPixmap(os.path.join(LOCAL_ROOT_DIR, PLUGIN_ICON))
        log(f"Icon path: {os.path.join(LOCAL_ROOT_DIR, PLUGIN_ICON)}")
        self.icon_la.setPixmap(icon_pixmap)

        self.play_btn.setIcon(
            QtGui.QIcon(os.path.join(LOCAL_ROOT_DIR, ANIMATION_PLAY_ICON))
        )

        self.time_values = []

        self.prepare_time_slider()

        self.play_btn.clicked.connect(self.animate_layers)

        self.draw_area_btn.clicked.connect(self.start_drawing)
        self.save_area_btn.clicked.connect(self.save_area)

        self.navigation_object.updateTemporalRange.connect(self.temporal_range_changed)
        self.time_slider.valueChanged.connect(self.slider_value_changed)

        self.drawing_layer = None
        self.drawing_layer_path = None

        self.layer_subset_string = None
        self.saved_layer = None

        self.feature_count = 0

        self.iface.projectRead.connect(self.prepare_time_slider)

    def animation_loop_toggled(self, value):
        """
        Handles the toggling of the animation loop checkbox.

        :param value: Indicates whether the loop checkbox is checked or unchecked.
        :type value: bool
        """
        self.save_settings()
        self.navigation_object.setLooping(value)

    def frame_rate_changed(self, value):
        """
        Handles changes to the animation frame rate.

        :param value: The new frame rate value.
        :type value: float
        """
        self.save_settings()
        self.navigation_object.setFramesPerSecond(value)

    def save_settings(self):
        """
        Saves the current settings to the QGIS plugins
         using the settings manager.
        """

        settings_manager.set_value(
            Settings.SITE_REFERENCE, self.site_reference_le.text()
        )
        settings_manager.set_value(
            Settings.SITE_VERSION, self.site_ref_version_le.text()
        )
        settings_manager.set_value(Settings.REPORT_AUTHOR, self.report_author_le.text())

        settings_manager.set_value(
            Settings.PROJECT_INCEPTION_DATE,
            self.project_inception_date.date().toString("yyyy MM"),
        )

        settings_manager.set_value(
            Settings.REPORT_COUNTRY, self.project_cmb_box.currentText()
        )
        settings_manager.set_value(
            Settings.PROJECT_FOLDER, self.project_folder.filePath()
        )

        settings_manager.set_value(
            Settings.ANIMATION_FRAME_RATE, self.frame_rate_box.value()
        )
        settings_manager.set_value(Settings.ANIMATION_LOOP, self.loop_box.isChecked())

    def restore_settings(self):
        """
        Restores the settings from the settings manager and updates the
        corresponding GUI widgets.
        """
        self.site_reference_le.setText(
            settings_manager.get_value(Settings.SITE_REFERENCE)
        )
        self.site_ref_version_le.setText(
            settings_manager.get_value(Settings.SITE_VERSION)
        )
        self.report_author_le.setText(
            settings_manager.get_value(Settings.REPORT_AUTHOR)
        )

        stored_project_date = QtCore.QDateTime.fromString(
            settings_manager.get_value(Settings.PROJECT_INCEPTION_DATE), "yyyy MM"
        )
        self.project_inception_date.setDateTime(stored_project_date)

        index = self.project_cmb_box.findText(
            settings_manager.get_value(Settings.REPORT_COUNTRY)
        )
        self.project_cmb_box.setCurrentIndex(index)

        if settings_manager.get_value(Settings.PROJECT_FOLDER):
            self.project_folder.setFilePath(
                settings_manager.get_value(Settings.PROJECT_FOLDER)
            )
        else:
            self.project_folder.setFilePath(QgsProject.instance().homePath())
            create_dir(os.path.join(self.project_folder.filePath(), "sites"))

    def import_project_instance(self):
        self.project_instances_changed()

    def project_instances_changed(self):
        self.drawing_frame.setEnabled(False)

        # Define file filter for shapefiles only
        file_filter = "Shapefiles (*.shp);;All Files (*)"

        # Trigger a file dialog that allows selecting only one .shp file
        instance_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            None, "Select Shapefile", "", file_filter
        )

        instance_name = pathlib.Path(instance_path).stem
        layer = QgsVectorLayer(instance_path, instance_name, "ogr")

        if layer.isValid():

            style_file = FileUtils.style_file_path(PROJECT_INSTANCE_STYLE)
            layer.loadNamedStyle(style_file)
            layer.triggerRepaint()

            # Add the layer to the site boundaries
            QgsProject.instance().addMapLayer(layer, False)
            root = QgsProject.instance().layerTreeRoot()

            # Find or create the group
            group = self.find_group_by_name(PROJECT_INSTANCES_GROUP_NAME, root)

            if not group:
                main_group = None
                for child in root.children():
                    if isinstance(child, QgsLayerTreeGroup):
                        main_group = child
                        break
                main_group = main_group if main_group is not None else root

                group = main_group.insertGroup(0, PROJECT_INSTANCES_GROUP_NAME)

            # Add the layer to the group
            group.addLayer(layer)

            self.load_attribute_form(layer)

    def load_attribute_form(self, layer):

        wkb_type = layer.wkbType()

        if Qgis.QGIS_VERSION_INT < 33000:
            geometry_type = QgsWkbTypes.geometryType(wkb_type)
            layer_type = geometry_type == QgsWkbTypes.PolygonGeometry
        else:
            layer_type = QgsWkbTypes.flatType(wkb_type) in (
                QgsWkbTypes.Polygon,
                QgsWkbTypes.MultiPolygon,
            )

        if not layer_type:
            self.show_message(
                tr("Selected layer doesn't " "have a polygon geometry type.")
            )
            return

        attribute_form = AttributeForm(layer, parent=self)
        attribute_form.exec_()

    def project_folder_changed(self):
        """
        Handles changes to the project folder path.
        """
        self.dir_exists()
        create_dir(os.path.join(self.project_folder.filePath(), "sites"))
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
            self.message_bar.pushWarning("Directory not found: ", dir_path)
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
        LOCAL_ROOT_DIR = Path(__file__).parent.parent.resolve()
        if (
            self.navigation_object.animationState()
            == QgsTemporalNavigationObject.AnimationState.Idle
        ):
            self.play_btn.setIcon(
                QtGui.QIcon(os.path.join(LOCAL_ROOT_DIR, ANIMATION_PAUSE_ICON))
            )
            self.play_btn.setToolTip(tr("Pause animation"))
            self.navigation_object.playForward()
        else:
            self.navigation_object.pause()
            self.play_btn.setToolTip(tr("Click to play animation"))
            self.play_btn.setIcon(
                QtGui.QIcon(os.path.join(LOCAL_ROOT_DIR, ANIMATION_PLAY_ICON))
            )

    def temporal_range_changed(self, temporal_range):
        """
        Update temporal range and UI elements when temporal range changes.

        :param temporal_range: New temporal range.
        :type temporal_range: QgsDateTimeRange
        """
        LOCAL_ROOT_DIR = Path(__file__).parent.parent.resolve()
        self.iface.mapCanvas().setTemporalRange(temporal_range)
        if temporal_range and temporal_range.begin():
            self.temporal_range_la.setText(
                tr(
                    f"Current time range: "
                    f'<b>{temporal_range.begin().toString("yyyy-MM")}'
                )
            )
        self.time_slider.setValue(self.navigation_object.currentFrameNumber())

        # On the last animation frame
        if (
            self.navigation_object.currentFrameNumber()
            == len(self.navigation_object.availableTemporalRanges()) - 1
        ):

            self.play_btn.setToolTip(tr("Click to play animation"))
            self.play_btn.setIcon(
                QtGui.QIcon(os.path.join(LOCAL_ROOT_DIR, ANIMATION_PLAY_ICON))
            )
        else:
            self.play_btn.setToolTip(tr("Pause animation"))
            self.play_btn.setIcon(
                QtGui.QIcon(os.path.join(LOCAL_ROOT_DIR, ANIMATION_PAUSE_ICON))
            )

    def prepare_time_slider(self):
        """
        Prepare the time slider based on the current selected imagery type.

        :type closed_imagery: IMAGERY, optional
        """
        values = []
        active_layer = None

        layers = QgsProject.instance().mapLayers()
        for path, layer in layers.items():
            self.update_layer_group(layer, True)

            if layer.metadata().contains(self.current_imagery_type.value.lower()):
                values.append(layer.temporalProperties().fixedTemporalRange())
                active_layer = layer

        self.update_layer_group(active_layer, True)

        sorted_date_time_ranges = sorted(values, key=lambda x: x.begin())

        self.time_slider.setRange(0, len(sorted_date_time_ranges) - 1)
        self.navigation_object.setAvailableTemporalRanges(sorted_date_time_ranges)

        temporal_range = (
            sorted_date_time_ranges[0] if len(sorted_date_time_ranges) > 0 else None
        )

        if temporal_range and temporal_range.begin():
            self.iface.mapCanvas().setTemporalRange(temporal_range)
            self.temporal_range_la.setText(
                tr(
                    f"Current time range: "
                    f'<b>{temporal_range.begin().toString("yyyy-MM")}'
                )
            )

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

        if not self.drawing_frame.isEnabled():
            self.drawing_frame.setEnabled(True)
            return

        if (
            self.site_reference_le.text() is None
            or self.site_reference_le.text().replace(" ", "") is ""
        ):
            self.show_message(
                tr(
                    "Action Required: Please complete the attributes"
                    " form before drawing the site polygon. "
                    "This ensures all necessary details are "
                    "captured accurately."
                ),
                Qgis.Warning,
            )
            return
        if (
            self.site_ref_version_le.text() is None
            or self.site_ref_version_le.text().replace(" ", "") is ""
        ):
            self.show_message(
                tr(
                    "Action Required: Please complete the attributes"
                    " form before drawing the site polygon. "
                    "This ensures all necessary details are "
                    "captured accurately."
                ),
                Qgis.Warning,
            )
            return
        if (
            self.report_author_le.text() is None
            or self.report_author_le.text().replace(" ", "") is ""
        ):
            self.show_message(
                tr(
                    "Action Required: Please complete the attributes"
                    " form before drawing the site polygon. "
                    "This ensures all necessary details are "
                    "captured accurately."
                ),
                Qgis.Warning,
            )
            return

        layers = QgsProject.instance().mapLayersByName(SATELLITE_IMAGERY)

        if layers:
            self.update_layer_group(layers[0], True)

        # Get current project crs id
        crs_id = QgsProject.instance().crs().authid()
        folder_path = self.project_folder.filePath()
        sites_path = os.path.join(folder_path, "sites")

        self.capture_date = datetime.now().strftime("%d%m%y")

        area_name = self._get_area_name()

        unique_area_name = f"{area_name}_{str(uuid.uuid4())[:4]}"
        layer_name = clean_filename(unique_area_name)

        self.drawing_layer_path = f"{os.path.join(sites_path, layer_name)}.shp"

        # Create a new layer with multipolygon geometry
        self.drawing_layer = QgsVectorLayer(
            f"MultiPolygon?crs={crs_id}", layer_name, "memory"
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
                QgsField("area (ha)", QVariant.String),
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

        site_symbol = QgsFillSymbol.createSimple(REPORT_SITE_BOUNDARY_STYLE)
        self.drawing_layer.renderer().setSymbol(site_symbol)
        self.drawing_layer.triggerRepaint()

        # Toggle layer editing
        self.drawing_layer.startEditing()

        # Disable editing for all fields
        qgis_version_int = Qgis.QGIS_VERSION_INT

        # Check if the QGIS version is 3.32 or later (33200)
        if qgis_version_int >= 33200:
            form_config = QgsEditFormConfig()
            form_config.setSuppress(Qgis.AttributeFormSuppression.On)
            self.drawing_layer.setEditFormConfig(form_config)
        else:
            form_config = QgsEditFormConfig()
            form_config.setSuppress(QgsEditFormConfig.FeatureFormSuppress.SuppressOn)
            self.drawing_layer.setEditFormConfig(form_config)

        # Enable shape digitizing toolbar
        self.iface.shapeDigitizeToolBar().setVisible(True)

        self.iface.actionAddFeature().trigger()

    def _get_area_name(self):
        """Get the area name based on the
         current project and plugin settings.

        :returns: Returns the area name.
        :rtype: str
        """
        area_name = (
            f"{self.site_reference_le.text()}_"
            f"{QgsProject.instance().baseName()}_"
            f"{self.project_cmb_box.currentText()}_"
            f"{self.capture_date}"
        )
        return area_name

    def is_project_info_valid(self, message) -> bool:
        """Validates user input.
        :returns: Returns True if the input is valid, else False.
        :rtype: bool
        """

        selected_date_time = self.project_inception_date.dateTime()

        if selected_date_time is None:
            self.show_message(message, Qgis.Warning)
            return False
        if (
            self.site_reference_le.text() is None
            or self.site_reference_le.text().replace(" ", "") is ""
        ):
            self.show_message(message, Qgis.Warning)
            return False
        if (
            self.report_author_le.text() is None
            or self.report_author_le.text().replace(" ", "") is ""
        ):
            self.show_message(message, Qgis.Warning)
            return False
        if (
            self.site_ref_version_le.text() is None
            or self.site_ref_version_le.text().replace(" ", "") is ""
        ):
            self.show_message(message, Qgis.Warning)
            return False

        return True

    def layer_feature_added(self, id):
        """
        Handles the addition of a new feature to the
        current drawn layer.

        :param id: The ID of the newly added feature.
        :type id: int
        """
        self.feature_count += 1
        if self.feature_count > 1:
            self.drawing_layer.deleteFeature(id)
            self.show_message(
                tr(
                    "Only one feature is allowed."
                    " Additional features are not permitted."
                ),
                Qgis.Warning,
            )
        else:
            self.show_message(
                tr(
                    f"New feature has been added."
                    f" Save the project area to keep polygon."
                ),
                Qgis.Info,
            )

    def layer_editing_stopped(self):
        """
        Resets the feature count tracking that is used to
        determine if user should continue to add features to the
        site project area.
        """
        self.feature_count = 0

    def find_group_by_name(self, group_name, root_group=None):
        """
        Find a group in the layer tree by its name.

        :param group_name: The name of the group to find.
        :type group_name: str

        :param root_group: The root group to start searching from.
                            Defaults to the root of the project.
        :type root_group: QgsLayerTreeGroup

        :returns: The group if found.
        :rtype: QgsLayerTreeGroup
        """
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
        """
        Updates the editing capabilities of passed fields in a QGIS vector map layer.

        :param layer: The QGIS layer where the fields' editing properties will be updated.
        :type layer: QgsVectorLayer

        :param field_names: A list of field names to update the editing properties for.
        :type field_names: list of str

        :param enabled: A boolean flag that determines whether the fields should be editable or not.
                        If True, the fields will be editable with a text editor;
                        if False, they will be hidden.
        :type enabled: bool
        """
        setup = "TextEdit" if enabled else "Hidden"
        for field_name in field_names:
            idx = layer.fields().indexOf(field_name)
            if idx != -1:
                config = QgsEditorWidgetSetup(setup, {})
                layer.setEditorWidgetSetup(idx, config)

    def save_area(self):
        """
        Saves the project area polygon to a shapefile and updates
        the relevant attributes.

        Calculates the area of the first feature, updates attributes
        like site reference and dates, and commits the changes.
        The layer is saved as a shapefile, added to the QGIS project
        and the original drawing layer is removed.
        The saved layer is set to read-only, the main map canvas
        refreshed and the whole project is saved.
        """

        if self.drawing_layer is None:
            self.show_message(
                tr(
                    "Please add the project area layer"
                    " before saving the project area"
                ),
                Qgis.Warning,
            )
            return

        error_message = tr(
            "Action Required: Please complete the"
            " attributes form before saving the site polygon."
            " This ensures all necessary details are"
            " captured accurately."
        )

        if not self.is_project_info_valid(error_message):
            return

        selected_date_time = self.project_inception_date.dateTime()

        saved_attributes_message = tr(
            f"It looks like you are trying to add a polygon with "
            f"the same attributes as the previous polygon. "
            f"Are you sure you want to save it?"
        )

        msg_box = QtWidgets.QMessageBox()
        msg_box.setWindowTitle(tr("EPAL Plugin"))
        msg_box.setText(saved_attributes_message)
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)

        yes_button = msg_box.button(QtWidgets.QMessageBox.Yes)
        yes_button.setText("Save Anyway")

        no_button = msg_box.button(QtWidgets.QMessageBox.No)
        no_button.setText("Cancel")

        if self.check_saved_attributes():
            msg_box.exec_()

            reply = msg_box.standardButton(msg_box.clickedButton())

            if reply == QtWidgets.QMessageBox.No:
                return

        # List of fields to enable editing on
        fields_to_enable = [
            "id",
            "site_ref",
            "version",
            "author",
            "country",
            "inception_date",
            "capture_date",
            "area (ha)",
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
            first_feature.setAttribute("id", 1)
            first_feature.setAttribute("site_ref", self.site_reference_le.text())
            first_feature.setAttribute("version", self.site_ref_version_le.text())
            first_feature.setAttribute("author", self.report_author_le.text())
            first_feature.setAttribute("country", self.project_cmb_box.currentText())
            first_feature.setAttribute(
                "inception_date", selected_date_time.toString("MMyy")
            )
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
            sites_path = os.path.join(folder_path, "sites")

            layer_name = clean_filename(area_name)

            layer_path = f"{os.path.join(sites_path, layer_name)}.shp"

            error, error_message = QgsVectorFileWriter.writeAsVectorFormatV2(
                self.drawing_layer, layer_path, transform_context, options
            )
            if error == QgsVectorFileWriter.NoError:
                saved_layer = QgsVectorLayer(layer_path, layer_name, "ogr")

                if not saved_layer.isValid():
                    self.show_message(
                        tr("Problem saving the project area layer."), Qgis.Critical
                    )

                # Activate the drawing layer in order to direct add the saved layer
                # into the same group
                self.iface.setActiveLayer(self.drawing_layer)

                site_symbol = QgsFillSymbol.createSimple(REPORT_SITE_BOUNDARY_STYLE)
                saved_layer.renderer().setSymbol(site_symbol)
                QgsProject.instance().addMapLayers([saved_layer])

                QgsProject.instance().removeMapLayer(self.drawing_layer)

                self.saved_layer = saved_layer

                saved_layer.setReadOnly(True)

                self.iface.mapCanvas().refresh()
                settings_manager.set_value(Settings.LAST_SITE_LAYER_PATH, layer_path)

                QgsProject.instance().write()

                self.show_message(
                    tr(
                        f"Successfully saved the project area polygon to "
                        f"{self.drawing_layer_path}."
                    ),
                    Qgis.Info,
                )

                self.save_attributes()
            else:
                self.show_message(
                    tr(f"Error saving project area polygon layer: {error}"),
                    Qgis.Warning,
                )
                log(
                    tr(
                        f"Error saving project area polygon layer: "
                        f"{error}, {error_message}, layer path "
                        f"{layer_path}"
                    )
                )

    def save_attributes(self):
        """
        Saves the current form field values to QGIS settings.

        This method retrieves the current values from the following fields in the form:

        - Site reference
        - Site reference version
        - Report author
        - Project inception date
        - Report country

        These values are then stored (or saved) plugin settings for later retrieval.
        """

        settings_manager.set_value(
            f"{Settings.SAVED_ATTRIBUTE}_{Settings.SITE_REFERENCE}",
            self.site_reference_le.text(),
        )
        settings_manager.set_value(
            f"{Settings.SAVED_ATTRIBUTE}_{Settings.SITE_VERSION}",
            self.site_ref_version_le.text(),
        )
        settings_manager.set_value(
            f"{Settings.SAVED_ATTRIBUTE}_{Settings.REPORT_AUTHOR}",
            self.report_author_le.text(),
        )

        settings_manager.set_value(
            f"{Settings.SAVED_ATTRIBUTE}_{Settings.PROJECT_INCEPTION_DATE}",
            self.project_inception_date.date().toString("yyyy MM"),
        )

        settings_manager.set_value(
            f"{Settings.SAVED_ATTRIBUTE}_{Settings.REPORT_COUNTRY}",
            self.project_cmb_box.currentText(),
        )

    def check_saved_attributes(self):
        """
        Compares the current values in the form fields with saved attribute values
        to determine if the attributes have changed.

        This method checks if the following fields in the form match their
        corresponding saved values:

        - Site reference
        - Site reference version
        - Report author
        - Project inception date (formatted as "yyyy MM")
        - Report country

        :returns: ``True`` if the saved attributes match the current values in
                  the form, otherwise ``False``.
        :rtype: bool
        """

        saved_site_reference = settings_manager.get_value(
            f"{Settings.SAVED_ATTRIBUTE}_{Settings.SITE_REFERENCE}"
        )
        saved_site_ref_version = settings_manager.get_value(
            f"{Settings.SAVED_ATTRIBUTE}_{Settings.SITE_VERSION}"
        )
        saved_report_author = settings_manager.get_value(
            f"{Settings.SAVED_ATTRIBUTE}_{Settings.REPORT_AUTHOR}"
        )
        saved_project_inception_date = settings_manager.get_value(
            f"{Settings.SAVED_ATTRIBUTE}_{Settings.PROJECT_INCEPTION_DATE}"
        )
        saved_report_country = settings_manager.get_value(
            f"{Settings.SAVED_ATTRIBUTE}_{Settings.REPORT_COUNTRY}"
        )

        if (
            saved_site_reference == self.site_reference_le.text()
            and saved_site_ref_version == self.site_ref_version_le.text()
            and saved_report_author == self.report_author_le.text()
            and saved_project_inception_date
            == self.project_inception_date.date().toString("yyyy MM")
            and saved_report_country == self.project_cmb_box.currentText()
        ):
            return True

        return False

    def cancel_drawing(self):
        """
        Cancels the drawing process, clear the project input fields and area.
        """

        self.site_reference_le.setText(None)
        self.site_ref_version_le.setText(None)
        self.report_author_le.setText(None)
        self.project_inception_date.clear()
        self.project_cmb_box.setCurrentIndex(-1)

        try:
            if self.drawing_layer:
                self.drawing_layer.commitChanges()
                QgsProject.instance().removeMapLayer(self.drawing_layer)
                self.iface.mapCanvas().refresh()

                self.show_message(
                    tr("Cleared the project input fields and area successfully."),
                    Qgis.Info,
                )

                self.drawing_layer = None
            else:
                self.show_message(tr("Cleared the project input fields."), Qgis.Info)
        except RuntimeError as e:
            self.show_message(
                tr("Cleared the project input fields and area successfully."), Qgis.Info
            )
            log(f"Encountered an error when clearing the project drawn area.")

    def show_message(self, message, level=Qgis.Warning, duration=None):
        """Shows message on the main widget message bar.

        :param message: Text message
        :type message: str

        :param level: Message level type
        :type level: Qgis.MessageLevel

        :param duration: How to display the message
        :type duration: int
        """
        self.message_bar.clearWidgets()

        if duration:
            self.message_bar.pushMessage(message, level=level, duration=duration)
        else:
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

    def get_site_layer(self) -> typing.Optional[QgsVectorLayer]:
        """Gets the required site layer.

        Caller needs to check validity of the layer.

        :returns: Returns the latest saved layer in the
        'sites' folder.
        :rtype: QgsVectorLayer
        """

        selected_layer = self.iface.activeLayer()

        if selected_layer is not None:
            layer_node = (
                QgsProject.instance().layerTreeRoot().findLayer(selected_layer.id())
            )
            if layer_node is not None:
                parent_group = layer_node.parent()

                if parent_group is not None:
                    if parent_group.name() == SITE_GROUP_NAME:
                        settings_manager.set_value(
                            Settings.LAST_SITE_LAYER_PATH,
                            selected_layer.dataProvider().dataSourceUri(),
                        )
                    else:
                        subset_string = selected_layer.subsetString()
                        selected_layer.setSubsetString("")

                        settings_manager.set_value(
                            Settings.CURRENT_PROJECT_LAYER_PATH,
                            selected_layer.dataProvider().dataSourceUri(),
                        )
                        selected_layer.setSubsetString(subset_string)
                    return selected_layer

        sites_layer_path = settings_manager.get_value(
            Settings.LAST_SITE_LAYER_PATH, default=""
        )

        if not os.path.exists(sites_layer_path):
            print("Layer path-", sites_layer_path)
            self.show_message(
                tr("The last saved site layer path does not exist."), Qgis.Critical
            )
            log(message="The last saved site layer path does not exist.", info=False)
            return None

        layer_path = pathlib.Path(sites_layer_path)

        return QgsVectorLayer(str(layer_path), layer_path.stem, "ogr")

    def on_generate_report(self):
        """Slot raised to initiate the generation of a site report."""

        # Get last saved layer
        site_layer = self.get_site_layer()

        if site_layer is None:
            tr_msg = tr("Unable to retrieve the project area.")
            QtWidgets.QMessageBox.critical(self, self.tr("Generate Report"), tr_msg)
            log(message=tr_msg, info=False)
            return

        if not site_layer.isValid():
            tr_msg = tr("The project area is invalid.")
            QtWidgets.QMessageBox.critical(self, self.tr("Generate Report"), tr_msg)
            log(message=tr_msg, info=False)
            return

        layer_node = QgsProject.instance().layerTreeRoot().findLayer(site_layer.id())
        group = ""
        if layer_node is not None:
            parent_group = layer_node.parent()
            group = parent_group.name()

        self.current_project_layer = site_layer
        self.layer_subset_string = self.current_project_layer.subsetString()

        self.current_project_layer.setSubsetString("")

        site_features = site_layer.getFeatures()
        features = list(site_features)

        if len(features) == 0:
            tr_msg = tr("The project area is empty.")
            QtWidgets.QMessageBox.critical(self, self.tr("Generate Report"), tr_msg)
            log(message=tr_msg, info=False)
            return

        imagery_type = IMAGERY.HISTORICAL

        temporal_info = MapTemporalInfo(
            imagery_type, self.iface.mapCanvas().temporalRange()
        )

        if group == PROJECT_INSTANCES_GROUP_NAME:
            project_folder = os.path.dirname(site_layer.dataProvider().dataSourceUri())

            farmer_map = {}

            for site_feature in site_layer.getFeatures():
                farmer_id = site_feature[FARMER_ID_FIELD]
                area = float(site_feature["area (ha)"])

                if farmer_id in farmer_map:
                    farmer_map[farmer_id]["area"] += area
                else:
                    farmer_map[farmer_id] = {}
                    farmer_map[farmer_id]["area"] = area
                    farmer_map[farmer_id]["incep_date"] = site_feature["IncepDate"]
                    farmer_map[farmer_id]["author"] = site_feature["author"]
                    farmer_map[farmer_id]["project"] = site_feature["project"]

            project_instances = []

            for farmer_id, farmer_map_items in farmer_map.items():

                metadata = ProjectMetadata(
                    farmer_id=farmer_id,
                    inception_date=farmer_map_items["incep_date"],
                    author=farmer_map_items["author"],
                    project=farmer_map_items["project"],
                    total_area=f"{farmer_map_items['area']:,.2f}",
                )

                project_instances.append(metadata)

            tasks = []
            main_task = QgsTask.fromFunction(
                "Report task", self.main_report_task, on_finished=self.main_report_task
            )

            self.feedback = QgsFeedback()

            main_task.progressChanged.connect(self.report_progress_changed)
            main_task.taskTerminated.connect(self.report_terminated)
            task_counter = 0

            self.project_dir = project_folder

            for metadata in project_instances:

                submit_result = report_manager.generate_site_report(
                    metadata, project_folder, temporal_info
                )
                if not submit_result.success:
                    self.message_bar.pushWarning(
                        tr("Report Error"),
                        tr(
                            "Unable to submit request "
                            "for report. See logs for more details."
                        ),
                    )

                    return
                last_sub_task = task_counter == len(project_instances) - 1
                if last_sub_task:
                    main_task.addSubTask(
                        submit_result.task, tasks, QgsTask.ParentDependsOnSubTask
                    )
                else:
                    main_task.addSubTask(submit_result.task, tasks)
                tasks.append(submit_result.task)

                task_counter += 1

            QgsApplication.taskManager().addTask(main_task)

            result = ReportSubmitResult(True, self.feedback, None, main_task)

            progress_message = tr(f"Generating {len(project_instances)} report(s) ...")
            self.report_progress_dialog = ReportProgressDialog(
                result, project_folder, True, message=progress_message
            )
            self.report_progress_dialog.setModal(False)
            self.report_progress_dialog.show()

        elif group == SITE_GROUP_NAME:
            message = tr(
                "Report Generation Error: "
                "No site drawing has been created or saved. "
                "To generate a report, please complete the "
                "following steps: fill in the attributes, "
                "draw a site polygon, save your work, and "
                "then click to generate the report."
            )
            if not self.is_project_info_valid(message):
                return

            if site_layer.dataProvider().dataSourceUri().startswith("memory"):
                self.show_message(message, Qgis.Warning, duration=10)
                return

            # Get capture date and area
            feature = features[0]

            # If shapefile, some attribute names are truncated
            capture_date = feature["capture_da"]
            area = feature["area (ha)"]

            if self.capture_date is None:
                self.capture_date = capture_date

            metadata = SiteMetadata(
                self.project_cmb_box.currentText(),
                self.project_inception_date.dateTime().toString("MMyy"),
                self.report_author_le.text(),
                self.site_reference_le.text(),
                self.site_ref_version_le.text(),
                self._get_area_name(),
                capture_date,
                area,
            )

            self.project_dir = self.project_folder.filePath()

            submit_result = report_manager.generate_site_report(
                metadata, self.project_dir, temporal_info
            )

            if not submit_result.success:
                self.message_bar.pushWarning(
                    tr("Report Error"),
                    tr(
                        "Unable to submit request for report. "
                        "See logs for more details."
                    ),
                )
                return
            submit_result.task.taskCompleted.connect(self.site_report_finished)

            QgsApplication.taskManager().addTask(submit_result.task)

            self.report_progress_dialog = ReportProgressDialog(
                submit_result, self.project_dir
            )
            self.report_progress_dialog.setModal(False)
            self.report_progress_dialog.show()

    def report_progress_changed(self, progress):
        self.feedback.setProgress(progress)

    def report_terminated(self):
        self.current_project_layer.setSubsetString(self.layer_subset_string)

    def main_report_task(self, exception, result=None):
        self.report_progress_dialog._on_report_finished()
        self.current_project_layer.setSubsetString(self.layer_subset_string)

    def site_report_finished(self):
        self.current_project_layer.setSubsetString(self.layer_subset_string)
