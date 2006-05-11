# $Id$

"""Collection of module utility functions.

@author: Charl P. Botha <http://cpbotha.net/>
"""

import wx
from external.vtkPipeline.vtkPipeline import \
     vtkPipelineBrowser
from external.vtkPipeline.ConfigVtkObj import ConfigVtkObj
import resources.graphics.images


def createECASButtons(d3module, viewFrame, viewFramePanel,
                      executeDefault=True):
    """Add Execute, Close, Apply and Sync buttons to the viewFrame.

    d3module is the module for which these buttons are being added.
    viewFrame is the actual dialog frame.
    viewFramePanel is the top-level panel in the frame, i.e. the panel
    completely filling the top-level sizer.

    IMPORTANT: viewFrame must have a top-level sizer that contains ONLY
    the viewFramePanel.  This is the default for wxGlade created dialogs
    with a top-level panel.  The viewFramePanel's sizer must be a
    vertical box sizer that contains ANOTHER sizer with a 7 pixel border
    all around.  These ECAS buttons will be in a sibling sizer to that
    ANOTHER sizer.

    The Execute, Close, Apply and Sync buttons will be created with the
    viewFramePanel as their parent.  They will be added to a horizontal sizer
    which will then be added to viewFramePanel.GetSizer().  The viewFramePanel
    sizer will then be used to fit the viewFramePanel.

    After this, the viewFrame.GetSizer() will be used to fit and layout the
    frame itself.

    The buttons will be assigned to executeButton, closeButton, applyButton
    and syncButton bindings in viewFrame, with corresponding ids:
    executeButtonId, closeButtonId, etc.

    After this call, you should use bindECAS to bind the correct events to
    these buttons.
    """

    # create the buttons
    viewFrame.executeButtonId = wx.NewId()
    viewFrame.executeButton = wx.Button(viewFramePanel,
                                        viewFrame.executeButtonId,
                                        "Execute")
    viewFrame.executeButton.SetToolTip(wx.ToolTip(
        "Apply any changes, then execute the whole network."))

    viewFrame.closeButtonId = wx.NewId()
    viewFrame.closeButton = wx.Button(viewFramePanel,
                                      viewFrame.closeButtonId,
                                      "Close")
    viewFrame.closeButton.SetToolTip(wx.ToolTip(
        "Close the dialog window."))

    viewFrame.applyButtonId = wx.NewId()
    viewFrame.applyButton = wx.Button(viewFramePanel,
                                      viewFrame.applyButtonId,
                                      "Apply")
    viewFrame.applyButton.SetToolTip(wx.ToolTip(
        "Modify configuration of underlying system as specified by "
        "this dialogue."))

    viewFrame.syncButtonId = wx.NewId()
    viewFrame.syncButton = wx.Button(viewFramePanel,
                                     viewFrame.syncButtonId,
                                     "Sync")
    viewFrame.syncButton.SetToolTip(wx.ToolTip(
        "Synchronise dialogue with configuration of underlying system."))

    viewFrame.helpButtonId = wx.NewId()
    viewFrame.helpButton = wx.Button(viewFramePanel,
                                     viewFrame.helpButtonId,
                                     "Help")
    viewFrame.helpButton.SetToolTip(wx.ToolTip(
        "Show help on this module."))
    


    # add them to their own sizer, each with a border of 4 pixels on the right
    buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
    for button in (viewFrame.executeButton, viewFrame.closeButton,
                   viewFrame.applyButton, viewFrame.syncButton):
        buttonSizer.Add(button, 0, wx.RIGHT, 7)

    # except for the right-most button, which has no border
    buttonSizer.Add(viewFrame.helpButton, 0)

    # add the buttonSizer to the viewFramePanel sizer with a border of 7 pixels
    # on the left, right and bottom... remember, this is below a sizer with
    # a 7 pixel border all around!
    # (we do it with 8, because the default execute button is quite big!)
    viewFramePanel.GetSizer().Add(buttonSizer, 0,
                                  wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.ALIGN_RIGHT, 8)
    # force the sizer to calculate new layout with all children (because
    # we've just added something)
    viewFramePanel.GetSizer().Layout()
    # fit and setsizehints (autolayout should remain on)    
    viewFramePanel.GetSizer().Fit(viewFramePanel)
    viewFramePanel.GetSizer().SetSizeHints(viewFramePanel)

    # now we have to get the top level sizer to do its thing
    # WORKAROUND - if we don't remove and add, the
    # viewFrame.GetSizer().Layout() below doesn't do anything.
    viewFrame.GetSizer().Remove(viewFramePanel)
    viewFrame.GetSizer().Add(viewFramePanel, 1, wx.EXPAND, 0)
    # WORKAROUND ENDS
    viewFrame.GetSizer().Layout() # this should update the minimum size
    viewFrame.GetSizer().Fit(viewFrame)
    viewFrame.GetSizer().SetSizeHints(viewFrame)

    # EVENT BINDINGS
    mm = d3module._moduleManager

    # call back into the graphEditor, if it exists
    ge = mm._devide_app.get_interface()._graphEditor    
    def helpModule(dvModule):
        if ge:
            ge._helpModule(dvModule)
    
    # execute
    wx.EVT_BUTTON(viewFrame, viewFrame.executeButtonId,
               lambda e: (mm.applyModuleViewToLogic(d3module),
                          mm.executeNetwork(d3module)))
    
    # close
    wx.EVT_BUTTON(viewFrame, viewFrame.closeButtonId,
               lambda e, vf=viewFrame: vf.Show(False))
    
    # apply
    wx.EVT_BUTTON(viewFrame, viewFrame.applyButtonId,
               lambda e: mm.applyModuleViewToLogic(d3module))
    
    # sync
    wx.EVT_BUTTON(viewFrame, viewFrame.syncButtonId,
               lambda e: mm.syncModuleViewWithLogic(d3module))

    # help
    wx.EVT_BUTTON(viewFrame, viewFrame.helpButtonId,
               lambda e: helpModule(d3module))

    # make sure that execute is the default button
    # unless the user specifies otherwise - in frames where we make
    # use of an introspection shell, we don't want Enter to execute...
    if executeDefault:
        viewFrame.executeButton.SetDefault()
        accel_table = wx.AcceleratorTable(
            [(wx.ACCEL_NORMAL, wx.WXK_ESCAPE, viewFrame.closeButtonId),
             (wx.ACCEL_NORMAL, wx.WXK_RETURN, viewFrame.executeButtonId)])
    else:
        accel_table = wx.AcceleratorTable(
            [(wx.ACCEL_NORMAL, wx.WXK_ESCAPE, viewFrame.closeButtonId)])

    # setup some hotkeys as well
    viewFrame.SetAcceleratorTable(accel_table)
    

