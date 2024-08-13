# -*- coding: utf-8 -*-
"""
Manager that handles report generation.
"""

import datetime
import os
from pathlib import Path
import shutil
import typing

from qgis.core import (
    Qgis,
    QgsApplication,
    QgsFeedback,
    QgsProject,
    QgsTask,
)
from qgis.utils import iface

from qgis.PyQt import QtCore, QtGui, sip

from .generator import SiteReportReportGeneratorTask
from ...models.base import MapTemporalInfo
from ...models.report import (
    ReportOutputResult,
    ReportSubmitResult,
    SiteMetadata,
    SiteReportContext
)
from ...utils import clean_filename, create_dir, FileUtils, log


class ReportManager(QtCore.QObject):
    """Class for handling report generation."""

    generate_started = QtCore.pyqtSignal(str)
    generate_error = QtCore.pyqtSignal(str)
    generate_completed = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.iface = iface

        # Report task (value) indexed by task id (key)
        self._report_tasks = {}

        # Report results (value) indexed by task id (key)
        self._report_results = {}

        self.task_manager = QgsApplication.instance().taskManager()

    def generate_site_report(
            self,
            metadata: SiteMetadata,
            project_folder: str,
            temporal_info: MapTemporalInfo
    ) -> ReportSubmitResult:
        """Initiates the site report generation process.

        :param metadata: Information about the site.
        :type metadata: SiteMetadata

        :param project_folder: Path of the project directory.
        :type project_folder: str

        :param temporal_info: Datetime range in the map canvas.
        :type temporal_info: MapTemporalInfo

        :returns: Returns a result object with the status of the submission.
        :rtype: ReportSubmitResult
        """
        if not Path(project_folder).exists():
            log(f"Project folder {project_folder} does not exist.", info=False)
            return ReportSubmitResult(False, None, "-1")

        feedback = QgsFeedback()
        context = self.create_site_context(
            metadata,
            project_folder,
            feedback,
            temporal_info
        )
        if context is None:
            log(
                f"Contextual information for creating the site report could not be created.",
                info=False
            )
            return ReportSubmitResult(False, None, "-1")

        site_report_task = SiteReportReportGeneratorTask(context)
        task_id = self.task_manager.addTask(site_report_task)
        if task_id == 0:
            log(f"Site report task could be not be submitted.", info=False)
            return ReportSubmitResult(False, None, "-1")

        self._report_tasks[task_id] = site_report_task

        return ReportSubmitResult(True, feedback, str(task_id))

    def task_by_id(self, task_id: str) -> typing.Optional[SiteReportReportGeneratorTask]:
        """Gets the report generator task using its identifier.

        :param task_id: Task identifier.
        :type task_id: str

        :returns: The tas corresponding to the given ID or
        None if not found.
        :rtype: QgsTask
        """
        try:
            task_id = int(task_id)
        except ValueError:
            return None

        return self.task_manager.task(task_id)

    def on_report_status_changed(self, task_id: int, status: QgsTask.TaskStatus):
        """Slot raised when the status of a generator task has changed.

        This function will emit when the report generator task has started,
        when it has completed successfully or terminated due to an error.

        :param task_id: ID of the task.
        :type task_id: int

        :param status: New task status.
        :type status: QgsTask.TaskStatus
        """
        task = self.task_manager.task(task_id)
        if not isinstance(task, SiteReportReportGeneratorTask):
            return

        if str(task_id) not in self._report_tasks:
            return

        if status == QgsTask.TaskStatus.Running:
            self.generate_started.emit(str(task_id))

        elif status == QgsTask.TaskStatus.Terminated:
            self.remove_report_task(str(task_id))

            self.generate_error.emit(str(task_id))

        elif status == QgsTask.TaskStatus.Complete:
            # Get result
            task = self.task_manager.task(task_id)
            result = task.result
            if result is not None:
                self._report_results[str(task_id)] = result

            self.remove_report_task(str(task_id))

            self.generate_completed.emit(str(task_id))

    @classmethod
    def create_site_context(
            cls,
            metadata: SiteMetadata,
            project_folder: str,
            feedback: QgsFeedback,
            temporal_info: MapTemporalInfo
    ) -> typing.Optional[SiteReportContext]:
        """Creates the contextual information required for generating the report.

        :param metadata: Information about the site.
        :type metadata: SiteMetadata

        :param project_folder: Path of the project directory.
        :type project_folder: str

        :param feedback: Feedback object for providing updates on
        the report generation process.
        :type feedback: QgsFeedback

        :param temporal_info: Datetime range in the map canvas.
        :type temporal_info: MapTemporalInfo

        :returns: Returns a context object containing required
        information for generating the report or None if it
        could not be created.
        :rtype: SiteReportContext
        """
        # Check report template
        report_template_path = FileUtils.site_report_template_path()
        if not Path(report_template_path).exists():
            log(
                f"Site report template {report_template_path} not found.",
                info=False
            )
            return None

        # Create 'reports' subdirectory
        report_dir = os.path.normpath(f"{project_folder}/reports")
        create_dir(report_dir)

        # Assert that the directory was successfully created
        if not Path(report_dir).exists():
            log(
                f"Reports directory could not be created in the project folder.",
                info=False
            )
            return None

        # Save the project file in the current location then copy
        # the project file for use in the report.
        storage_type = None
        if Qgis.versionInt() >= 32200:
            storage_type = QgsProject.instance().filePathStorage()
            QgsProject.instance().setFilePathStorage(Qgis.FilePathType.Absolute)

        status = QgsProject.instance().write()
        if not status:
            log(
                f"Unable to save the current project.",
                info=False
            )
            return None

        current_qgs_project_path = QgsProject.instance().absoluteFilePath()
        if not current_qgs_project_path:
            log(
                f"Unable to retrieve the file path of the current project.",
                info=False
            )
            return None

        # Copy project file to 'reports' folder
        report_qgs_project_path = os.path.normpath(
            f"{report_dir}/{clean_filename(metadata.area_name)}.qgz"
        )
        try:
            shutil.copy(current_qgs_project_path, report_qgs_project_path)
        except (OSError, shutil.SameFileError):
            log(
                f"Unable to copy the project file in the 'reports' folder.",
                info=False
            )
            return None

        # Reset to the original file storage type
        if Qgis.versionInt() >= 32200 and storage_type is not None:
            QgsProject.instance().setFilePathStorage(storage_type)

        return SiteReportContext(
            metadata,
            feedback,
            project_folder,
            report_qgs_project_path,
            report_template_path,
            temporal_info
        )

    def remove_report_task(self, task_id: str) -> bool:
        """Remove report task associated with the given scenario.

        :param task_id: Unique report task identifier.
        :type task_id: str

        :returns: True if the task has been successfully removed
        else False if there is no associated task.
        :rtype: bool
        """
        if task_id not in self._report_tasks:
            return False

        report_task = self._report_tasks[task_id]
        if report_task is None:
            return False

        if sip.isdeleted(report_task):
            _ = self._report_tasks.pop(task_id)
            return False

        if (
                report_task.status() != QgsTask.TaskStatus.Complete
                or report_task.status() != QgsTask.TaskStatus.Terminated
        ):
            report_task.cancel()

        _ = self._report_tasks.pop(task_id)

        return True

    def get_output_result(
            self,
            submit_result: ReportSubmitResult
    ) -> typing.Optional[ReportOutputResult]:
        """Get the output result from the given submit result.

        :param submit_result: Result from the request to process a report request,
        :type submit_result: ReportSubmitResult

        :returns: Returns the corresponding output result for the given submit
        result or None if the process is still running or an error occurred.
        :rtype: ReportOutputResult
        """
        if not submit_result.success:
            return None

        return self._report_results.get(submit_result.identifier, None)

    def cancel(self, submit_result: ReportSubmitResult) -> bool:
        """Cancel a report generation task.

        :param submit_result: Submit result whose corresponding task is to
        be canceled.
        :type submit_result: ReportSubmitResult

        :returns: Returns True if the task was successfully cancelled
        else False if the task was not found or if it had already
        completed.
        :rtype: bool
        """
        if not submit_result.success:
            return False

        return self.remove_report_task(submit_result.identifier)

    @classmethod
    def view_pdf(cls, output_result: ReportOutputResult):
        """Opens the output report in the host's default PDF viewer.

        :param output_result: Result object from the report generation
        process.
        :type output_result: ReportResult

        :returns: True if the PDF was successfully loaded, else
        False if the result from the generation process was False.
        :rtype: bool
        """
        if not output_result.success:
            return False

        pdf_path = os.path.normpath(
            f"{output_result.output_path}/{clean_filename(output_result.name)}.pdf"
        )

        pdf_url = QtCore.QUrl.fromLocalFile(str(pdf_path))
        if pdf_url.isEmpty():
            return False

        return QtGui.QDesktopServices.openUrl(pdf_url)


report_manager = ReportManager()
