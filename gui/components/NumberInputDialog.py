# -*- coding: utf-8 -*-

#####################################################################################################
# Chloe - landscape metrics
#
# Copyright 2018 URCAUE-Nouvelle Aquitaine
# Author(s) J-C. Naud, O. Bedel - Alkante (http://www.alkante.com) ;
#           H. Boussard - INRA UMR BAGAP (https://www6.rennes.inra.fr/sad)
# 
# Created on Mon Oct 22 2018
# This file is part of Chloe - landscape metrics.
# 
# Chloe - landscape metrics is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Chloe - landscape metrics is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Chloe - landscape metrics.  If not, see <http://www.gnu.org/licenses/>.
#####################################################################################################

import os

from qgis.PyQt import uic
from qgis.PyQt.QtWidgets import QDialog, QTreeWidgetItem, QMessageBox
from qgis.core import QgsRasterLayer

from qgis.utils import iface
from processing.tools import dataobjects

pluginPath = os.path.split(os.path.dirname(__file__))[0]
WIDGET, BASE = uic.loadUiType(
    os.path.join(pluginPath, 'ui', 'DlgNumberInput.ui'))


class NumberInputDialog(BASE, WIDGET):

    def __init__(self, isInteger):
        super(NumberInputDialog, self).__init__(None)
        self.setupUi(self)

        if hasattr(self.leFormula, 'setPlaceholderText'):
            self.leFormula.setPlaceholderText(
                self.tr('[Enter your formula here]'))

        self.treeValues.doubleClicked.connect(self.addValue)

        self.value = None
        self.isInteger = isInteger

        if not self.isInteger:
            self.lblWarning.hide()

        self.fillTree()

    def fillTree(self):
        layersItem = QTreeWidgetItem()
        layersItem.setText(0, self.tr('Values from data layers extents'))
        self.treeValues.addTopLevelItem(layersItem)
        layers = dataobjects.getAllLayers()
        for layer in layers:
            layerItem = QTreeWidgetItem()
            layerItem.setText(0, unicode(layer.name()))
            layerItem.addChild(TreeValueItem(self.tr('Min X'),
                                             layer.extent().xMinimum()))
            layerItem.addChild(TreeValueItem(self.tr('Max X'),
                                             layer.extent().xMaximum()))
            layerItem.addChild(TreeValueItem(self.tr('Min Y'),
                                             layer.extent().yMinimum()))
            layerItem.addChild(TreeValueItem(self.tr('Max Y'),
                                             layer.extent().yMaximum()))
            if isinstance(layer, QgsRasterLayer):
                cellsize = (layer.extent().xMaximum()
                            - layer.extent().xMinimum()) / layer.width()
                layerItem.addChild(TreeValueItem(self.tr('Cellsize'),
                                                 cellsize))
            layersItem.addChild(layerItem)

        layersItem = QTreeWidgetItem()
        layersItem.setText(0, self.tr('Values from raster layers statistics'))
        self.treeValues.addTopLevelItem(layersItem)
        layers = dataobjects.getRasterLayers()
        for layer in layers:
            for i in range(layer.bandCount()):
                stats = layer.dataProvider().bandStatistics(i + 1)
                layerItem = QTreeWidgetItem()
                layerItem.setText(0, unicode(layer.name()))
                layerItem.addChild(TreeValueItem(self.tr('Mean'), stats.mean))
                layerItem.addChild(TreeValueItem(self.tr('Std. deviation'),
                                                 stats.stdDev))
                layerItem.addChild(TreeValueItem(self.tr('Max value'),
                                                 stats.maximumValue))
                layerItem.addChild(TreeValueItem(self.tr('Min value'),
                                                 stats.minimumValue))
                layersItem.addChild(layerItem)

        canvasItem = QTreeWidgetItem()
        canvasItem.setText(0, self.tr('Values from QGIS map canvas'))
        self.treeValues.addTopLevelItem(canvasItem)
        extent = iface.mapCanvas().extent()
        extentItem = QTreeWidgetItem()
        extentItem.setText(0, self.tr('Current extent'))
        extentItem.addChild(TreeValueItem(self.tr('Min X'), extent.xMinimum()))
        extentItem.addChild(TreeValueItem(self.tr('Max X'), extent.xMaximum()))
        extentItem.addChild(TreeValueItem(self.tr('Min Y'), extent.yMinimum()))
        extentItem.addChild(TreeValueItem(self.tr('Max Y'), extent.yMaximum()))
        canvasItem.addChild(extentItem)

        extent = iface.mapCanvas().fullExtent()
        extentItem = QTreeWidgetItem()
        extentItem.setText(0,
                           self.tr('Full extent of all layers in map canvas'))
        extentItem.addChild(TreeValueItem(self.tr('Min X'), extent.xMinimum()))
        extentItem.addChild(TreeValueItem(self.tr('Max X'), extent.xMaximum()))
        extentItem.addChild(TreeValueItem(self.tr('Min Y'), extent.yMinimum()))
        extentItem.addChild(TreeValueItem(self.tr('Max Y'), extent.yMaximum()))
        canvasItem.addChild(extentItem)

    def addValue(self):
        item = self.treeValues.currentItem()
        if isinstance(item, TreeValueItem):
            formula = self.leFormula.text() + ' ' + unicode(item.value)
            self.leFormula.setText(formula.strip())

    def accept(self):
        try:
            self.value = float(eval(unicode(self.leFormula.text())))
            if self.isInteger:
                self.value = int(round(self.value))
            QDialog.accept(self)
        except:
            QMessageBox.critical(self, self.tr('Wrong expression'),
                                 self.tr('The expression entered is not correct'))

    def reject(self):
        self.value = None
        QDialog.reject(self)


class TreeValueItem(QTreeWidgetItem):

    def __init__(self, name, value):
        QTreeWidgetItem.__init__(self)
        self.value = value
        self.setText(0, name + ': ' + unicode(value))
