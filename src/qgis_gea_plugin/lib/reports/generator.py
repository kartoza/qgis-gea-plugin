# -*- coding: utf-8 -*-
"""
Site report generator.
"""
from numbers import Number
import os
from pathlib import Path
import traceback
import typing

from qgis.core import (
    QgsCoordinateReferenceSystem,
    QgsCoordinateTransform,
    QgsFillSymbol,
    QgsLayoutExporter,
    QgsLayoutItemMap,
    QgsMapLayer,
    QgsPrintLayout,
    QgsProject,
    QgsRasterLayer,
    QgsReadWriteContext,
    QgsRectangle,
    QgsTask,
    QgsVectorLayer
)

from qgis.PyQt import QtCore, QtXml

from ...definitions.defaults import (
    ADMIN_AREAS_GROUP_NAME,
    DETAILED_ZOOM_OUT_FACTOR,
    EXCLUSION_MASK_GROUP_NAME,
    GOOGLE_LAYER_NAME,
    LANDSAT_2013_LAYER_SEGMENT,
    LANDSAT_IMAGERY_GROUP_NAME,
    OVERVIEW_ZOOM_OUT_FACTOR,
    RECENT_IMAGERY_GROUP_NAME,
    REPORT_LANDSCAPE_DESCRIPTION_SUFFIX,
    REPORT_SITE_BOUNDARY_STYLE,
    SITE_GROUP_NAME
)
from ...models.base import IMAGERY, LayerNodeSearch
from ...models.report import (
    SiteReportContext,
    ReportOutputResult
)
from ...utils import (
    clean_filename,
    log,
    tr,
)


