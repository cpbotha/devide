# glenoidMouldDesigner.py copyright 2003 Charl P. Botha http://cpbotha.net/
# $Id: glenoidMouldDesigner.py,v 1.1 2003/03/17 16:00:55 cpbotha Exp $
# dscas3 module that designs glenoid moulds by making use of insertion
# axis and model of scapula

from moduleBase import moduleBase
import vtk
from wxPython.wx import *

class glenoidMouldDesigner(moduleBase):

    def __init__(self, moduleManager):
        
        # call parent constructor
        moduleBase.__init__(self, moduleManager)

    def close(self):
        pass

    def getInputDescriptions(self):
        return('Scapula vtkPolyData', 'Insertion axis (points)')

    def setInput(self, idx, inputStream):
        if idx == 0:
            # will work for None and not-None
            self._imageCast.SetInput(inputStream)
        else:
            if inputStream is None:
                if self._inputPoints:
                    self._inputPoints.removeObserver(self._inputPointsObserver)
                
            else:
                inputStream.addObserver(self._inputPointsObserver)

            self._inputPoints = inputStream

            # initial update
            self._inputPointsObserver(self._inputPoints)

    def getOutputDescriptions(self):
        return ('Mould design (vtkPolyData)',) # for now

    def getOutput(self):
        pass

    def logicToConfig(self):
        pass

    def configToLogic(self):
        pass

    def viewToConfig(self):
        pass

    def configToView(self):
        pass

    def executeModule(self):
        pass

    def view(self):
        pass
