# landmarkTransform.py copyright (c) 2003 by Charl P. Botha <cpbotha@ieee.org>
# $Id: landmarkTransform.py,v 1.2 2003/10/15 12:59:06 cpbotha Exp $
# see module documentation

# TODO:
# * make mode configurable by the user

import genUtils
from moduleBase import moduleBase
from moduleMixins import noConfigModuleMixin
import moduleUtils
import wx
import vtk

class landmarkTransform(moduleBase, noConfigModuleMixin):
    """The landmarkTransform will calculate a 4x4 linear transform that maps
    from a set of source landmarks to a set of target landmarks.

    The mapping is optimised with a least-squares metric.  You have to supply
    two sets of points, all points in the source set have to be named
    'Source' and all the points in the target set have to be named 'Target'.

    This module will supply a vtkTransform at its first output and a 4x4
    vtk Matrix at its second output.  By connecting the vtkTransform to
    a transformPolyData module, you'll be able to perform the actual
    transformation.
    """

    def __init__(self, moduleManager):
        moduleBase.__init__(self, moduleManager)
        noConfigModuleMixin.__init__(self)

        self._inputPoints = None
        self._inputPointsOID = -1
        self._sourceLandmarks = None
        self._targetLandmarks = None

        self._landmarkTransform = vtk.vtkLandmarkTransform()
        # make this configurable!
        self._landmarkTransform.SetModeToRigidBody()

        self._viewFrame = self._createViewFrame(
            {'vtkLandmarkTransform': self._landmarkTransform})

        self.configToLogic()
        self.syncViewWithLogic()

    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.getInputDescriptions())):
            self.setInput(inputIdx, None)

        # this will take care of all display thingies
        noConfigModuleMixin.close(self)
        
        # get rid of our reference
        del self._landmarkTransform

    def getInputDescriptions(self):
        return ('Source and Target Points',)

    def setInput(self, idx, inputStream):
        if inputStream is not self._inputPoints:

            if self._inputPoints:
                self._inputPoints.removeObserver(self._inputPointsOID)

            if inputStream:
                self._inputPointsOID = inputStream.addObserver(
                    self._observerInputPoints)

            self._inputPoints = inputStream

            # initial update
            self._observerInputPoints(None)

    def getOutputDescriptions(self):
        return (self._landmarkTransform.GetClassName(),
                self._landmarkTransform.GetMatrix().GetClassName())

    def getOutput(self, idx):
        if idx == 0:
            return self._landmarkTransform
        else:
            return self._landmarkTransform.GetMatrix()

    def logicToConfig(self):
        pass
    
    def configToLogic(self):
        pass
    
    def viewToConfig(self):
        pass

    def configToView(self):
        pass
    
    def executeModule(self):
        self._landmarkTransform.Update()

    def view(self, parent_window=None):
        # if the window was visible already. just raise it
        if not self._viewFrame.Show(True):
            self._viewFrame.Raise()

    def _observerInputPoints(self, obj):
        # the points have changed, let's see if they really have

        if not self._inputPoints:
            return
        
        tempSourceLandmarks = [i['world'] for i in self._inputPoints
                               if i['name'].lower() == 'source']
        tempTargetLandmarks = [i['world'] for i in self._inputPoints
                               if i['name'].lower() == 'target']

        if tempSourceLandmarks != self._sourceLandmarks or \
           tempTargetLandmarks != self._targetLandmarks:

            if len(tempSourceLandmarks) != len(tempTargetLandmarks):
                md= wx.MessageDialog(
                    self._moduleManager.getModuleViewParentWindow(),
                    "landmarkTransform: Your 'Source' landmark set and "
                    "'Target' landmark set should be of equal size.",
                    "Landmark Set Size",
                    wx.ICON_INFORMATION | wx.OK)
                
                md.ShowModal()

            else:
                self._sourceLandmarks = tempSourceLandmarks
                self._targetLandmarks = tempTargetLandmarks

                sourceLandmarks = vtk.vtkPoints()
                targetLandmarks = vtk.vtkPoints()
                landmarkPairs = ((self._sourceLandmarks, sourceLandmarks),
                                 (self._targetLandmarks, targetLandmarks))
                
                for lmp in landmarkPairs:
                    lmp[1].SetNumberOfPoints(len(lmp[0]))
                    for pointIdx in range(len(lmp[0])):
                        lmp[1].SetPoint(pointIdx, lmp[0][pointIdx])
                                 
                self._landmarkTransform.SetSourceLandmarks(sourceLandmarks)
                self._landmarkTransform.SetTargetLandmarks(targetLandmarks)
                
        
        