class SiteReportReportGeneratorTask(QgsTask):
    """Class for generating the site report."""

    def __init__(self, context: SiteReportContext):
        super().__init__(
            f"{tr('Generating site report for')}: {context.metadata.area_name}"
        )
        self._context = context
        self._metadata = self._context.metadata
        self._feedback = self._context.feedback
        self._result = None
        self._layout = None
        self._project = None
        self._error_messages: typing.List[str] = []
        self._output_layout_path = ""
        self._base_layout_name = ""
        self._output_report_layout = None
        self._site_layer = None
        self._landscape_layer = None

    @property
    def context(self) -> SiteReportContext:
        """Gets the context used for generating the report.

        :returns: Returns the context object.
        :rtype: SiteReportContext
        """
        return self._context

    @property
    def result(self) -> ReportOutputResult:
        """Returns the result object which contains information
        on whether the process succeeded or failed.

        :returns: The result of the report generation process.
        :rtype: ReportResult
        """
        return self._result

    @property
    def output_layout_path(self) -> str:
        """Absolute path to a temporary file containing the
        report layout as a QPT file.

        Since the layout is created in this task object, it is
        recommended to use this layout path to reconstruct
        the layout rather getting a reference to the layout
        object since it was created in a separate thread.

        :returns: Path to the report layout template file
        or an empty string if the process was not successful.
        :rtype: str
        """
        return self._output_layout_path

    @property
    def layout(self) -> QgsPrintLayout:
        """Gets the output report layout.

        :returns: Returns the output report layout, which is
        only available after the successful generation of the
        report, when the task has finished running, else it
        returns a None object.
        :rtype: QgsPrintLayout
        """
        return self._output_report_layout

    def cancel(self):
        """Cancel the report generation task."""
        self._context.feedback.cancel()

        super().cancel()

    def run(self) -> bool:
        """Initiates the report generation process and returns
        a result indicating whether the process succeeded or
        failed.

        :returns: True if the report generation process succeeded
        or False it if failed.
        :rtype: bool
        """
        if self.isCanceled():
            return False

        try:
            if not self._generate_report():
                self._result = self._get_failed_result()
                return False

            return True
        except Exception as ex:
            # Last resort to capture general exceptions.
            exc_info = "".join(traceback.TracebackException.from_exception(ex).format())
            self._error_messages.append(exc_info)
            self._result = self._get_failed_result()
            return False

    def finished(self, result: bool):
        """If successful, add the layout to the project.

        :param result: Flag indicating if the result of the
        report generation process. True if successful,
        else False.
        :type result: bool
        """
        if len(self._result.errors) > 0:
            log(
                f"Errors occurred when generating the site "
                f"report for {self._context.metadata.area_name}."
                f" See details below: ",
                info=False,
            )
            for err in self._result.errors:
                err_msg = f"{err}\n"
                log(err_msg, info=False)

        if result:
            # Load layout
            project = QgsProject.instance()
            self._output_report_layout = _load_layout_from_file(self._output_layout_path, project)
            if self._output_report_layout is None:
                log("Could not load output report from file.", info=False)
                return

            project.layoutManager().addLayout(self._output_report_layout)
            log(
                f"Successfully generated the site report for "
                f"{self._context.metadata.area_name}."
            )

    def _check_feedback_cancelled_or_set_progress(self, value: float) -> bool:
        """Check if there is a request to cancel the process, else
        set the progress.

        :returns: Returns True if the process was cancelled else False.
        :rtype: bool
        """
        if self._feedback.isCanceled():
            tr_msg = tr("Generation of site report cancelled.")
            self._error_messages.append(tr_msg)

            return True

        self._feedback.setProgress(value)

        return False

    def _get_failed_result(self) -> ReportOutputResult:
        """Creates the report result object."""
        return ReportOutputResult(
            False,
            "",
            self._context.metadata.area_name,
            tuple(self._error_messages)
        )

    def _export_to_pdf(self) -> bool:
        """Exports the report to a PDF file in the output
        directory using the layout name as the file name.

        :returns: True if the layout was successfully exported else False.
        :rtype: bool
        """
        if self._layout is None or self._project is None:
            return False

        clean_report_name = clean_filename(self._base_layout_name)

        exporter = QgsLayoutExporter(self._layout)
        pdf_path = f"{self._context.report_dir}/{clean_report_name}.pdf"
        result = exporter.exportToPdf(pdf_path, QgsLayoutExporter.PdfExportSettings())
        if result == QgsLayoutExporter.ExportResult.Success:
            return True
        else:
            tr_msg = tr(
                "Could not export report to PDF. Check if there is PDF "
                "opened for the same project."
            )
            self._error_messages.append(f"{tr_msg} {pdf_path}.")
            return False

    def _generate_report(self) -> bool:
        """Generate site report.

        :returns: Returns True if the process succeeded, else False.
        :rtype: bool
        """
        if self._check_feedback_cancelled_or_set_progress(0):
            return False

        # Set QGIS project
        self._set_project()
        if self._project is None:
            return False

        if self._check_feedback_cancelled_or_set_progress(25):
            return False

        # Load report template
        if not self._load_template():
            return False

        # Assert template has been set
        if self._layout is None:
            return False

        if self._check_feedback_cancelled_or_set_progress(35):
            return False

        self._set_metadata_values()

        if self._check_feedback_cancelled_or_set_progress(45):
            return False

        self._set_site_layer()

        if self._check_feedback_cancelled_or_set_progress(50):
            return False

        self._set_landscape_layer()

        if self._check_feedback_cancelled_or_set_progress(55):
            return False

        self._configure_map_items_zoom_level()

        if self._check_feedback_cancelled_or_set_progress(75):
            return False

        # Save report layout in temporary file
        if not self._save_layout_to_file():
            return False

        if self._check_feedback_cancelled_or_set_progress(80):
            return False

        # Export report to PDF
        if not self._export_to_pdf():
            return False

        if self._check_feedback_cancelled_or_set_progress(100):
            return False

        # Set result
        self._result = ReportOutputResult(
            True,
            self._context.report_dir,
            self._base_layout_name,
            tuple(self._error_messages)
        )

        return True

    def _set_metadata_values(self):
        """Set the site metadata values."""
        # Inception date
        self.set_label_value("inception_date_label", self._metadata.inception_date)

        # Site reference version
        self.set_label_value("site_version_label", self._metadata.version)

        # Site reference
        self.set_label_value("site_reference_label", self._metadata.site_reference)

        # Site capture date
        self.set_label_value("capture_date_label", self._metadata.capture_date)

        # Author
        self.set_label_value("author_label", self._metadata.author)

        # Country
        self.set_label_value("country_label", self._metadata.country)

        # Area value
        self.set_label_value("site_area_label", f"{self._metadata.computed_area} ha")

    def _get_layer_from_node_name(
            self,
            node_name: str,
            search_type: LayerNodeSearch = LayerNodeSearch.EXACT_MATCH,
            group_name: str = ""
    ) -> typing.Optional[QgsMapLayer]:
        """Gets the map layer from the corresponding name of the layer
        tree item.

        :param node_name: Name of the layer tree item.
        :type node_name: str

        :param search_type: Whether to perform an exact matching
        string or whether it contains a sub-string specified in the
        `node_name`. Default is EXACT_MATCH
        :type search_type: LayerNodeSearch

        :param group_name: Whether to limit the search to layers in
        the layer group with the given name.
        :type group_name: str

        :returns: Returns the first corresponding map layer or None if
        not found.
        :rtype: QgsMapLayer
        """
        root_tree = self._project.layerTreeRoot()

        matching_node = None
        for node in root_tree.findLayers():
            if group_name:
                if node.parent() and node.parent().name() == group_name:
                    for child in node.parent().children():
                        if search_type == LayerNodeSearch.EXACT_MATCH \
                                and child.name() == node_name:
                            matching_node = child
                            break
                        elif search_type == LayerNodeSearch.CONTAINS \
                                and node_name in child.name():
                            matching_node = child
                            break
            else:
                if search_type == LayerNodeSearch.EXACT_MATCH \
                        and node.name() == node_name:
                    matching_node = node
                    break
                elif search_type == LayerNodeSearch.CONTAINS \
                        and node_name in node.name():
                    matching_node = node
                    break

        if matching_node is None:
            tr_msg = tr("layer node not found.")
            self._error_messages.append(f"{node_name} {tr_msg}")
            return None

        return matching_node.layer()

    def _get_map_item_by_id(self, map_id: str) -> typing.Optional[QgsLayoutItemMap]:
        """Gets a map item corresponding to the given identifier.

        :param map_id: Map item identifier.
        :type map_id: str

        :returns: Returns the first map item matching the
        given ID else None if not found.
        :rtype: QgsLayoutItemMap
        """
        map_item = self._layout.itemById(map_id)
        if map_item is None:
            tr_msg = tr("not found in report template.")
            self._error_messages.append(f"'{map_id}' {tr_msg}")
            return None

        return map_item

    def _set_site_layer(self):
        """Fetch the site boundary layer saved in the project's
        'sites' boundary folder.
        """
        site_path = f"{self._context.project_dir}/sites/" \
                    f"{clean_filename(self._metadata.area_name)}.shp"

        if not os.access(site_path, os.R_OK):
            tr_msg = tr(
                "Current user does not have permission to read the "
                "site boundary shapefile"
            )
            self._error_messages.append(tr_msg)
            return

        p = Path(site_path)
        if not p.exists():
            tr_msg = tr("Site boundary shapefile does not exist")
            self._error_messages.append(f"{tr_msg} {site_path}")
            return

        site_layer = QgsVectorLayer(site_path, "Site Boundary", "ogr")
        if not site_layer.isValid():
            tr_msg = tr("Site boundary shapefile is invalid")
            self._error_messages.append(tr_msg)
            return

        # We need to update the data source of the site layer in the
        # project since it was only saved as a memory layer.
        project_site_layer = self._get_layer_from_node_name(
            self._metadata.area_name,
            LayerNodeSearch.EXACT_MATCH,
            SITE_GROUP_NAME
        )
        if project_site_layer is None:
            tr_msg = tr("Reference site layer not found in the project.")
            self._error_messages.append(tr_msg)
            return

        project_site_layer.setDataSource(
            site_layer.source(),
            project_site_layer.name(),
            site_layer.providerType(),
            site_layer.dataProvider().ProviderOptions()
        )

        site_symbol = QgsFillSymbol.createSimple(REPORT_SITE_BOUNDARY_STYLE)
        project_site_layer.renderer().setSymbol(site_symbol)
        project_site_layer.triggerRepaint()

        self._site_layer = project_site_layer

    def _set_landscape_layer(self):
        """Set the landscape layer i.e. Nicfi or Landsat depending on the
        information in the TemporalInfo object.
        """
        # For now, we are only interested in Landsat 2013
        # hence the commented code.
        # if self._context.temporal_info.image_type == IMAGERY.NICFI:
        #     group_name = RECENT_IMAGERY_GROUP_NAME
        # elif self._context.temporal_info.image_type == IMAGERY.HISTORICAL:
        #     group_name = LANDSAT_IMAGERY_GROUP_NAME
        # else:
        #     group_name = ""
        #
        # if not group_name:
        #     tr_msg = tr("Landscape group name could not be determined")
        #     self._error_messages.append(tr_msg)
        #     return
        #
        # layers = self._get_layers_in_group(group_name)
        # if len(layers) == 0:
        #     tr_msg = tr("No layers in landscape group")
        #     self._error_messages.append(f"{tr_msg}: {group_name}")
        #     return
        #
        # # Search corresponding layers
        # for layer in layers:
        #     temporal_properties = layer.temporalProperties()
        #     if temporal_properties is None:
        #         continue
        #
        #     if not temporal_properties.isActive():
        #         continue
        #
        #     if not isinstance(layer, QgsRasterLayer):
        #         continue
        #
        #     temporal_range = temporal_properties.fixedTemporalRange()
        #     if temporal_range == self._context.temporal_info.date_range:
        #         self._landscape_layer = layer
        #
        #         break

        landsat_2013_layer = self._get_layer_from_node_name(
            LANDSAT_2013_LAYER_SEGMENT,
            LayerNodeSearch.CONTAINS,
            LANDSAT_IMAGERY_GROUP_NAME
        )
        if landsat_2013_layer is not None:
            self._landscape_layer = landsat_2013_layer

        if self._landscape_layer is None:
            tr_msg = tr("Landscape layer not found")
            self._error_messages.append(
                f"{tr_msg} under {LANDSAT_IMAGERY_GROUP_NAME}"
            )

    def _configure_map_items_zoom_level(self):
        """Set layers and zoom levels of map items."""
        if self._site_layer is None:
            tr_msg = tr("Site layer not found or shapefile is invalid")
            self._error_messages.append(tr_msg)
            return

        # Site maps
        detailed_extent = self._configure_site_maps()

        # Get mask layers
        mask_layers = self._get_layers_in_group(EXCLUSION_MASK_GROUP_NAME)

        # Landscape maps
        self._configure_landscape_maps(detailed_extent, mask_layers)

        # Current imagery
        self._configure_current_maps(detailed_extent, mask_layers)

    def _configure_landscape_maps(
            self,
            detailed_extent: QgsRectangle,
            mask_layers: typing.List[QgsMapLayer]
    ):
        """Set the zoom level and layers for the landscape exclusion
        and inclusion maps.

        :param detailed_extent: Extent to use for the landscape exclusion
        and inclusion maps.
        :type detailed_extent: QgsRectangle

        :param mask_layers: Exclusion mask layers
        :type mask_layers: list
        """
        if self._landscape_layer is None:
            tr_msg = tr(
                "Landscape layer is missing, landscape maps will not "
                "be rendered correctly."
            )
            self._error_messages.append(tr_msg)

        # landscape layer with mask map
        historic_mask_map = self._get_map_item_by_id("historic_mask_map")
        if historic_mask_map and detailed_extent:
            # Transform extent
            landscape_imagery_extent = self._transform_extent(
                detailed_extent,
                self._site_layer.crs(),
                historic_mask_map.crs()
            )

            if landscape_imagery_extent.isNull():
                tr_msg = tr(
                    "Invalid extent for setting in the current imagery "
                    "with mask map"
                )
                self._error_messages.append(tr_msg)
            else:
                landscape_mask_layers = [self._site_layer]
                landscape_mask_layers.extend(mask_layers)
                if self._landscape_layer is not None:
                    landscape_mask_layers.append(self._landscape_layer)
                historic_mask_map.setFollowVisibilityPreset(False)
                historic_mask_map.setFollowVisibilityPresetName("")
                historic_mask_map.setLayers(landscape_mask_layers)
                historic_mask_map.zoomToExtent(landscape_imagery_extent)
                historic_mask_map.refresh()

        # Landscape with no-mask map
        landscape_no_mask_map = self._get_map_item_by_id("historic_no_mask_map")
        if landscape_no_mask_map and detailed_extent:
            # Transform extent
            landscape_no_mask_extent = self._transform_extent(
                detailed_extent,
                self._site_layer.crs(),
                landscape_no_mask_map.crs()
            )

            if landscape_no_mask_extent.isNull():
                tr_msg = tr(
                    "Invalid extent for setting in the landscape imagery "
                    "with no-mask map"
                )
                self._error_messages.append(tr_msg)
            else:
                landscape_no_mask_layers = [self._site_layer]
                if self._landscape_layer is not None:
                    landscape_no_mask_layers.append(self._landscape_layer)

                landscape_no_mask_map.setFollowVisibilityPreset(False)
                landscape_no_mask_map.setFollowVisibilityPresetName("")
                landscape_no_mask_map.setLayers(landscape_no_mask_layers)
                landscape_no_mask_map.zoomToExtent(landscape_no_mask_extent)
                landscape_no_mask_map.refresh()

    def _configure_current_maps(
            self,
            detailed_extent: QgsRectangle,
            mask_layers: typing.List[QgsMapLayer]
    ):
        """Set the zoom level and layers for the current imagery maps.

        :param detailed_extent: Extent to use for the current maps.
        :type detailed_extent: QgsRectangle

        :param mask_layers: Exclusion mask layers
        :type mask_layers: list
        """
        google_layer = self._get_layer_from_node_name(
            GOOGLE_LAYER_NAME,
            LayerNodeSearch.EXACT_MATCH
        )

        # Current imagery with mask map
        current_mask_map = self._get_map_item_by_id("current_mask_map")
        if current_mask_map and detailed_extent:
            # Transform extent
            current_imagery_extent = self._transform_extent(
                detailed_extent,
                self._site_layer.crs(),
                current_mask_map.crs()
            )

            if current_imagery_extent.isNull():
                tr_msg = tr(
                    "Invalid extent for setting in the current imagery "
                    "with mask map."
                )
                self._error_messages.append(tr_msg)
            else:
                current_mask_layers = [self._site_layer]
                current_mask_layers.extend(mask_layers)
                current_mask_layers.append(google_layer)
                current_mask_map.setFollowVisibilityPreset(False)
                current_mask_map.setFollowVisibilityPresetName("")
                current_mask_map.setLayers(current_mask_layers)
                current_mask_map.zoomToExtent(current_imagery_extent)
                current_mask_map.refresh()

        # Current imagery with no-mask map
        current_no_mask_map = self._get_map_item_by_id("current_no_mask_map")
        if current_no_mask_map and detailed_extent:
            # Transform extent
            current_no_mask_imagery_extent = self._transform_extent(
                detailed_extent,
                self._site_layer.crs(),
                current_no_mask_map.crs()
            )

            if current_no_mask_imagery_extent.isNull():
                tr_msg = tr(
                    "Invalid extent for setting in the current imagery "
                    "with no-mask map."
                )
                self._error_messages.append(tr_msg)
            else:
                current_no_mask_layers = [self._site_layer, google_layer]
                current_no_mask_map.setFollowVisibilityPreset(False)
                current_no_mask_map.setFollowVisibilityPresetName("")
                current_no_mask_map.setLayers(current_no_mask_layers)
                current_no_mask_map.zoomToExtent(current_no_mask_imagery_extent)
                current_no_mask_map.refresh()

    def _configure_site_maps(self) -> QgsRectangle:
        """Set the zoom level and layers for the overview and detailed maps.

        :returns: Returns the extent of the detailed map.
        :rtype: QgsRectangle
        """
        site_extent = self._site_layer.extent()

        google_layer = self._get_layer_from_node_name(
            GOOGLE_LAYER_NAME,
            LayerNodeSearch.EXACT_MATCH
        )

        map_item_layers = [self._site_layer]

        ref_admin_layer = None
        admin_layers = self._get_layers_in_group(ADMIN_AREAS_GROUP_NAME)
        if len(admin_layers) > 0:
            ref_admin_layer = admin_layers[0]
            map_item_layers.extend(admin_layers)

        if google_layer:
            # We want the Google layer as the last item
            map_item_layers.extend([google_layer])

        # Overview map
        overview_map = self._get_map_item_by_id("site_location_overview_map")
        if overview_map:
            # We use the admin layer to control the overview extent i.e.
            # ensure we do not zoom out beyond the national extent.
            admin_extent = None
            if ref_admin_layer:
                admin_extent = self._transform_extent(
                    ref_admin_layer.extent(),
                    ref_admin_layer.crs(),
                    overview_map.crs()
                )

            # Transform extent
            overview_extent = self._transform_extent(
                site_extent,
                self._site_layer.crs(),
                overview_map.crs()
            )
            if overview_extent.isNull():
                tr_msg = tr("Invalid extent for setting in the overview map.")
                self._error_messages.append(tr_msg)
            else:
                # Zoom out by factor
                overview_extent.scale(OVERVIEW_ZOOM_OUT_FACTOR)

                if admin_extent:
                    if admin_extent.contains(overview_extent):
                        overview_map.zoomToExtent(overview_extent)
                    else:
                        overview_map.zoomToExtent(admin_extent)
                else:
                    overview_map.zoomToExtent(overview_extent)

                overview_map.setFollowVisibilityPreset(False)
                overview_map.setFollowVisibilityPresetName("")
                overview_map.setLayers(map_item_layers)
                overview_map.refresh()

        # Detailed site map
        detailed_map = self._get_map_item_by_id("site_location_detailed_map")
        detailed_extent = None
        if detailed_map:
            # Transform extent
            detailed_extent = self._transform_extent(
                site_extent,
                self._site_layer.crs(),
                detailed_map.crs()
            )

            if detailed_extent.isNull():
                tr_msg = tr("Invalid extent for setting in the detailed map.")
                self._error_messages.append(tr_msg)
            else:
                detailed_map.setFollowVisibilityPreset(False)
                detailed_map.setFollowVisibilityPresetName("")
                detailed_map.setLayers(map_item_layers)

                # Zoom out by factor
                detailed_extent.scale(DETAILED_ZOOM_OUT_FACTOR)
                detailed_map.zoomToExtent(detailed_extent)
                detailed_map.refresh()

        return detailed_extent

    def _get_layers_in_theme(self, theme_name: str) -> typing.List[QgsMapLayer]:
        """Returns the visible map layers in the given theme.

        :param theme_name: Name of the theme containing map layers.
        :type theme_name: str

        :returns: Returns the list of visible map layers or an empty list.
        :rtype: list
        """
        theme_collection = self._project.mapThemeCollection()
        theme = theme_collection.mapThemeState(theme_name)
        if theme is None:
            return []

        return [record.layer() for record in theme.layerRecords()]

    def _get_layers_in_group(self, group_name: str) -> typing.List[QgsMapLayer]:
        """Gets all the map layers in a group node.

        :param group_name: Group name to retrieve the layers.
        :type group_name: str

        :returns: Returns all the layers in the given group or an
        empty list if the group was not found or does not contain
        any layers.
        :rtype: list
        """
        root_tree = self._project.layerTreeRoot()

        search_group = root_tree.findGroup(group_name)
        if search_group is None:
            return []

        return [tree_layer.layer() for tree_layer in search_group.findLayers()]

    def _transform_extent(
            self,
            extent: QgsRectangle,
            source_crs: QgsCoordinateReferenceSystem,
            target_crs: QgsCoordinateReferenceSystem
    ) -> QgsRectangle:
        """Transform the extent from the given source CRS to the target CRS.

        :param extent: Extent to be reprojected.
        :type extent: QgsRectangle

        :param source_crs: CRS of the input extent.
        :type source_crs: QgsCoordinateReferenceSystem

        :param target_crs: Target CRS of the output extent.
        :type target_crs: QgsCoordinateReferenceSystem

        :returns: Returns the reprojected extent.
        :rtype: QgsRectangle
        """
        if source_crs == target_crs:
            return extent

        if source_crs is None or target_crs is None:
            return extent

        try:
            coordinate_xform = QgsCoordinateTransform(
                source_crs,
                target_crs,
                self._project
            )
            return coordinate_xform.transformBoundingBox(extent)
        except Exception as e:
            tr_msg = tr("using the default input extent")
            self._error_messages.append(f"{e}, {tr_msg}")

        return extent

    def _set_project(self):
        """Deserialize the project from the report context."""
        if not self._context.qgs_project_path:
            tr_msg = tr("Project file not specified")
            self._error_messages.append(tr_msg)
            return

        else:
            if not os.access(self._context.qgs_project_path, os.R_OK):
                tr_msg = tr(
                    "Current user does not have permission to read the project file"
                )
                self._error_messages.append(tr_msg)
                return

            p = Path(self._context.qgs_project_path)
            if not p.exists():
                tr_msg = tr("Project file does not exist")
                self._error_messages.append(f"{tr_msg} {self._context.qgs_project_path}")
                return

        project = QgsProject()
        result = project.read(self._context.qgs_project_path)
        if not result:
            tr_msg = tr("Unable to read the project file")
            self._error_messages.append(f"{tr_msg} {self._context.qgs_project_path}")
            return

        if project.error():
            tr_msg = tr("Error in project file")
            self._error_messages.append(f"{tr_msg}: {project.error()}")
            return

        self._project = project

    def _load_template(self) -> bool:
        """Loads the template defined in the report context.

        :returns: True if the template was successfully loaded,
        else False.
        :rtype: bool
        """
        if self._project is None:
            tr_msg = tr("Project not set.")
            self._error_messages.append(tr_msg)
            return False

        report_layout = _load_layout_from_file(
            self._context.template_path, self._project, self._error_messages
        )
        if report_layout is None:
            return False

        self._layout = report_layout

        # Check if there is another layout in the project
        # with the same name.
        base_report_name = self._context.metadata.area_name
        layout = self._project.layoutManager().layoutByName(base_report_name)
        if layout:
            counter = 2
            while True:
                base_report_name = f"{base_report_name}_{counter!s}"
                layout = self._project.layoutManager().layoutByName(base_report_name)
                if layout is None:
                    break
                counter += 1

        self._base_layout_name = base_report_name

        self._layout.setName(self._base_layout_name)

        return True

    def _save_layout_to_file(self) -> bool:
        """Serialize the updated report layout to a temporary file."""
        temp_layout_file = QtCore.QTemporaryFile()
        if not temp_layout_file.open():
            tr_msg = tr("Could not open temporary file to write the report.")
            self._error_messages.append(tr_msg)
            return False

        file_name = temp_layout_file.fileName()
        self._output_layout_path = f"{file_name}.qpt"

        result = self._layout.saveAsTemplate(
            self._output_layout_path, QgsReadWriteContext()
        )
        if not result:
            tr_msg = tr("Could not save the report template.")
            self._error_messages.append(tr_msg)
            return False

        return True

    def set_label_value(self, label_id: str, value: str):
        """Sets the value of the label with the given ID.

        If the label is not found in the layout, a corresponding
        error message will be logged.

        :param label_id: Label identifier in the layout.
        :type label_id: str

        :param value: Value to be set in the label.
        :type value: str
        """
        if self._layout is None:
            tr_msg = tr("Unable to set label value, layout not found.")
            self._error_messages.append(tr_msg)
            return

        label_item = self._layout.itemById(label_id)
        if label_item is None:
            tr_msg = tr("not found in report template.")
            self._error_messages.append(f"'{label_id}' {tr_msg}")
            return

        label_item.setText(value)


