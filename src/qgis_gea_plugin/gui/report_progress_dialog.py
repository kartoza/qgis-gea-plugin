# -*- coding: utf-8 -*-
"""
Dialog for showing the progress of the report generation process.
"""

import os
import platform
import typing
import subprocess

import pathlib

from qgis.core import Qgis, QgsTaskWrapper
from qgis.gui import QgsGui

from qgis.PyQt import QtCore, QtGui, QtWidgets

from qgis.PyQt.uic import loadUiType

from ..models.report import ReportOutputResult, ReportSubmitResult
from ..lib.reports.manager import report_manager
from ..utils import FileUtils, log, tr

WidgetUi, _ = loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/report_progress_dialog.ui")
)


class ReportProgressDialog(QtWidgets.QDialog, WidgetUi):
    """Dialog for showing the progress of the report generation process."""

    dialog_closed = QtCore.pyqtSignal()

    def __init__(
        self,
        submit_result: ReportSubmitResult,
        project_dir=None,
        show_pdf_folder=False,
        message=None,
        parent=None
    ):
        super().__init__(
            parent,
            QtCore.Qt.WindowMinimizeButtonHint | QtCore.Qt.WindowCloseButtonHint
        )
        self.setupUi(self)

        QgsGui.enableAutoGeometryRestore(self)

        self._report_manager = report_manager

        self._report_running = True

        self.show_pdf_folder = show_pdf_folder
        self.project_dir = project_dir
        self.report_output_dir = None

        self._submit_result = submit_result
        self._task = submit_result.task
        self._feedback = self._submit_result.feedback
        self._feedback.progressChanged.connect(self._on_progress_changed)

        if not self.show_pdf_folder:
            self.btn_open_pdf = self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok)
            self.btn_open_pdf.setText(tr("Open PDF"))
            self.btn_open_pdf.setEnabled(False)
            self.btn_open_pdf.setIcon(FileUtils.get_icon("pdf.svg"))
            self.btn_open_pdf.clicked.connect(self._on_open_pdf)
        else:
            self.btn_open_pdf = self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok)
            self.btn_open_pdf.setText(tr("Open report(s) folder"))
            self.btn_open_pdf.setEnabled(False)
            self.btn_open_pdf.setIcon(FileUtils.get_icon("pdf.svg"))
            self.btn_open_pdf.clicked.connect(self._on_open_pdf_folder)

        self.btn_close = self.buttonBox.button(QtWidgets.QDialogButtonBox.Close)
        self.btn_close.setText(tr("Cancel"))
        self.btn_close.clicked.connect(self._on_closed)

        self.progress_message = message or tr("Generating report...")
        self.lbl_message.setText(self.progress_message)

        self.pg_bar.setValue(int(self._feedback.progress()))

        if self._task is not None:
            self._task.taskCompleted.connect(self._on_report_finished)
            self._task.taskTerminated.connect(self._on_report_error)

    def _on_progress_changed(self, progress: float):
        """Slot raised when report progress has changed.

        :param progress: Current progress of the report
        process.
        :type progress: float
        """
        self.pg_bar.setValue(int(progress))

    def _on_report_finished(self):
        """Slot raised when the report has successfully completed."""
        self.btn_open_pdf.setEnabled(True)
        self._set_close_state()

        if self.report_result and len(self.report_result.errors) == 0:
            self.lbl_message.setText(tr("Report generation complete"))
        elif self.show_pdf_folder:
            self.report_output_dir = os.path.join(
                f"{self.project_dir}",
                "reports"
            )
        else:
            tr_msg = tr(
                "Report generation complete however there were errors "
                "encountered. \nSee logs for more information."
            )
            self.lbl_message.setText(tr_msg)

    def _on_report_error(self):
        """Slot raised when an error occurred."""
        self.btn_open_pdf.setEnabled(False)
        self._set_close_state()
        tr_msg = tr(
            f"Error occurred during report generation. "
            "\nSee logs for more information"
        )
        self.lbl_message.setText(tr_msg)

        if not isinstance(self._task, QgsTaskWrapper):
            log(tr(f"Error generating report, {self._task._error_messages} \n"))

            log(tr(f"{self._task._result.errors}")) if self._task._result else None
        else:
            log(f"Probem running task {self._task.status}")


    @property
    def report_result(self) -> typing.Optional[ReportOutputResult]:
        """Gets the report result.

        :returns: The report result based on the submit
        status or None if the task is not found or the
        task is not complete or an error occurred.
        :rtype: ReportResult
        """
        if (self._task is None or
                isinstance(self._task, QgsTaskWrapper)
        ):
            return None

        return self._task.result

    def _on_open_pdf(self):
        """Slot raised to show PDF report if report generation process
        was successful.
        """
        if self.report_result is None:
            log(
                tr(
                    "Output from the report generation "
                    "process could not be determined."
                )
            )

            return

        status = self._report_manager.view_pdf(self.report_result)
        if not status:
            log(tr("Unable to open the PDF report."))

    def _on_open_pdf_folder(self):
        """Slot raised to show PDF report if report generation process
        was successful.
        """

        # Open the folder
        if self.report_output_dir:
            if os.path.exists(str(self.report_output_dir)):
                current_os = platform.system()

                if current_os == "Windows":
                    os.startfile(self.report_output_dir)
                elif current_os == "Darwin":  # macOS
                    subprocess.run(['open', self.report_output_dir])
                elif current_os == "Linux":
                    subprocess.run(['xdg-open', self.report_output_dir])
                else:
                    log(f"Unsupported OS: {current_os}")
                subprocess.run(['xdg-open', self.report_output_dir])
            else:
                log("Folder path doesn't exist")
        else:
            log(f"Reporty directory not available {self.report_output_dir}")

    def _set_close_state(self):
        """Set dialog to a closeable state."""
        self._report_running = False
        self.btn_close.setText(tr("Close"))

    def _on_closed(self):
        """Slot raised when the Close button has been clicked."""
        if self._report_running:
            if self.show_pdf_folder:
                self._submit_result.task.cancel()
            else:
                status = self._report_manager.cancel(self._submit_result)
                if not status:
                    log(tr("Unable to cancel report generation process."))
                    return

            self._set_close_state()
            self.lbl_message.setText(tr("Report generation canceled"))
        else:
            self.dialog_closed.emit()
            self.close()
