# glenoidMouldDesigner.py copyright 2003 Charl P. Botha http://cpbotha.net/
# $Id: glenoidMouldDesignFLT.py,v 1.2 2003/03/18 17:48:40 cpbotha Exp $
# dscas3 module that designs glenoid moulds by making use of insertion
# axis and model of scapula

# this module doesn't satisfy the event handling requirements of DSCAS3 yet
# if you call update on the output PolyData, this module won't know to
# execute, because at the moment main processing takes place in Python-land
# this will be so at least until we convert the processing to a vtkSource
# child that has the PolyData as output or until we fake it with Observers
# This is not critical.

from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import vtk
from wxPython.wx import *

class glenoidMouldDesignFLT(moduleBase, noConfigModuleMixin):

    def __init__(self, moduleManager):
        
        # call parent constructor
        moduleBase.__init__(self, moduleManager)
        # and mixin
        noConfigModuleMixin.__init__(self)

        self._inputPolyData = None
        self._inputPoints = None
        self._inputPointsOID = None
        self._giaProximal = None
        self._giaDistal = None
        self._outputPolyData = vtk.vtkPolyData()

        # create the frame and display it proudly!
        self._createViewFrame('Glenoid Mould Designer View',
                              {'Output Polydata': self._outputPolyData})
        self._viewFrame.Show(True)

    def close(self):
        # disconnect all inputs
        self.setInput(0, None)
        self.setInput(1, None)
        # take care of critical instances
        self._outputPolyData = None
        # mixin close
        noConfigModuleMixin.close(self)

    def getInputDescriptions(self):
        return('Scapula vtkPolyData', 'Insertion axis (points)')

    def setInput(self, idx, inputStream):
        if idx == 0:
            # will work for None and not-None
            self._inputPolyData = inputStream
        else:
            if inputStream is not self._inputPoints:
                if self._inputPoints:
                    self._inputPoints.removeObserver(self._inputPointsOID)

                if inputStream:
                    self._inputPointsOID = inputStream.addObserver(
                        self._inputPointsObserver)

                self._inputPoints = inputStream

                # initial update
                self._inputPointsObserver(None)
                    

    def getOutputDescriptions(self):
        return ('Mould design (vtkPolyData)',) # for now

    def getOutput(self):
        return self._outputPolyData

    def logicToConfig(self):
        pass

    def configToLogic(self):
        pass

    def viewToConfig(self):
        pass

    def configToView(self):
        pass

    def executeModule(self):
        if self._giaDistal and self._giaProximal and self._inputPolyData:
            # construct eight planes with the insertion axis as mid-line
            # the planes should go somewhat further proximally than the
            # proximal insertion axis point

            pass # a stone (ha ha)
            

    def view(self):
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

    def _inputPointsObserver(self, obj):
        # extract a list from the input points
        if self._inputPoints:
            # extract the two points with labels 'GIA Proximal'
            # and 'GIA Distal'
            
            giaProximal = [i['world'] for i in self._inputPoints if i['name'] == 'GIA Proximal']

            giaDistal = [i['world'] for i in self._inputPoints if i['name'] == 'GIA Distal']

            if giaProximal and giaDistal:
                # we only apply these points to our internal parameters
                # if they're valid and if they're new
                self._giaProximal = giaProximal[0]
                self._giaDistal = giaDistal[0]
