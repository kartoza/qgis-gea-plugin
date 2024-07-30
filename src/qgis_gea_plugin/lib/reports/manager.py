# -*- coding: utf-8 -*-
"""
Manager that handles report generation.
"""

import datetime
import os
from pathlib import Path
import typing

from qgis.core import (
    Qgis,
    QgsApplication,
    QgsFeedback,
    QgsMasterLayoutInterface,
    QgsProject,
    QgsPrintLayout,
    QgsTask,
)
from qgis.gui import QgsLayoutDesignerInterface
from qgis.utils import iface

from qgis.PyQt import QtCore

from ...models.report import ReportSubmitResult, SiteMetadata, SiteReportContext
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

    def generate_site_report(self, metadata: SiteMetadata, project_folder: str) -> ReportSubmitResult:
        """Initiates the site report generation process.

        :param metadata: Information about the site.
        :type metadata: SiteMetadata

        :param project_folder: Path of the project directory.
        :type project_folder: str

        :returns: Returns a result object with the status of the submission.
        :rtype: ReportSubmitResult
        """
        if not Path(project_folder).exists():
            log(f"Project folder {project_folder} does not exist.")
            return ReportSubmitResult(False, None, "-1")

        feedback = QgsFeedback()
        context = self.create_site_context(metadata, project_folder, feedback)
        if context is None:
            log(f"Contextual information for creating the site report could not be created.")
            return ReportSubmitResult(False, None, "-1")

        return ReportSubmitResult(True, feedback, "")

    @classmethod
    def create_site_context(
            cls,
            metadata: SiteMetadata,
            project_folder: str,
            feedback: QgsFeedback
    ) -> typing.Optional[SiteReportContext]:
        """Creates the contextual information required for generating the report.

        :param metadata: Information about the site.
        :type metadata: SiteMetadata

        :param project_folder: Path of the project directory.
        :type project_folder: str

        :param feedback: Feedback object for providing updates on
        the report generation process.
        :type feedback: QgsFeedback

        :returns: Returns a context object containing required
        information for generating the report or None if it
        could not be created.
        :rtype: SiteReportContext
        """
        # Check report template
        report_template_path = FileUtils.site_report_template_path()
        if not Path(report_template_path).exists():
            log(f"Site report template {report_template_path} not found.")
            return None

        # Create 'reports' subdirectory
        report_dir = os.path.normpath(f"{project_folder}/reports")
        create_dir(report_dir)

        # Assert that the directory was successfully created
        if not Path(report_dir).exists():
            log(f"Reports directory could not be created in the project folder.")
            return None

        # Save project file
        qgs_project_path = os.path.normpath(
            f"{report_dir}/{clean_filename(metadata.area_name)}.qgz"
        )

        version = Qgis.versionInt()
        storage_type = None
        if version >= 32200:
            storage_type = QgsProject.instance().filePathStorage()
            QgsProject.instance().setFilePathStorage(Qgis.FilePathType.Absolute)

        result = QgsProject.instance().write(qgs_project_path)

        # Restore the original storage type
        if version >= 32200 and storage_type is not None:
            QgsProject.instance().setFilePathStorage(storage_type)

        if not result:
            log(f"Unable to save the current project to file.")
            return None

        return SiteReportContext(
            metadata,
            feedback,
            project_folder,
            qgs_project_path,
            report_template_path
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

        if (
                report_task.status() != QgsTask.TaskStatus.Complete
                or report_task.status() != QgsTask.TaskStatus.Terminated
        ):
            report_task.cancel()

        _ = self._report_tasks.pop(task_id)

        return True
