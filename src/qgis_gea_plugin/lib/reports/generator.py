# -*- coding: utf-8 -*-
"""
Site report generator.
"""
from numbers import Number
import os
from pathlib import Path
import traceback
import typing
import re

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
    QgsVectorLayer,
    QgsProject,
    QgsLayerTreeGroup,
    QgsLayerTreeLayer,
)

from qgis.PyQt import QtCore, QtXml

from ...conf import settings_manager, Settings
from ...definitions.defaults import (
    ADMIN_AREAS_GROUP_NAME,
    DETAILED_ZOOM_OUT_FACTOR,
    EXCLUSION_MASK_GROUP_NAME,
    GOOGLE_LAYER_NAME,
    LANDSAT_2013_LAYER_SEGMENT,
    LANDSAT_2015_LAYER_SEGMENT,
    LANDSAT_IMAGERY_GROUP_NAME,
    OVERVIEW_ZOOM_OUT_FACTOR,
    REPORT_SITE_BOUNDARY_STYLE,
    PROJECT_INSTANCE_STYLE,
)
from ...models.base import LayerNodeSearch
from qgis.PyQt.QtCore import QDate
from ...models.report import (
    SiteReportContext,
    ReportOutputResult,
    SiteMetadata,
    ProjectMetadata,
)
from ...utils import (
    clean_filename,
    FileUtils,
    log,
    tr,
)


class SiteReportReportGeneratorTask(QgsTask):
    """Class for generating the site report."""

    def __init__(self, context: SiteReportContext):
        super().__init__()
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
        self._2015_layer = None
        self.report_name = (
            context.metadata.area_name
            if isinstance(context.metadata, SiteMetadata)
            else f"Farmer ID {context.metadata.farmer_id}"
        )

        self.setDescription(f"{tr('Generating report for')}: {self.report_name}")


