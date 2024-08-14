# -*- coding: utf-8 -*-
"""
Dialog for showing the progress of the report generation process.
"""

import os
import typing

from qgis.core import Qgis
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

        self._submit_result = submit_result
        self._feedback = self._submit_result.feedback
        self._feedback.progressChanged.connect(self._on_progress_changed)

        self.btn_open_pdf = self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok)
        self.btn_open_pdf.setText(tr("Open PDF"))
        self.btn_open_pdf.setEnabled(False)
        self.btn_open_pdf.setIcon(FileUtils.get_icon("pdf.svg"))
        self.btn_open_pdf.clicked.connect(self._on_open_pdf)

        self.btn_close = self.buttonBox.button(QtWidgets.QDialogButtonBox.Close)
        self.btn_close.setText(tr("Cancel"))
        self.btn_close.clicked.connect(self._on_closed)

        self.lbl_message.setText(tr("Generating report..."))

        self.pg_bar.setValue(int(self._feedback.progress()))

        self._task = None
        if submit_result.identifier:
            self._task = self._report_manager.task_by_id(submit_result.identifier)

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

        if len(self.report_result.errors) == 0:
            self.lbl_message.setText(tr("Report generation complete"))
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
            f"{self._task.error_messages}"
            "\nSee logs for more information"
        )
        self.lbl_message.setText(tr_msg)

        log(tr(f"Error generating report, {self._task.error_messages} \n"))

        log(tr(f"{self._task._result.errors}")) if self._task._result else None

    @property
    def report_result(self) -> typing.Optional[ReportOutputResult]:
        """Gets the report result.

        :returns: The report result based on the submit
        status or None if the task is not found or the
        task is not complete or an error occurred.
        :rtype: ReportResult
        """
        if self._task is None:
            return None

        return self._task.result

    def _on_open_pdf(self):
        """Slot raised to show PDF report if report generation process
        was successful.
        """
        if self.report_result is None:
            log(
                tr("Output from the report generation process could not be determined.")
            )

            return

        status = self._report_manager.view_pdf(self.report_result)
        if not status:
            log(tr("Unable to open the PDF report."))

    def _set_close_state(self):
        """Set dialog to a closeable state."""
        self._report_running = False
        self.btn_close.setText(tr("Close"))

    def _on_closed(self):
        """Slot raised when the Close button has been clicked."""
        if self._report_running:
            status = self._report_manager.cancel(self._submit_result)
            if not status:
                log(tr("Unable to cancel report generation process."))
                return

            self._set_close_state()
            self.lbl_message.setText(tr("Report generation canceled"))
        else:
            self.dialog_closed.emit()
            self.close()
