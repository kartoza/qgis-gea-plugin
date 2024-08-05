# -*- coding: utf-8 -*-
"""
    Plugin utilities
"""

import os
from pathlib import Path

from qgis.PyQt import QtCore, QtGui
from qgis.core import (
    Qgis,
    QgsMessageLog,
)

from .definitions.defaults import SITE_REPORT_TEMPLATE_NAME


def log(
    message: str,
    name: str = "qgis_gea",
    info: bool = True,
    notify: bool = True,
):
    """Logs the message into QGIS logs using qgis_cplus as the default
    log instance.
    If notify_user is True, user will be notified about the log.

    :param message: The log message
    :type message: str

    :param name: Name of te log instance, qgis_cplus is the default
    :type message: str

    :param info: Whether the message is about info or a
    warning
    :type info: bool

    :param notify: Whether to notify user about the log
    :type notify: bool
    """
    level = Qgis.Info if info else Qgis.Warning
    QgsMessageLog.logMessage(
        message,
        name,
        level=level,
        notifyUser=notify,
    )

def tr(message):
    """Get the translation for a string using Qt translation API.
    We implement this ourselves since we do not inherit QObject.

    :param message: String for translation.
    :type message: str, QString

    :returns: Translated version of message.
    :rtype: QString
    """
    # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
    return QtCore.QCoreApplication.translate("QgisGea", message)


def clean_filename(filename):
    """Creates a safe filename by removing operating system
    invalid filename characters.

    :param filename: File name
    :type filename: str

    :returns A clean file name
    :rtype str
    """
    characters = " %:/,\[]<>*?"

    for character in characters:
        if character in filename:
            filename = filename.replace(character, "_")

    return filename

def create_dir(directory: str, log_message: str = ""):
    """Creates new file directory if it doesn't exist"""
    p = Path(directory)
    if not p.exists():
        try:
            p.mkdir()
        except (FileNotFoundError, OSError):
            log(log_message)


def animation_state_change(value):
    log(f"{value}")
    pass


class FileUtils:
    """
    Provides functionality for commonly used file- or dir-related
    operations.
    """

    @staticmethod
    def plugin_dir() -> str:
        """Returns the root directory of the plugin.

        :returns: Root directory of the plugin.
        :rtype: str
        """
        return os.path.join(os.path.dirname(os.path.realpath(__file__)))

    @staticmethod
    def report_template_path(file_name) -> str:
        """Get the absolute path to the template file with the given name.
        Caller needs to verify that the file actually exists.

        :param file_name: Template file name including the extension.
        :type file_name: str

        :returns: The absolute path to the template file with the given name.
        :rtype: str
        """
        absolute_path = f"{FileUtils.plugin_dir()}/data/report_templates/{file_name}"

        return os.path.normpath(absolute_path)

    @staticmethod
    def site_report_template_path() -> str:
        """Gets the path to the report template
        (*.qpt) file.

        :returns: Returns the absolute path to the
        report template (*.qpt) file.
        :rtype: str
        """
        return FileUtils.report_template_path(SITE_REPORT_TEMPLATE_NAME)

    @staticmethod
    def get_icon(file_name: str) -> QtGui.QIcon:
        """Creates an icon based on the icon name in the 'icons' folder.

        :param file_name: File name which should include the extension.
        :type file_name: str

        :returns: Icon object matching the file name.
        :rtype: QtGui.QIcon
        """
        icon_path = os.path.normpath(f"{FileUtils.plugin_dir()}/icons/{file_name}")

        if not os.path.exists(icon_path):
            return QtGui.QIcon()

        return QtGui.QIcon(icon_path)