def createStandardObjectAndPipelineIntrospection(d3module,
                                                 viewFrame, viewFramePanel,
                                                 objectDict,
                                                 renderWindow=None):
       
    """Given a devide module and its viewframe, this will create a
    standard wxChoice and wxButton (+ labels) UI for object and
    pipeline introspection.  In addition, it'll call
    setupObjectAndPipelineIntrospection in order to bind events to these
    controls.

    In order to use this, the module HAS to use the
    vtkPipelineConfigModuleMixin.

    IMPORTANT: viewFrame must have a top-level sizer that contains ONLY
    the viewFramePanel.  This is the default for wxGlade created dialogs
    with a top-level panel.  The viewFramePanel's sizer must be a
    vertical box sizer.  That sizer must contain yet ANOTHER sizer with a 7
    pixel border all around.  The introspection controls will be created
    as a sibling to the ANOTHER sizer.  Also see the moduleWriting guide.
    
    """

    ocLabel = wx.StaticText(viewFramePanel, -1, "Examine the")
    objectChoiceId = wx.NewId()
    objectChoice = wx.Choice(viewFramePanel, objectChoiceId, choices=[])
    objectChoice.SetToolTip(wx.ToolTip(
        "Select an object from the drop-down box to introspect it."))
    pbLabel = wx.StaticText(viewFramePanel, -1, "or")
    pipelineButtonId = wx.NewId()
    pipelineButton = wx.Button(viewFramePanel, pipelineButtonId, "Pipeline")
    pipelineButton.SetToolTip(wx.ToolTip(
        "Show the underlying VTK pipeline."))

    hSizer = wx.BoxSizer(wx.HORIZONTAL)
    hSizer.Add(ocLabel, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 4)
    hSizer.Add(objectChoice, 1, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 4)
    hSizer.Add(pbLabel, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 4)
    hSizer.Add(pipelineButton, 0, wx.ALIGN_CENTER_VERTICAL, 0)

    # this will usually get added right below an existing sizer with 7 points
    # border all around.  Below us the ECAS buttons will be added and these
    # assume that there is a 7 pixel border above them, which is why we
    # supply a 7 pixel below us.
    viewFramePanel.GetSizer().Add(hSizer, 0,
                                  wx.LEFT|wx.RIGHT|wx.BOTTOM|wx.EXPAND, 7)

    # force the sizer to calculate new layout with all children (because
    # we've just added something)
    viewFramePanel.GetSizer().Layout()
    # fit and setsizehints (autolayout should remain on)    
    viewFramePanel.GetSizer().Fit(viewFramePanel)
    viewFramePanel.GetSizer().SetSizeHints(viewFramePanel)

    # now we have to get the top level sizer to do its thing
    # WORKAROUND - if we don't remove and add, the
    # viewFrame.GetSizer().Layout() below doesn't do anything.
    viewFrame.GetSizer().Remove(viewFramePanel)
    viewFrame.GetSizer().Add(viewFramePanel, 1, wx.EXPAND, 0)
    # WORKAROUND ENDS
    viewFrame.GetSizer().Layout() # this should update the minimum size
    viewFrame.GetSizer().Fit(viewFrame)
    viewFrame.GetSizer().SetSizeHints(viewFrame)
    
    # finally do the actual event setup
    setupObjectAndPipelineIntrospection(d3module, viewFrame, objectDict,
                                        renderWindow,
                                        objectChoice, objectChoiceId,
                                        pipelineButtonId)

