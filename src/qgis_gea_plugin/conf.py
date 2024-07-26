# -*- coding: utf-8 -*-
"""
    Handles storage and retrieval of the plugin QgsSettings.
"""

import contextlib
import dataclasses
import datetime
import enum
import json
import os.path
import uuid
from pathlib import Path

from qgis.PyQt import QtCore
from qgis.core import QgsSettings

from .utils import log


@contextlib.contextmanager
def qgis_settings(group_root: str, settings=None):
    """Context manager to help defining groups when creating QgsSettings.

    :param group_root: Name of the root group for the settings
    :type group_root: str

    :param settings: QGIS settings to use
    :type settings: QgsSettings

    :yields: Instance of the created settings
    :ytype: QgsSettings
    """
    if settings is None:
        settings = QgsSettings()
    settings.beginGroup(group_root)
    try:
        yield settings
    finally:
        settings.endGroup()


class Settings(enum.Enum):
    """Plugin settings names"""

    HISTORICAL_VIEW = "historical"
    NICFI_VIEW = "nicfi"

    SITE_REFERENCE = "site_reference"
    SITE_VERSION = "site_version"
    REPORT_AUTHOR = "report_author"
    REPORT_COUNTRY = "report_country"
    PROJECT_INCEPTION_DATE = "project_inception_date"

    PROJECT_FOLDER = 'project_folder'


class SettingsManager(QtCore.QObject):
    """Manages saving/loading settings for the plugin in QgsSettings."""

    BASE_GROUP_NAME: str = "qgis_gea_plugin"

    settings = QgsSettings()

    scenarios_settings_updated = QtCore.pyqtSignal()
    priority_layers_changed = QtCore.pyqtSignal()
    settings_updated = QtCore.pyqtSignal([str, object], [Settings, object])

    def set_value(self, name: str, value):
        """Adds a new setting key and value on the plugin specific settings.

        :param name: Name of setting key
        :type name: str

        :param value: Value of the setting
        :type value: Any
        """
        self.settings.setValue(f"{self.BASE_GROUP_NAME}/{name}", value)
        if isinstance(name, Settings):
            name = name.value

        self.settings_updated.emit(name, value)

    def get_value(self, name: str, default=None, setting_type=None):
        """Gets value of the setting with the passed name.

        :param name: Name of setting key
        :type name: str

        :param default: Default value returned when the setting key does not exist
        :type default: Any

        :param setting_type: Type of the store setting
        :type setting_type: Any

        :returns: Value of the setting
        :rtype: Any
        """
        if setting_type:
            return self.settings.value(
                f"{self.BASE_GROUP_NAME}/{name}", default, setting_type
            )
        return self.settings.value(f"{self.BASE_GROUP_NAME}/{name}", default)

    def find_settings(self, name):
        """Returns the plugin setting keys from the
         plugin root group that matches the passed name

        :param name: Setting name to search for
        :type name: str

        :returns result: List of the matching settings names
        :rtype result: list
        """

        result = []
        with qgis_settings(f"{self.BASE_GROUP_NAME}") as settings:
            for settings_name in settings.childKeys():
                if name in settings_name:
                    result.append(settings_name)
        return result

    def remove(self, name):
        """Remove the setting with the specified name.

        :param name: Name of the setting key
        :type name: str
        """
        self.settings.remove(f"{self.BASE_GROUP_NAME}/{name}")

    def delete_settings(self):
        """Deletes the all the plugin settings."""
        self.settings.remove(f"{self.BASE_GROUP_NAME}")


settings_manager = SettingsManager()
