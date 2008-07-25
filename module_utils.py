# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

"""Collection of module utility functions.

@author: Charl P. Botha <http://cpbotha.net/>
"""

import wx
import resources.graphics.images

def create_eoca_buttons(d3module, viewFrame, viewFramePanel,
                        ok_default=True, 
                        cancel_hotkey=True):
    """Add Execute, OK, Cancel and Apply buttons to the viewFrame.

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

    The buttons will be created with the viewFramePanel as their
    parent.  They will be added to a horizontal sizer which will then
    be added to viewFramePanel.GetSizer().  The viewFramePanel sizer
    will then be used to fit the viewFramePanel.

    After this, the viewFrame.GetSizer() will be used to fit and
    layout the frame itself.
    """

    # create the buttons
    viewFrame.executeButtonId = wx.NewId()
    viewFrame.executeButton = wx.Button(viewFramePanel,
                                        viewFrame.executeButtonId,
                                        "&Execute")
    viewFrame.executeButton.SetToolTip(wx.ToolTip(
        "Apply all changes, then execute the whole network "\
        "(F5 or Alt-E)."))

    viewFrame.id_ok_button = wx.ID_OK
    viewFrame.ok_button = wx.Button(
            viewFramePanel, viewFrame.id_ok_button, "OK")
    viewFrame.ok_button.SetToolTip(wx.ToolTip(
        "Apply all changes, then close this dialogue (Enter)."))

    viewFrame.id_cancel_button = wx.ID_CANCEL
    viewFrame.cancel_button = wx.Button(
            viewFramePanel, viewFrame.id_cancel_button, "Cancel")
    viewFrame.cancel_button.SetToolTip(wx.ToolTip(
        "Cancel all changes, then close this dialogue (Esc)."))

    viewFrame.applyButtonId = wx.NewId()
    viewFrame.applyButton = wx.Button(viewFramePanel,
                                      viewFrame.applyButtonId,
                                      "Apply")
    viewFrame.applyButton.SetToolTip(wx.ToolTip(
        "Apply all changes, keep this dialogue open."))


    # add them to their own sizer, each with a border of 4 pixels on the right
    buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
    for button in (viewFrame.executeButton, viewFrame.ok_button,
                   viewFrame.cancel_button):
        buttonSizer.Add(button, 0, wx.RIGHT, 7)

    # except for the right-most button, which has no border
    buttonSizer.Add(viewFrame.applyButton, 0)

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
    mm = d3module._module_manager

    # call back into the graphEditor, if it exists
    ge = mm._devide_app.get_interface()._graph_editor

    # execute
    wx.EVT_BUTTON(viewFrame, viewFrame.executeButtonId,
               lambda e: (mm.applyModuleViewToLogic(d3module),
                          mm.executeNetwork(d3module)))
    
    # OK (apply and close)
    wx.EVT_BUTTON(viewFrame, viewFrame.id_ok_button,
               lambda e, vf=viewFrame:
               (mm.applyModuleViewToLogic(d3module),
                   vf.Show(False)))
    
    # Cancel
    def helper_cancel():
        mm.syncModuleViewWithLogic(d3module)
        viewFrame.Show(False)

    wx.EVT_BUTTON(viewFrame, viewFrame.id_cancel_button,
               lambda e: helper_cancel()) 
    
    # Apply
    wx.EVT_BUTTON(viewFrame, viewFrame.applyButtonId,
               lambda e: mm.applyModuleViewToLogic(d3module))

    # make sure that OK is the default button
    # unless the user specifies otherwise - in frames where we make
    # use of an introspection shell, we don't want Enter to executeh
    # or Ctrl-Enter to execute the whole network.
    accel_list = []

    if cancel_hotkey:
        # this doesn't work for frames, but I'm keeping it here just
        # in case.  We use the EVT_CHAR_HOOK later to capture escape
        accel_list.append(
                (wx.ACCEL_NORMAL, wx.WXK_ESCAPE,
                 viewFrame.id_cancel_button))

    # add F5 hotkey to this dialogue as well so that we can execute
    accel_list.append(
            (wx.ACCEL_NORMAL, wx.WXK_F5,
                viewFrame.executeButtonId))

    if ok_default:
        viewFrame.ok_button.SetDefault()
        accel_list.append(
                (wx.ACCEL_NORMAL, wx.WXK_RETURN,
                    viewFrame.id_ok_button))
    
    # setup some hotkeys as well
    viewFrame.SetAcceleratorTable(wx.AcceleratorTable(accel_list))

    def handler_evt_char_hook(event):
        if event.KeyCode == wx.WXK_ESCAPE:
            helper_cancel()

        else:
            event.Skip()

    if cancel_hotkey:
        # this is the only way to capture escape on a frame
        viewFrame.Bind(wx.EVT_CHAR_HOOK, handler_evt_char_hook)