class SiteReportReportGeneratorTask(QgsTask):
    """Class for generating the site report."""

    def __init__(self, context: SiteReportContext):
        super().__init__()
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
        self._2015_layer = None
        self.report_name = (
            context.metadata.area_name
            if isinstance(context.metadata, SiteMetadata)
            else f"Farmer ID {context.metadata.farmer_id}"
        )

        self.setDescription(f"{tr('Generating report for')}: {self.report_name}")

        # Log class properties and their types
        log_verbose = False
        if log_verbose:
            log("SiteReportReportGeneratorTask initialized with:", to_file=True)
            log(
                f"-----------------------------------------------------------",
                to_file=True,
            )
            log(f"  _context: {type(self._context).__name__}", to_file=True)
            log(f"  _metadata: {type(self._metadata).__name__}", to_file=True)
            log(f"  _feedback: {type(self._feedback).__name__}", to_file=True)
            log(f"  _result: {type(self._result).__name__}", to_file=True)
            log(f"  _layout: {type(self._layout).__name__}", to_file=True)
            log(f"  _project: {type(self._project).__name__}", to_file=True)
            log(
                f"  _error_messages: {type(self._error_messages).__name__}",
                to_file=True,
            )
            log(
                f"  _output_layout_path: {type(self._output_layout_path).__name__}",
                to_file=True,
            )
            log(
                f"  _base_layout_name: {type(self._base_layout_name).__name__}",
                to_file=True,
            )
            log(
                f"  _output_report_layout: {type(self._output_report_layout).__name__}",
                to_file=True,
            )
            log(f"  _site_layer: {type(self._site_layer).__name__}", to_file=True)
            log(
                f"  _landscape_layer: {type(self._landscape_layer).__name__}",
                to_file=True,
            )
            log(f"  _2015_layer: {type(self._2015_layer).__name__}", to_file=True)
            log(f"  report_name: {type(self.report_name).__name__}", to_file=True)
            log(
                f"-----------------------------------------------------------",
                to_file=True,
            )

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
        else:
            return True

    def finished(self, result: bool):
        """If successful, add the layout to the project.

        :param result: Flag indicating if the result of the
        report generation process. True if successful,
        else False.
        :type result: bool
        """
        if self.isCanceled():
            return
        try:
            if not self._generate_report():
                self._result = self._get_failed_result()

        except Exception as ex:
            # Last resort to capture general exceptions.
            exc_info = "".join(traceback.TracebackException.from_exception(ex).format())
            self._error_messages.append(exc_info)
            self._result = self._get_failed_result()
            return

        if self._result and len(self._result.errors) > 0:
            log(
                f"Errors occurred when generating the "
                f"report for {self.report_name}."
                f" See details below: ",
                info=False,
            )
            for err in self._result.errors:
                err_msg = f"{err}\n"
                log(err_msg, info=False)
            return
        # Load layout
        project = QgsProject.instance()
        self._output_report_layout = _load_layout_from_file(
            self._output_layout_path, project
        )
        if self._output_report_layout is None:
            log("Could not load output report from file.", info=False)
            return

        layout_name = self._output_report_layout.name()

        for layout in project.layoutManager().printLayouts():
            if layout.name() == layout_name:
                project.layoutManager().removeLayout(layout)
                break

        project.layoutManager().addLayout(self._output_report_layout)

        log(f"Successfully generated the report for " f"{self.report_name}.")

    def _check_feedback_cancelled_or_set_progress(self, value: float) -> bool:
        """Check if there is a request to cancel the process, else
        set the progress.

        :returns: Returns True if the process was cancelled else False.
        :rtype: bool
        """
        if self._feedback.isCanceled():
            tr_msg = tr("Generation of report has been cancelled.")
            self._error_messages.append(tr_msg)

            return True

        self._feedback.setProgress(value)

        return False

    def _get_failed_result(self) -> ReportOutputResult:
        """Creates the report result object."""
        return ReportOutputResult(
            False, "", self.report_name, tuple(self._error_messages)
        )

    def _export_to_pdf(self) -> bool:
        """Exports the report to a PDF file in the output
        directory using the layout name as the file name.

        :returns: True if the layout was successfully exported else False.
        :rtype: bool
        """
        log("Exporting report to PDF...")
        if self._layout is None or self._project is None:
            return False

        clean_report_name = clean_filename(self.report_name)
        pdf_path = f"{self._context.report_dir}/{clean_report_name}.pdf"

        # check if the pdf already exists, if it does, skip
        if os.path.exists(pdf_path):
            log(f"PDF file {pdf_path} already exists, skipping export.")
            return True

        exporter = QgsLayoutExporter(self._layout)
        log(f"Path when exporting pdf {pdf_path}")

        # Ensure all map items are rendered before exporting
        for item in self._layout.items():
            if isinstance(item, QgsLayoutItemMap):
                log(f"Waiting for map item '{item.id()}' to render...")
                item.refresh()

        # Export the layout to PDF
        settings = QgsLayoutExporter.PdfExportSettings()
        settings.rasterizeWholeImage = True
        self._layout.refresh()

        result = exporter.exportToPdf(pdf_path, settings)
        if result == QgsLayoutExporter.ExportResult.Success:
            log(f"PDF successfully exported to {pdf_path}")
            return True
        else:
            tr_msg = tr(
                "Could not export report to PDF. Check if there is a PDF "
                "opened for the same project."
            )
            self._error_messages.append(f"{tr_msg} {pdf_path}.")
            return False
        # open the layout in QGIS

    def _generate_report(self) -> bool:
        """Generate report.

        :returns: Returns True if the process succeeded, else False.
        :rtype: bool
        """
        if self._check_feedback_cancelled_or_set_progress(0):
            return False

        # Early check to see if the output already exists so we can skip the generation
        clean_report_name = clean_filename(self.report_name)
        pdf_path = f"{self._context.report_dir}/{clean_report_name}.pdf"
        verbose = False
        if verbose:
            log(f"Early check of PDF file {pdf_path} checking...")

        if os.path.exists(pdf_path):
            log(f"PDF file {pdf_path} already exists, skipping export.")
            return True

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
        log("Report template loaded successfully.")

        self._set_metadata_values()
        log("Metadata values set in report layout.")
        if self._check_feedback_cancelled_or_set_progress(45):
            return False

        self._set_site_layer()
        log("Site layer set in report layout.")

        if self._check_feedback_cancelled_or_set_progress(50):
            return False

        self._set_landscape_layer()
        self._set_2015_layer()
        log("Landscape layers set in report layout.")

        if self._check_feedback_cancelled_or_set_progress(55):
            return False

        self._configure_map_items_zoom_level()
        log("Map items zoom levels configured.")

        if self._check_feedback_cancelled_or_set_progress(75):
            return False
        log("Map items zoom levels configured.")

        # Save report layout in temporary file
        if not self._save_layout_to_file():
            return False
        log("Report layout saved to file.")

        if self._check_feedback_cancelled_or_set_progress(80):
            return False

        log("Report layout saved to file.")
        # Export report to PDF
        if not self._export_to_pdf():
            return False

        log("Report exported to PDF.")
        if self._check_feedback_cancelled_or_set_progress(100):
            return False

        log("Report generation completed successfully.")
        # Set result
        self._result = ReportOutputResult(
            True,
            self._context.report_dir,
            self._base_layout_name,
            tuple(self._error_messages),
        )
        log("Report generation result set successfully.")
        return True

    def _set_metadata_values(self):
        """Set the report metadata values."""

        if isinstance(self._metadata, SiteMetadata):
            log("Setting metadata values for SiteMetadata.")
            self.set_label_value("inception_date_label", self._metadata.inception_date)
            self.set_label_value("site_version_label", self._metadata.version)
            self.set_label_value("site_reference_label", self._metadata.site_reference)
            self.set_label_value("capture_date_label", self._metadata.capture_date)
            self.set_label_value("author_label", self._metadata.author)
            self.set_label_value("country_label", self._metadata.country)
            self.set_label_value(
                "site_area_label", f"{self._metadata.computed_area} ha"
            )
        elif isinstance(self._metadata, ProjectMetadata):
            log("Setting metadata values for ProjectMetadata.")
            # Check if the farmer_id ends with an integer and if so split it off
            # and use it for the ID label
            # The ending integer is used as the farmer number
            # we use a regex to strip off the whole multidigit number at the start or end of the string

            start_match_regex = r"^(\d+)"
            start_match = re.search(start_match_regex, self._metadata.farmer_id)

            end_match_regex = r"(\d+)$"
            end_match = re.search(end_match_regex, self._metadata.farmer_id)
            if start_match:
                log(f"Farmer ID starts with an integer: {start_match.group(0)}")
                farmer_number = str(start_match.group(0))
                farmer_name = self._metadata.farmer_id.replace(
                    farmer_number, ""
                ).strip()
                self.set_label_value("farmer_id_label", f"{farmer_name}")
                self.set_label_value("farmer_number_label", f"{farmer_number}")
            elif end_match:
                log(f"Farmer ID ends with an integer: {end_match.group(0)}")
                farmer_name = self._metadata.farmer_id[: end_match.start()]
                farmer_number = end_match.group(0)
                self.set_label_value("farmer_id_label", f"{farmer_name}")
                self.set_label_value("farmer_number_label", f"{farmer_number}")
            else:
                log("Farmer ID does not start or end with an integer.")
                # If the farmer_id does not start or end with an integer, use it as is
                self.set_label_value("farmer_id_label", f"{self._metadata.farmer_id}")
                # and hide the number box
                label_item = self._layout.itemById("farmer_number_label")
                label_item.hide()
            log("Setting report label values for ProjectMetadata.")
            try:
                if self._metadata.author:
                    log("report_author_label: " f"{self._metadata.author}")
                    self.set_label_value("report_author_label", self._metadata.author)
                else:
                    log("report_author_label: Not set")
            except AttributeError as e:
                log(
                    f"Error setting report author label value: {e}. "
                    "Author metadata attribute may be missing."
                )
            try:
                if self._metadata.project:
                    log("project_label: " f"{self._metadata.project}")
                    self.set_label_value("project_label", self._metadata.project)
                else:
                    log("project_label: Not set")
            except AttributeError as e:
                log(
                    f"Error setting project label value: {e}. "
                    "Project metadata attribute may be missing."
                )
            try:
                if self._metadata.inception_date:
                    log("inception_date_label: " f"{self._metadata.inception_date}")
                    # Check if inception_date is a QDate, convert to string if needed
                    inception_date = self._metadata.inception_date
                    if isinstance(inception_date, QDate):
                        inception_date = inception_date.toString("yyyy-MM-dd")
                    self.set_label_value("inception_date_label", inception_date)
                else:
                    log("inception_date_label: Not set")
            except AttributeError as e:
                log(
                    f"Error setting inception date label value: {e}. "
                    "Inception date metadata attribute may be missing."
                )
            return
            try:
                if self._metadata.capture_date:
                    log("capture_date_label: " f"{self._metadata.capture_date}")
                    self.set_label_value(
                        "capture_date_label", self._metadata.capture_date
                    )
                else:
                    log("capture_date_label: Not set")
            except AttributeError as e:

                log(
                    f"Error setting capture date label value: {e}. "
                    "Capture date metadata attribute may be missing."
                )
            try:
                if self._metadata.total_area:
                    log("area_label: " f"{self._metadata.total_area} ha")
                    self.set_label_value(
                        "area_label", f"{self._metadata.total_area} ha"
                    )
                else:
                    log("area_label: Not set")
            except AttributeError as e:
                log(
                    f"Error setting area label value: {e}. "
                    "Area metadata attribute may be missing."
                )
            log("Report label values set successfully.")

    def _get_layer_from_node_name(
        self,
        node_name: str,
        search_type: LayerNodeSearch = LayerNodeSearch.EXACT_MATCH,
        group_name: str = "",
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
        last_group = FileNotFoundError
        for node in root_tree.findLayers():
            # log(f"Checking Node: {matching_node} for {node_name}")
            if group_name:
                if group_name != last_group:
                    log(f"Group: {group_name}")
                last_group = group_name
                if node.parent() and node.parent().name() == group_name:
                    for child in node.parent().children():
                        log(f"Child: {child.name()}")
                        if (
                            search_type == LayerNodeSearch.EXACT_MATCH
                            and child.name() == node_name
                        ):
                            log(f"Exact match found for {child.name()}")
                            matching_node = child
                            break
                        elif (
                            search_type == LayerNodeSearch.CONTAINS
                            and node_name in child.name()
                        ):
                            log(f"Partial match found for {child.name()}")
                            matching_node = child
                            break
            else:
                if (
                    search_type == LayerNodeSearch.EXACT_MATCH
                    and node.name() == node_name
                ):
                    log(f"Exact match found for {node.name()}")
                    matching_node = node
                    break
                elif (
                    search_type == LayerNodeSearch.CONTAINS and node_name in node.name()
                ):
                    log(f"Partial match found for {node.name()}")
                    matching_node = node
                    break

        if matching_node is None:
            tr_msg = tr("layer node not found.")
            log(f"{tr_msg}, node name {node_name} using search mode: {search_type}")
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
        """Fetch the project boundary layer."""
        log("Setting site layer for the report...")
        site_path = (
            settings_manager.get_value(Settings.LAST_SITE_LAYER_PATH, default="")
            if isinstance(self._context.metadata, SiteMetadata)
            else settings_manager.get_value(
                Settings.CURRENT_PROJECT_LAYER_PATH, default=""
            )
        )
        log(f"Site layer path: {site_path}")
        path = Path(site_path)
        if not path.exists():
            tr_msg = tr("Report layer shapefile does not exist")
            log(tr_msg)
            self._error_messages.append(f"{tr_msg} {site_path}")
            return

        site_layer = self.find_layer_by_name(path.stem)

        if site_layer is None:
            return
        log(f"Found site layer: {site_layer.name()}")
        if not site_layer.isValid():
            tr_msg = tr("Report layer shapefile is invalid")
            log(tr_msg)
            self._error_messages.append(tr_msg)
            return
        log("Site layer is valid.")
        if isinstance(self._context.metadata, SiteMetadata):
            site_symbol = QgsFillSymbol.createSimple(REPORT_SITE_BOUNDARY_STYLE)
            site_layer.renderer().setSymbol(site_symbol)
            site_layer.triggerRepaint()
            log("Site layer style set successfully.")
        else:
            style_file = FileUtils.style_file_path(PROJECT_INSTANCE_STYLE)
            site_layer.loadNamedStyle(style_file)
            site_layer.triggerRepaint()

            raw_id = self._context.metadata.farmer_id
            safe_id = raw_id.replace("'", "''")  # escape single quotes

            site_layer.setSubsetString(f"\"FarmerID\" = '{safe_id}'")

            site_layer.triggerRepaint()
            log("Project layer style set successfully.")

        self._site_layer = site_layer

    def find_layer_by_name(self, layer_name):
        layers = QgsProject.instance().mapLayers()

        for layer_id, layer in layers.items():
            if clean_filename(layer.name()) == layer_name:
                return layer
        return None

    def _set_landscape_layer(self):
        """Set the landscape layer i.e. Landsat depending on the
        information in the TemporalInfo object.
        """

        landsat_2013_layer = self.get_first_matching_layer_in_group(
            LANDSAT_IMAGERY_GROUP_NAME, LANDSAT_2013_LAYER_SEGMENT
        )

        if landsat_2013_layer is not None:
            log("Landsat 2013 layer set .... OK")
            self._landscape_layer = landsat_2013_layer

        if self._landscape_layer is None:
            tr_msg = tr("Landscape layer not found")
            self._error_messages.append(f"{tr_msg} under {LANDSAT_IMAGERY_GROUP_NAME}")

    def _set_2015_layer(self):
        """Set the 2015 layer i.e. Landsat depending on the
        information in the TemporalInfo object.
        """

        landsat_2015_layer = self.get_first_matching_layer_in_group(
            LANDSAT_IMAGERY_GROUP_NAME, LANDSAT_2015_LAYER_SEGMENT
        )

        if landsat_2015_layer is not None:
            log("Landsat 2015 layer set .... OK")
            self._2015_layer = landsat_2015_layer

        if self._2015_layer is None:
            tr_msg = tr("2015 Landsat layer not found")
            self._error_messages.append(f"{tr_msg} under {LANDSAT_IMAGERY_GROUP_NAME}")

    def _configure_map_items_zoom_level(self):
        """Set layers and zoom levels of map items."""
        if self._site_layer is None:
            tr_msg = tr("Project layer not found or shapefile is invalid")
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
        self, detailed_extent: QgsRectangle, mask_layers: typing.List[QgsMapLayer]
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
        historic_masked_map = self._get_map_item_by_id("2013_historic_mask_map")
        log("Setting up historic map with mask for 2013 landscape imagery")
        if historic_masked_map and detailed_extent:
            # Transform extent
            landscape_imagery_extent = self._transform_extent(
                detailed_extent, self._site_layer.crs(), historic_masked_map.crs()
            )

            if landscape_imagery_extent.isNull():
                tr_msg = tr(
                    "Invalid extent for setting in the current imagery " "with mask map"
                )
                self._error_messages.append(tr_msg)
                log(tr_msg)
            else:
                log("Historic mask layer extent is set")
                landscape_mask_layers = [self._site_layer]
                landscape_mask_layers.extend(mask_layers)
                if self._landscape_layer is not None:
                    log(
                        f"Historic Landscape layer is set to {self._landscape_layer.name()}"
                    )
                    log(
                        f"Historic Landscape layer source {self._landscape_layer.source()}"
                    )
                    landscape_mask_layers.append(self._landscape_layer)
                historic_masked_map.setFollowVisibilityPreset(False)
                historic_masked_map.setFollowVisibilityPresetName("")
                historic_masked_map.setLayers(landscape_mask_layers)
                historic_masked_map.zoomToExtent(landscape_imagery_extent)
                historic_masked_map.refresh()

        # Landscape with no-mask map
        historic_no_mask_map = self._get_map_item_by_id("2013_historic_no_mask_map")
        if historic_no_mask_map and detailed_extent:
            # Transform extent
            log(
                "Setting up historic landscape map with NO mask for 2013 landscape imagery"
            )
            landscape_no_mask_extent = self._transform_extent(
                detailed_extent, self._site_layer.crs(), historic_no_mask_map.crs()
            )

            if landscape_no_mask_extent.isNull():
                tr_msg = tr(
                    "Invalid extent for setting in the landscape imagery "
                    "with no-mask map"
                )
                self._error_messages.append(tr_msg)
            else:
                log("Historic mask layer extent is set")
                landscape_no_mask_layers = [self._site_layer]
                if self._landscape_layer is not None:
                    log(
                        f"Historic Landscape layer is set to {self._landscape_layer.name()}"
                    )
                    log(
                        f"Historic Landscape layer source {self._landscape_layer.source()}"
                    )

                    landscape_no_mask_layers.append(self._landscape_layer)

                historic_no_mask_map.setFollowVisibilityPreset(False)
                historic_no_mask_map.setFollowVisibilityPresetName("")
                historic_no_mask_map.setLayers(landscape_no_mask_layers)
                historic_no_mask_map.zoomToExtent(landscape_no_mask_extent)
                historic_no_mask_map.refresh()

        # landscape layer with mask map
        landscape_masked_map_2015 = self._get_map_item_by_id("2015_historic_mask_map")
        if landscape_masked_map_2015 and detailed_extent:
            log("Setting up historic map WITH mask for 2015 imagery")
            # Transform extent
            landscape_imagery_extent = self._transform_extent(
                detailed_extent, self._site_layer.crs(), landscape_masked_map_2015.crs()
            )

            if landscape_imagery_extent.isNull():
                tr_msg = tr(
                    "Invalid extent for setting in the current imagery " "with mask map"
                )
                self._error_messages.append(tr_msg)
                log(tr_msg)
            else:
                log("Historic mask layer extent is set")
                landscape_mask_layers = [self._site_layer]
                landscape_mask_layers.extend(mask_layers)
                if self._2015_layer is not None:
                    log(f"2015 Landscape layer is set to {self._2015_layer.name()}")
                    log(f"2015 Landscape layer source {self._2015_layer.source()}")
                    landscape_mask_layers.append(self._2015_layer)
                landscape_masked_map_2015.setFollowVisibilityPreset(False)
                landscape_masked_map_2015.setFollowVisibilityPresetName("")
                landscape_masked_map_2015.setLayers(landscape_mask_layers)
                landscape_masked_map_2015.zoomToExtent(landscape_imagery_extent)
                landscape_masked_map_2015.refresh()

        # Landscape with no-mask map
        landscape_no_mask_map_2015 = self._get_map_item_by_id(
            "2015_historic_no_mask_map"
        )
        if landscape_no_mask_map_2015 and detailed_extent:
            log("Setting up landscape map with NO mask for 2015 landscape imagery")
            # Transform extent
            landscape_no_mask_extent = self._transform_extent(
                detailed_extent,
                self._site_layer.crs(),
                landscape_no_mask_map_2015.crs(),
            )

            if landscape_no_mask_extent.isNull():
                tr_msg = tr(
                    "Invalid extent for setting in the landscape imagery "
                    "with no-mask map"
                )
                self._error_messages.append(tr_msg)
            else:
                log("Historic mask layer extent is set")
                landscape_no_mask_layers = [self._site_layer]
                if self._2015_layer is not None:
                    log(f"2015 Landscape layer is set to {self._2015_layer.name()}")
                    log(f"2015 Landscape layer source {self._2015_layer.source()}")
                    landscape_no_mask_layers.append(self._2015_layer)
                landscape_no_mask_map_2015.setFollowVisibilityPreset(False)
                landscape_no_mask_map_2015.setFollowVisibilityPresetName("")
                landscape_no_mask_map_2015.setLayers(landscape_no_mask_layers)
                landscape_no_mask_map_2015.zoomToExtent(landscape_imagery_extent)
                landscape_no_mask_map_2015.refresh()

    def _configure_current_maps(
        self, detailed_extent: QgsRectangle, mask_layers: typing.List[QgsMapLayer]
    ):
        """Set the zoom level and layers for the current imagery maps.

        :param detailed_extent: Extent to use for the current maps.
        :type detailed_extent: QgsRectangle

        :param mask_layers: Exclusion mask layers
        :type mask_layers: list
        """
        google_layer = self._get_layer_from_node_name(
            GOOGLE_LAYER_NAME, LayerNodeSearch.EXACT_MATCH
        )

        # Current imagery with mask map
        current_mask_map = self._get_map_item_by_id("current_mask_map")
        if current_mask_map and detailed_extent:
            # Transform extent
            current_imagery_extent = self._transform_extent(
                detailed_extent, self._site_layer.crs(), current_mask_map.crs()
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
                detailed_extent, self._site_layer.crs(), current_no_mask_map.crs()
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

    def get_first_layer_in_group(self, group_name: str) -> typing.Optional[QgsMapLayer]:
        """Get the first layer in the group with the given name.

        ..versionadded 1.5

        ..addedby: Tim Sutton, 4 May 2025

        I added this method because the original method returned layers with the incorrect source.
        This method is a recursive function that searches for the first layer
        in the group with the given name.

        :param group_name: Name of the group to search for.
        :type group_name: str
        :returns: Returns the first layer found in the group or None if not found.
        :rtype: QgsMapLayer
        """

        def recurse(node, indent="", parent=None):
            if isinstance(node, QgsLayerTreeGroup):
                if node.name() == group_name:
                    for child in node.children():
                        if isinstance(child, QgsLayerTreeLayer):
                            layer = child.layer()
                            if layer:
                                log(
                                    f"{indent}🗃️  Found Layer in group '{group_name}': {layer.name()}"
                                )
                                log(f"{indent}🚛  ↳ Source: {layer.source()}")
                                log(f"{indent}🛍️  ↳ Provider: {layer.providerType()}")
                                log(
                                    "-----------------------------------------------------------"
                                )
                                return layer
                    return None  # Group matched, but no layer found
                else:
                    for child in node.children():
                        found = recurse(child, indent + "  ", node)
                        if found:
                            return found
            return None

        root = QgsProject.instance().layerTreeRoot()
        return recurse(root)

    def get_first_matching_layer_in_group(
        self, group_name: str, search_string: str
    ) -> typing.Optional[QgsMapLayer]:
        """Get the first layer that contains the search string in the group that has the given group name.

        ..versionadded 1.5

        ..addedby: Tim Sutton, 4 May 2025

        I added this method because the original method returned layers with the incorrect source.
        This method is a recursive function that searches for the first layer
        in the group with the given name.


        :param group_name: Name of the group to search for.
        :type group_name: str
        :param search_string: The string to search for in the layer name.
        :type search_string: str
        :returns: Returns the first layer found in the group or None if not found.
        :rtype: QgsMapLayer
        """

        def recurse(node, indent="", parent=None):
            if isinstance(node, QgsLayerTreeGroup):
                if node.name() == group_name:
                    for child in node.children():
                        if isinstance(child, QgsLayerTreeLayer):
                            layer = child.layer()
                            if search_string in layer.name():
                                log(
                                    f"{indent}🗃️  Found Layer in group '{group_name}': {layer.name()}"
                                )
                                log(f"{indent}🚛  ↳ Source: {layer.source()}")
                                log(f"{indent}🛍️  ↳ Provider: {layer.providerType()}")
                                log(
                                    "-----------------------------------------------------------"
                                )
                                return layer
                    return None  # Group matched, but no layer found
                else:
                    for child in node.children():
                        found = recurse(child, indent + "  ", node)
                        if found:
                            return found
            return None

        root = QgsProject.instance().layerTreeRoot()
        return recurse(root)

    def _get_layers_in_group(self, group_name: str) -> typing.List[QgsMapLayer]:
        """Gets all map layers in the group with the given name, recursively.

        .. versionadded:: 1.5
        .. addedby:: Tim Sutton, 4 May 2025

        :param group_name: Group name to retrieve the layers.
        :type group_name: str

        :returns: List of all valid QgsMapLayer instances found in the group.
        :rtype: list
        """
        result_layer_names: typing.List[str] = []
        result_layers: typing.List[QgsMapLayer] = []

        def recurse(node, indent=""):
            if isinstance(node, QgsLayerTreeGroup):
                if node.name() == group_name:
                    log(f"📁 Found group: {group_name}")
                    # Collect layers within this group only
                    for child in node.children():
                        if isinstance(child, QgsLayerTreeLayer):
                            layer = child.layer()
                            try:
                                log(f"{indent}🗃️  Layer: {layer.name()}")
                                result_layer_names.append(layer.name())
                            except:
                                log(
                                    f"{indent}⚠️ Invalid or missing layer in group '{group_name}'"
                                )
                    return True  # Found and processed the group — stop recursion
                else:
                    for child in node.children():
                        if recurse(child, indent + "  "):
                            return True  # Early exit once group is found
                return False

        root = self._project.layerTreeRoot()
        recurse(root)
        for layer_name in result_layer_names:
            layer = self.get_first_matching_layer_in_group(group_name, layer_name)
            result_layers.append(layer)
        return result_layers

    def _configure_site_maps(self) -> QgsRectangle:
        """Set the zoom level and layers for the overview and detailed maps.

        :returns: Returns the extent of the detailed map.
        :rtype: QgsRectangle
        """

        site_extent = self._site_layer.extent()

        google_layer = self._get_layer_from_node_name(
            GOOGLE_LAYER_NAME, LayerNodeSearch.EXACT_MATCH
        )

        map_item_layers = [self._site_layer]
        admin_layer = self.get_first_layer_in_group(ADMIN_AREAS_GROUP_NAME)
        map_item_layers.append(admin_layer)

        if google_layer:
            # We want the Google layer as the last item
            map_item_layers.append(google_layer)

        # Overview map
        overview_map = self._get_map_item_by_id("site_location_overview_map")
        if overview_map:
            # We use the admin layer to control the overview extent i.e.
            # ensure we do not zoom out beyond the national extent.
            admin_extent = None
            overview_extent = None
            log(f"Overview map CRS: {overview_map.crs().authid()}")
            if admin_layer:
                extent = admin_layer.extent()
                log(
                    f"Admin layer CRS: {admin_layer.crs().authid() if admin_layer else 'None'}"
                )
                log(f"Admin layer extent: {extent.toString()}")
                log(
                    f"Using reference admin layer for site_location_overview_map {admin_layer.name()}"
                )

                admin_extent = self._transform_extent(
                    extent, admin_layer.crs(), overview_map.crs()
                )
                log(f"Admin layer extent after transform: {admin_extent.toString()}")
            else:
                log("Reference admin layer not found, using site layer extent")

                log(f"Site layer CRS: {self._site_layer.crs().authid()}")
                log(f"Site layer extent: {self._site_layer.extent().toString()}")
                # Transform extent
                overview_extent = self._transform_extent(
                    site_extent, self._site_layer.crs(), overview_map.crs()
                )
            if not overview_extent or overview_extent.isNull():
                tr_msg = tr("Invalid extent for setting in the overview map.")
                self._error_messages.append(tr_msg)
            else:
                # Zoom out by factor
                overview_extent.scale(OVERVIEW_ZOOM_OUT_FACTOR)

            if admin_extent:
                log("Admin extent is set")
                if overview_extent and admin_extent.contains(overview_extent):
                    log("Admin extent contains overview extent")
                    overview_map.zoomToExtent(overview_extent)
                else:
                    log("Admin extent does not contain overview extent")
                    overview_map.zoomToExtent(admin_extent)
            else:
                log("Admin extent is not set, using overview extent")
                overview_map.zoomToExtent(overview_extent)
            log(f"Overview map extent: {overview_map.extent().toString()}")
            # Visibiity presets are the same thing as map themes
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
                site_extent, self._site_layer.crs(), detailed_map.crs()
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

    def _transform_extent(
        self,
        extent: QgsRectangle,
        source_crs: QgsCoordinateReferenceSystem,
        target_crs: QgsCoordinateReferenceSystem,
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
                source_crs, target_crs, self._project
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
                self._error_messages.append(
                    f"{tr_msg} {self._context.qgs_project_path}"
                )
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
        base_report_name = self.report_name

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
