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
import io
import subprocess
import time
from PyQt4.QtCore import QSettings
from qgis.core import QgsVectorFileWriter

from processing.core.GeoAlgorithm import GeoAlgorithm
from processing.core.parameters import ParameterMultipleInput, ParameterVector, ParameterRaster, ParameterTableField, ParameterNumber, ParameterBoolean, ParameterSelection, ParameterString, ParameterFile, ParameterTable
from processing.core.outputs import OutputVector,OutputRaster, OutputFile, OutputDirectory
from processing.tools import dataobjects, vector

from processing.core.ProcessingConfig import ProcessingConfig
from processing.core.SilentProgress import SilentProgress
from processing.tools.system import getTempFilename, isWindows, isMac

from osgeo import osr
from time import gmtime, strftime

from ast import literal_eval


from PyQt4.QtGui import QIcon
from ..ChloeUtils import ChloeUtils
import tempfile
from processing.tools.system import isWindows


# Mother class
from .chloe_algorithm import CholeAlgorithm

# Master Dialog
from ..gui.FromCSVAlgorithmDialog import FromCSVAlgorithmDialog
from ..ChloeUtils import ASCOutputRaster


class FromCSVAlgorithm(CholeAlgorithm):
    """
    Algorithm generate ascii grid from csv
    """

    # Paramaters
    INPUT_FILE_CSV = 'INPUT_FILE_CSV'
    FIELDS         = 'FIELDS'
    N_COLS         = 'N_COLS'
    N_ROWS         = 'N_ROWS'
    XLL_CORNER     = 'XLL_CORNER'
    YLL_CORNER     = 'YLL_CORNER'
    CELL_SIZE      = 'CELL_SIZE'
    NODATA_VALUE   = 'NODATA_VALUE'

    SAVE_PROPERTIES = 'SAVE_PROPERTIES'
    OUTPUT_ASC      = 'OUTPUT_ASC'

    def getCustomParametersDialog(self):
        """Define Dialog associed with this algorithm"""
        return FromCSVAlgorithmDialog(self)

    def defineCharacteristics(self):
        """
        Algorithme variable and parameters parameters
        """
        CholeAlgorithm.defineCharacteristics(self)

        # The name/group that the user will see in the toolbox
        self.group      = 'generate ascii grid'
        self.i18n_group = self.tr('generate ascii grid')
        self.name       = 'from csv'
        self.i18n_name  = self.tr('from csv')

        # === INPUT PARAMETERS ===
        self.addParameter(ParameterTable(
            name=self.INPUT_FILE_CSV,
            description=self.tr('Input file csv')))


        self.addParameter(ParameterString(
            name=self.FIELDS, 
            description=self.tr('Fields selection'),
            default=''))

        self.addParameter(ParameterNumber(
            name=self.N_COLS,
            description=self.tr('Columns count'),
            minValue=0,
            default=100))

        self.addParameter(ParameterNumber(
            name=self.N_ROWS,
            description=self.tr('Rows count'),
            minValue=0,
            default=100))

        self.addParameter(ParameterNumber(
            name=self.XLL_CORNER,
            description=self.tr('X bottom left corner coordinate'),
            default=0.0))

        self.addParameter(ParameterNumber(
            name=self.YLL_CORNER,
            description=self.tr('Y bottom left corner coordinate'),
            default=0.0))

        self.addParameter(ParameterNumber(
            name=self.CELL_SIZE,
            description=self.tr('Cell size'),
            default=1.0))

        self.addParameter(ParameterNumber(
            name=self.NODATA_VALUE,
            description=self.tr('Value if no-data'),
            default=-1))


        self.addOutput(OutputFile(
            name=self.SAVE_PROPERTIES,
            description=self.tr('Properties file'),
            ext='properties'))
                                  
        # === OUTPUT PARAMETERS ===
        self.addOutput(ASCOutputRaster(
            name=self.OUTPUT_ASC,
            description=self.tr('Ouput Raster ascii')))


    def processAlgorithm(self, progress):
        """Here is where the processing itself takes place"""

        # === INPUT_LAYER
        # @inprogress test utf8 encoding strategy
        self.input_csv = self.getParameterValue(self.INPUT_FILE_CSV).encode('utf-8')

        self.variables    = self.getParameterValue(self.FIELDS)
        self.ncols        = self.getParameterValue(self.N_COLS)
        self.nrows        = self.getParameterValue(self.N_ROWS)
        self.xllcorner    = self.getParameterValue(self.XLL_CORNER)
        self.yllcorner    = self.getParameterValue(self.YLL_CORNER)
        self.cellsize     = self.getParameterValue(self.CELL_SIZE)
        self.nodata_value = self.getParameterValue(self.NODATA_VALUE)

        
        # === SAVE_PROPERTIES
        #f_save_properties = self.getParameterValue(self.SAVE_PROPERTIES)
        f_save_properties = self.getOutputValue(self.SAVE_PROPERTIES)
        if f_save_properties:
            self.f_path = f_save_properties
        else:
            if not self.f_path:
                self.f_path = getTempFilename(ext="properties")


        # === OUTPUT_ASC
        self.output_asc = self.getOutputValue(self.OUTPUT_ASC)

        # Constrution des chemins de sortie des fichiers
        base_in  = os.path.basename(self.input_csv)
        name_in  = os.path.splitext(base_in)[0]
        #ext_in  = os.path.splitext(base_in)[1]

        dir_out  = os.path.dirname(self.output_asc)
        base_out = os.path.basename(self.output_asc)
        name_out = os.path.splitext(base_out)[0]
        #ext_out = os.path.splitext(base_out)[1]

        # === Properties file
        self.createPropertiesTempFile() # Create Properties file (temp or chosed)

        # === CORE
        commands = self.getConsoleCommands()            # Get args command
        ChloeUtils.runChole(commands, progress)         # RUN

        # === Projection file
        f_prj = dir_out+os.sep+name_out+".prj"
        self.createProjectionFile(f_prj)

    def createPropertiesTempFile(self):
        """Create Properties File"""

        s_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
        with open(self.f_path,"w") as fd:
            fd.write("#"+s_time+"\n")
            fd.write("treatment=from csv\n")
            fd.write("visualize_ascii=false\n")
            fd.write( ChloeUtils.formatString('input_csv='+self.input_csv+"\n",isWindows()))  
            fd.write( ChloeUtils.formatString('output_asc='+self.output_asc+"\n",isWindows()))
            fd.write("variables={"   +     self.variables     +"}\n")
            fd.write("ncols="        + str(self.ncols)        + "\n")
            fd.write("nrows="        + str(self.nrows)        + "\n")
            fd.write("xllcorner="    + str(self.xllcorner)    + "\n")
            fd.write("yllcorner="    + str(self.yllcorner)    + "\n")
            fd.write("cellsize="     + str(self.cellsize)     + "\n")
            fd.write("nodata_value=" + str(self.nodata_value) + "\n")