def _load_layout_from_file(
    template_path: str, project: QgsProject, error_messages: list = None
) -> typing.Union[QgsPrintLayout, None]:
    """Util for loading layout templates from a file. It supports
    an optional argument for list to write error messages.
    """
    p = Path(template_path)
    if not p.exists():
        if error_messages:
            tr_msg = tr("Template file does not exist")
            error_messages.append(f"{tr_msg} {template_path}.")
        return None

    template_file = QtCore.QFile(template_path)
    doc = QtXml.QDomDocument()
    doc_status = True
    try:
        if not template_file.open(QtCore.QIODevice.ReadOnly):
            if error_messages:
                tr_msg = tr("Unable to read template file")
                error_messages.append(f"{tr_msg} {template_path}")
            doc_status = False

        if doc_status:
            if not doc.setContent(template_file):
                if error_messages:
                    tr_msg = tr("Failed to parse template file contents")
                    error_messages.append(f"{tr_msg} {template_path}")
                doc_status = False
    finally:
        template_file.close()

    if not doc_status:
        return None

    layout = QgsPrintLayout(project)
    _, load_status = layout.loadFromTemplate(doc, QgsReadWriteContext())
    if not load_status:
        if error_messages:
            tr_msg = tr("Could not load template from")
            error_messages.append(f"{tr_msg} {template_path}")
        return None

    return layout