createECASButtons = create_eoca_buttons

def create_standard_object_introspection(d3module, 
                                         viewFrame, viewFramePanel,
                                         objectDict,
                                         renderWindow=None):
       
    """Given a devide module and its viewframe, this will create a
    standard wxChoice and wxButton (+ labels) UI for object and
    introspection.  In addition, it'll call setup_object_introspection
    in order to bind events to these controls.

    In order to use this, the module HAS to use the
    IntrospectModuleMixin.

    IMPORTANT: viewFrame must have a top-level sizer that contains ONLY
    the viewFramePanel.  This is the default for wxGlade created dialogs
    with a top-level panel.  The viewFramePanel's sizer must be a
    vertical box sizer.  That sizer must contain yet ANOTHER sizer with a 7
    pixel border all around.  The introspection controls will be created
    as a sibling to the ANOTHER sizer.  Also see the moduleWriting guide.
    
    """

    introspect_button_id = wx.NewId()
    introspect_button = wx.Button(viewFramePanel, introspect_button_id, "Introspect")

    ocLabel = wx.StaticText(viewFramePanel, -1, "the")
    
    objectChoiceId = wx.NewId()
    objectChoice = wx.Choice(viewFramePanel, objectChoiceId, choices=[])
    objectChoice.SetToolTip(wx.ToolTip(
        "Select an object from the drop-down box to introspect it."))

    hSizer = wx.BoxSizer(wx.HORIZONTAL)
    hSizer.Add(introspect_button, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 4)
    hSizer.Add(ocLabel, 0, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 4)
    hSizer.Add(objectChoice, 1, wx.RIGHT|wx.ALIGN_CENTER_VERTICAL, 4)

    vSizer = wx.BoxSizer(wx.VERTICAL)
    sl = wx.StaticLine(viewFramePanel, -1)
    vSizer.Add(sl, 0, wx.CENTER|wx.EXPAND|wx.BOTTOM, 7)
    vSizer.Add(hSizer, 0, wx.CENTER|wx.EXPAND)

    # this will usually get added right below an existing sizer with 7 points
    # border all around.  Below us the ECAS buttons will be added and these
    # assume that there is a 7 pixel border above them, which is why we
    # supply a 7 pixel below us.
    viewFramePanel.GetSizer().Add(vSizer, 0,
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
    setup_object_introspection(d3module, viewFrame, objectDict,
                               renderWindow,
                               objectChoice, introspect_button_id)

# make sure the old method name still works.
createStandardObjectAndPipelineIntrospection = \
        create_standard_object_introspection

def getModuleIcon():
    icon = wx.EmptyIcon()
    icon.CopyFromBitmap(
        resources.graphics.images.getdevidelogom32x32Bitmap())
    return icon

def createModuleViewFrameTitle(d3module):
    return '%s View' % \
           (d3module.__class__.__name__,)

def instantiateModuleViewFrame(d3module, module_manager, frameClass):
    # instantiate the frame
    pw = module_manager.get_module_view_parent_window()
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

def setup_object_introspection(d3module, viewFrame, objectDict,
                                        renderWindow,
                                        objectChoice, introspect_button_id,
                                        ):
    """Setup all object introspection for standard module views with a
    choice for object introspection.  Call this if you have a
    wx.Choice and wx.Button ready!

    viewFrame is the actual window of the module view.
    objectDict is a dictionary with object name strings as keys and object
    instances as values.
    renderWindow is an optional renderWindow that'll be used for updating,
    pass as None if you don't have this.
    objectChoice is the object choice widget.
    objectChoiceId is the event id connected to the objectChoice widget.

    In order to use this, the module HAS to use the
    IntrospectModuleMixin.

    """

    # fill out the objectChoice with the object names
    objectChoice.Clear()
    for objectName in objectDict.keys():
        objectChoice.Append(objectName)
    # default on first object
    objectChoice.SetSelection(0)

    # setup the two default callbacks
    wx.EVT_BUTTON(viewFrame, introspect_button_id,
                  lambda e: d3module._defaultObjectChoiceCallback(
        viewFrame, renderWindow, objectChoice, objectDict))

# old method name should still work
setupObjectAndPipelineIntrospection = setup_object_introspection

def setupVTKObjectProgress(d3module, obj, progressText):
    # we DON'T use SetProgressMethod, as the handler object then needs
    # to store a binding to the vtkProcessObject, which means that
    # the objects never die... this way, there are no refs
    # in addition, the AddObserver is the standard way for doing this
    # we should probably not use ProgressText though...
    obj.SetProgressText(progressText)
    mm = d3module._module_manager
    obj.AddObserver(
        'ProgressEvent', lambda vtko, name:
        mm.genericProgressCallback(vtko,
                                   vtko.GetClassName(),
                                   vtko.GetProgress(),
                                   progressText))
