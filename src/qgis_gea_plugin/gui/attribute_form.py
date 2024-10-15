# -*- coding: utf-8 -*-
"""
Dialog for showing the attribute form dialog.
"""

import os
from datetime import datetime


from qgis.PyQt import QtCore, QtGui, QtWidgets

from qgis.PyQt.uic import loadUiType

from qgis.core import (
    Qgis,
    QgsEditorWidgetSetup,
    QgsField,
    QgsFillSymbol,
    QgsInterval,
    QgsLayerTreeGroup,
    QgsPalLayerSettings,
    QgsProject,
    QgsTextFormat,
    QgsTemporalNavigationObject,
    QgsUnitTypes,
    QgsVectorFileWriter,
    QgsVectorLayer,
    QgsVectorLayerSimpleLabeling
)

from ..utils import tr

from ..definitions.defaults import PROJECT_AREAS

WidgetUi, _ = loadUiType(
    os.path.join(os.path.dirname(__file__), "../ui/attribute_form.ui")
)


class AttributeForm(QtWidgets.QDialog, WidgetUi):
    """Dialog for showing the attribute form."""

    def __init__(
        self,
        layer,
        parent=None
    ):
        super().__init__(
            parent,
            QtCore.Qt.WindowMinimizeButtonHint | QtCore.Qt.WindowCloseButtonHint
        )
        self.setupUi(self)
        self.layer = layer

        self.project_cmb_box.addItems(PROJECT_AREAS)

        self.buttonBox.button(QtWidgets.QDialogButtonBox.Ok).setText("Save")

        self.buttonBox.button(
            QtWidgets.QDialogButtonBox.Ok
        ).setEnabled(False)

        ok_signals = [
            self.report_author_le.textChanged,
            self.project_cmb_box.currentIndexChanged,
        ]
        for signal in ok_signals:
            signal.connect(self.update_ok_buttons)


    def update_ok_buttons(self):
        """ Responsible for changing the state of the
         attribute form dialog OK button.
        """
        enabled_state = self.report_author_le.text() != "" and \
                        self.project_cmb_box.currentText() != ""
        self.buttonBox.button(
            QtWidgets.QDialogButtonBox.Ok).setEnabled(enabled_state)


    def accept(self):

        self.layer.startEditing()

        fields = self.layer.fields()

        new_fields = ['author', 'project','area (ha)']
        attributes = []

        for field in new_fields:
            if fields.indexFromName(field) != -1:
                reply = QtWidgets.QMessageBox.warning(
                    self,
                    tr("QGIS GEA PLUGIN"),
                    tr('Field "{}" already exists in the layer.'
                       'Do you want to proceed and overwrite it?').
                    format(field),

                    QtWidgets.QMessageBox.Yes,
                    QtWidgets.QMessageBox.No,
                )
                if reply == QtWidgets.QMessageBox.Yes:
                    continue
                else:
                    self.layer.commitChanges()
                    return
            else:
                # If not found in the layer add it to the list
                # of attributes that will be added to layer fields later
                attributes.append(QgsField(
                    field,
                    QtCore.QVariant.String)
                )

        provider = self.layer.dataProvider()
        provider.addAttributes(attributes)

        self.layer.updateFields()

        features = self.layer.getFeatures()
        feature = next(features, None)
        while feature is not None:
            # Set attribute values
            feature_area = "-"
            geom = feature.geometry()
            if geom is not None and geom.isGeosValid():
                area = geom.area() / 10000
                feature_area = f"{area:,.2f}"

            feature.setAttribute(
                "author",
                self.report_author_le.text()
            )
            feature.setAttribute(
                "project",
                self.project_cmb_box.currentText()
            )
            feature.setAttribute("area (ha)", feature_area)

            self.layer.updateFeature(feature)
            # Retrieve the next feature
            feature = next(features, None)

        self.layer.commitChanges()
        self.layer.setReadOnly(True)

        super().accept()

