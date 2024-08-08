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
    Qgis,
    QgsBasicNumericFormat,
    QgsFeedback,
    QgsFillSymbol,
    QgsLayerTreeNode,
    QgsLayoutExporter,
    QgsLayoutItemLabel,
    QgsLayoutItemLegend,
    QgsLayoutItemManualTable,
    QgsLayoutItemMap,
    QgsLayoutItemPage,
    QgsLayoutItemPicture,
    QgsLayoutItemScaleBar,
    QgsLayoutItemShape,
    QgsLayoutPoint,
    QgsLayoutSize,
    QgsMapLayerLegendUtils,
    QgsNumericFormatContext,
    QgsPrintLayout,
    QgsProcessingFeedback,
    QgsProject,
    QgsRasterLayer,
    QgsReadWriteContext,
    QgsLegendRenderer,
    QgsLegendStyle,
    QgsScaleBarSettings,
    QgsTask,
    QgsTableCell,
    QgsTextFormat,
    QgsUnitTypes,
)

from qgis.PyQt import QtCore, QtGui, QtXml

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
                f" See details: ",
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
            tr_msg = tr("Could not export report to PDF")
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

        if self._check_feedback_cancelled_or_set_progress(45):
            return False

        self._set_metadata_values()

        if self._check_feedback_cancelled_or_set_progress(55):
            return False

        # Save report layout in temporary file
        if not self._save_layout_to_file():
            return False

        if self._check_feedback_cancelled_or_set_progress(75):
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
            tuple()
        )

        return True

    def _set_metadata_values(self):
        """Set the site metadata values."""
        # Inception date
        self.set_Label_value("inception_date_label", self._metadata.inception_date)

        # Site reference version
        self.set_Label_value("site_version_label", self._metadata.version)

        # Site reference
        self.set_Label_value("site_reference_label", self._metadata.site_reference)

        # Site capture date
        self.set_Label_value("capture_date_label", self._metadata.capture_date)

        # Author
        self.set_Label_value("author_label", self._metadata.author)

        # Country
        self.set_Label_value("country_label", self._metadata.country)

        # Area value
        self.set_Label_value("site_area_label", self._metadata.computed_area)

    def _set_project(self):
        """Deserialize the project from the report context."""
        if not self._context.qgs_project_path:
            tr_msg = tr("Project file not specified.")
            self._error_messages.append(tr_msg)
            return

        else:
            if not os.access(self._context.qgs_project_path, os.R_OK):
                tr_msg = tr(
                    "Current user does not have permission to read the project file."
                )
                self._error_messages.append(tr_msg)
                return

            p = Path(self._context.qgs_project_path)
            if not p.exists():
                tr_msg = tr("Project file does not exist")
                self._error_messages.append(f"{tr_msg} {self._context.qgs_project_path}.")
                return

        project = QgsProject()
        result = project.read(self._context.qgs_project_path)
        if not result:
            tr_msg = tr("Unable to read the project file")
            self._error_messages.append(f"{tr_msg} {self._context.qgs_project_path}.")
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

    def set_Label_value(self, label_id: str, value: str):
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
