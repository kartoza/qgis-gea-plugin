# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QgisGea

 A QGIS plugin that enables usage of the EPAL afforestation data visualization.
                             -------------------
        begin                : 2024-06-27
        copyright            : (C) 2024 by Kartoza
        email                : info@kartoza.com
        git sha              : $Format:%H$
 ***************************************************************************/
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 This script initializes the plugin, making it known to QGIS.
"""


# noinspection PyPep8Naming
def classFactory(iface):  # pylint: disable=invalid-name
    """Load QgisGea class
    :param iface: A QGIS interface instance.
    :type iface: QgsInterface
    """
    #
    from .main import QgisGea

    return QgisGea(iface)
