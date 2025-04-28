"""
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os.path
import os
import tempfile
import datetime
import logging

from typing import Optional
from qgis.core import QgsSettings, Qgis
from qgis.PyQt.QtCore import QTranslator, QCoreApplication, Qt
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QMessageBox, QAction, QPushButton

# Initialize Qt resources from file resources.py
from .resources import *
from .utils import log

from .gui.qgis_gea import QgisGeaPlugin

# Set up logging - see utilites.py log_message for usage
# use log_message instead of QgsMessageLog.logMessage everywhere please....
temp_dir = tempfile.gettempdir()
# Use a timestamp to ensure unique log file names
datestamp = datetime.datetime.now().strftime("%Y%m%d")
log_path_env = os.getenv("GEA_LOG", 0)
if log_path_env:
    log_file_path = log_path_env
else:
    log_file_path = os.path.join(temp_dir, f"geest_logfile_{datestamp}.log")
logging.basicConfig(
    filename=log_file_path,
    filemode="a",  # Append mode
    format="%(asctime)s [%(levelname)s] %(message)s",
    level=logging.DEBUG,
)
date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
log(f"»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»")
log(f"GEA Pluging started at {date}")
log(f"Logging output to: {log_file_path}")
log(f"log_path_env: {log_path_env}")
log(f"»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»»")


class QgisGea:
    """QGIS GEA Plugin Implementation."""

    def __init__(self, iface):
        self.iface = iface

        debug_env = int(os.getenv("GEA_DEBUG", 0))
        if debug_env:
            self.debug()

        self.plugin_dir = os.path.dirname(__file__)
        locale = QgsSettings().value("locale/userLocale")[0:2]
        locale_path = os.path.join(
            self.plugin_dir, "i18n", "QgisGeaPlugin{}.qm".format(locale)
        )

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr("&EPAL - Eligible Project Area Locator.")
        self.pluginIsActive = False
        self.toolbar = self.iface.addToolBar(
            "Open EPAL - Eligible Project Area Locator"
        )
        self.toolbar.setObjectName("EPAL - Eligible Project Area Locator.")

        self.main_widget = QgisGeaPlugin(
            iface=self.iface, parent=self.iface.mainWindow()
        )

    def debug(self):
        """
        Enters debug mode.
        Shows a message to attach a debugger to the process.
        """

        self.display_information_message_box(
            title="GEA",
            message="Close this dialog then open VSCode and start your debug client.",
        )
        import multiprocessing  # pylint: disable=import-outside-toplevel

        if multiprocessing.current_process().pid > 1:
            import debugpy  # pylint: disable=import-outside-toplevel

            debugpy.listen(("0.0.0.0", 9000))
            debugpy.wait_for_client()
            self.display_information_message_bar(
                title="GEA",
                message="Visual Studio Code debugger is now attached on port 9000",
            )
            self.debug_running = True

    def display_information_message_bar(
        self,
        title: Optional[str] = None,
        message: Optional[str] = None,
        more_details: Optional[str] = None,
        button_text: str = "Show details ...",
        duration: int = 8,
    ) -> None:
        """
        Display an information message bar.
        :param title: The title of the message bar.
        :param message: The message inside the message bar.
        :param more_details: The message inside the 'Show details' button.
        :param button_text: Text of the button if 'more_details' is not empty.
        :param duration: The duration for the display, default is 8 seconds.
        """
        self.iface.messageBar().clearWidgets()
        widget = self.iface.messageBar().createMessage(title, message)

        if more_details:
            button = QPushButton(widget)
            button.setText(button_text)
            button.pressed.connect(
                lambda: self.display_information_message_box(
                    title=title, message=more_details
                )
            )
            widget.layout().addWidget(button)

        self.iface.messageBar().pushWidget(widget, Qgis.Info, duration)

    def display_information_message_box(
        self, parent=None, title: Optional[str] = None, message: Optional[str] = None
    ) -> None:
        """
        Display an information message box.
        :param title: The title of the message box.
        :param message: The message inside the message box.
        """
        QMessageBox.information(parent, title, message)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.
        We implement this ourselves since we do not inherit QObject.
        :param message: String for translation.
        :type message: str, QString
        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate(
            "EPAL - Eligible Project Area Locator", message
        )

    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_web_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None,
    ):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_web_menu: Flag indicating whether the action
            should also be added to the web menu. Defaults to True.
        :type add_to_web_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)

        if add_to_web_menu:
            self.iface.addPluginToWebMenu(self.menu, action)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = ":/plugins/qgis_gea_plugin/icon.svg"
        self.add_action(
            icon_path,
            text=self.tr("Open Plugin"),
            callback=self.run,
            parent=self.iface.mainWindow(),
        )

    def onClosePlugin(self):
        """Cleanup necessary items here when plugin widget is closed"""
        self.pluginIsActive = False

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        try:
            for action in self.actions:
                self.iface.removePluginMenu(
                    self.tr("&EPAL - Eligible Project Area Locator."), action
                )
                self.iface.removePluginWebMenu(
                    self.tr("&EPAL - Eligible Project Area Locator."), action
                )
                self.iface.removeToolBarIcon(action)

        except Exception as e:
            pass

    def run(self):
        if self.main_widget == None:
            self.main_widget = QgisGeaPlugin(
                iface=self.iface, parent=self.iface.mainWindow()
            )

        self.iface.addDockWidget(Qt.RightDockWidgetArea, self.main_widget)
        self.main_widget.show()

        if not self.pluginIsActive:
            self.pluginIsActive = True