def getModuleIcon():
    icon = wx.EmptyIcon()
    icon.CopyFromBitmap(
        resources.graphics.images.getdevidelogom32x32Bitmap())
    return icon

def createModuleViewFrameTitle(d3module):
    return '%s View: %s' % \
           (d3module.__class__.__name__,
            d3module._moduleManager.get_instance_name(d3module))

def instantiateModuleViewFrame(d3module, moduleManager, frameClass):
    # instantiate the frame
    pw = moduleManager.get_module_view_parent_window()
    # name becomes the WM_CLASS under X
    viewFrame = frameClass(pw, -1, 'dummy', name='DeVIDE')

    # make sure that it's only hidden when it's closed
    wx.EVT_CLOSE(viewFrame,
              lambda e: viewFrame.Show(False))

    # set its title (is there not an easier way to get the class name?)
    viewFrame.SetTitle(createModuleViewFrameTitle(d3module))

    # set its icon!
    viewFrame.SetIcon(getModuleIcon())

    return viewFrame

def setupObjectAndPipelineIntrospection(d3module, viewFrame, objectDict,
                                        renderWindow,
                                        objectChoice, objectChoiceId,
                                        pipelineButtonId):
    """Setup all object and pipeline introspection for standard module
    views with a choice for objects and a button for pipeline
    introspection.  Call this if you have a wx.Choice and wx.Button ready!

    viewFrame is the actual window of the module view.
    objectDict is a dictionary with object name strings as keys and object
    instances as values.
    renderWindow is an optional renderWindow that'll be used for updating,
    pass as None if you don't have this.
    objectChoice is the object choice widget.
    objectChoiceId is the event id connected to the objectChoice widget.
    pipelineButtonId is the event id connected to the pipeline
    introspection button.

    In order to use this, the module HAS to use the
    vtkPipelineConfigModuleMixin.

    """

    # fill out the objectChoice with the object names
    objectChoice.Clear()
    for objectName in objectDict.keys():
        objectChoice.Append(objectName)
    # default on first object
    objectChoice.SetSelection(0)

    # setup the two default callbacks
    wx.EVT_CHOICE(viewFrame, objectChoiceId,
               lambda e: d3module._defaultObjectChoiceCallback(
        viewFrame, renderWindow, objectChoice, objectDict))

    wx.EVT_BUTTON(viewFrame, pipelineButtonId,
               lambda e: d3module._defaultPipelineCallback(
        viewFrame, renderWindow, objectDict))



def setupVTKObjectProgress(d3module, obj, progressText):
    # we DON'T use SetProgressMethod, as the handler object then needs
    # to store a binding to the vtkProcessObject, which means that
    # the objects never die... this way, there are no refs
    # in addition, the AddObserver is the standard way for doing this
    # we should probably not use ProgressText though...
    obj.SetProgressText(progressText)
    mm = d3module._moduleManager
    obj.AddObserver(
        'ProgressEvent', lambda vtko, name:
        mm.genericProgressCallback(vtko,
                                   vtko.GetClassName(),
                                   vtko.GetProgress(),
                                   progressText))
