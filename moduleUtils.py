# $Id: moduleUtils.py,v 1.9 2003/05/13 09:51:08 cpbotha Exp $

from wxPython.wx import *
from external.vtkPipeline.vtkPipeline import \
     vtkPipelineBrowser
from external.vtkPipeline.ConfigVtkObj import ConfigVtkObj

def bind_CSAEO(module, view_frame):
    # it seems wxID_CANCEL (and probably some others) is an exception
    # if you use XMLID on it, it just don't work dude
    EVT_BUTTON(view_frame, wxID_CANCEL,
               lambda e, vf=view_frame: vf.Show(false))
    EVT_BUTTON(view_frame, wxID_OK,
               lambda e, m=module, vf=view_frame: (m.apply_config(),
                                                   vf.Show(false)))
    EVT_BUTTON(view_frame, XMLID('MV_ID_SYNC'),
               lambda e, m=module: m.sync_config())
    EVT_BUTTON(view_frame, XMLID('MV_ID_APPLY'),
               lambda e, m=module: m.apply_config())
    EVT_BUTTON(view_frame, XMLID('MV_ID_EXECUTE'),
               lambda e, m=module: (m.apply_config(),
                                    m.execute_module()))


def createECASButtons(d3module, viewFrame, viewFramePanel):
    """Add Execute, Close, Apply and Sync buttons to the viewFrame.

    d3module is the module for which these buttons are being added.
    viewFrame is the actual dialog frame.
    viewFramePanel is the top-level panel in the frame, i.e. the panel
    completely filling the top-level sizer.

    IMPORTANT: viewFrame must have a top-level sizer that contains ONLY
    the viewFramePanel.  This is the default for wxGlade created dialogs
    with a top-level panel.  The viewFramePanel's sizer must be a
    vertical box sizer.

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
    viewFrame.executeButtonId = wxNewId()
    viewFrame.executeButton = wxButton(viewFramePanel,
                                       viewFrame.executeButtonId,
                                       "Execute")
    viewFrame.executeButton.SetToolTip(wxToolTip(
        "Apply any changes, then execute the module."))

    viewFrame.closeButtonId = wxNewId()
    viewFrame.closeButton = wxButton(viewFramePanel,
                                       viewFrame.closeButtonId,
                                       "Close")
    viewFrame.closeButton.SetToolTip(wxToolTip(
        "Close the dialog window."))

    viewFrame.applyButtonId = wxNewId()
    viewFrame.applyButton = wxButton(viewFramePanel,
                                       viewFrame.applyButtonId,
                                       "Apply")
    viewFrame.applyButton.SetToolTip(wxToolTip(
        "Modify configuration of underlying system as specified by "
        "this dialogue."))

    viewFrame.syncButtonId = wxNewId()
    viewFrame.syncButton = wxButton(viewFramePanel,
                                       viewFrame.syncButtonId,
                                       "Sync")
    viewFrame.syncButton.SetToolTip(wxToolTip(
        "Synchronise dialogue with configuration of underlying system."))

    # add them to their own sizer, each with a border of 4 pixels
    buttonSizer = wxBoxSizer(wxHORIZONTAL)
    for button in (viewFrame.executeButton, viewFrame.closeButton,
                   viewFrame.applyButton, viewFrame.syncButton):
        buttonSizer.Add(button, 0, wxALL, 4)

    # add the buttonSizer to the viewFramePanel sizer with a border of 5 pixels
    viewFramePanel.GetSizer().Add(buttonSizer, 0, wxALL|wxALIGN_RIGHT, 5)
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
    viewFrame.GetSizer().Add(viewFramePanel, 1, wxEXPAND, 0)
    # WORKAROUND ENDS
    viewFrame.GetSizer().Layout() # this should update the minimum size
    viewFrame.GetSizer().Fit(viewFrame)
    viewFrame.GetSizer().SetSizeHints(viewFrame)

    # EVENT BINDINGS
    # execute
    EVT_BUTTON(viewFrame, viewFrame.executeButtonId,
               lambda e, m=d3module: (m.applyViewToLogic(),
                                      m.executeModule()))
    # close
    EVT_BUTTON(viewFrame, viewFrame.closeButtonId,
               lambda e, vf=viewFrame: vf.Show(False))
    # apply
    EVT_BUTTON(viewFrame, viewFrame.applyButtonId,
               lambda e, m=d3module: m.applyViewToLogic())
    # sync
    EVT_BUTTON(viewFrame, viewFrame.syncButtonId,
               lambda e, m=d3module: m.syncViewWithLogic())               

    # make sure that execute is the default button
    viewFrame.executeButton.SetDefault()

    # setup some hotkeys as well
    accel_table = wxAcceleratorTable(
        [(wxACCEL_NORMAL, WXK_ESCAPE, viewFrame.closeButtonId),
         (wxACCEL_NORMAL, WXK_RETURN, viewFrame.executeButtonId)])
    viewFrame.SetAcceleratorTable(accel_table)
    

def bindCSAEO(module, view_frame):
    """Bind events to buttons in standard view/config module dialogue.

    This function is used when the dialogue code has been created with
    wxGlade instead of XRCEd.
    """
    
    view_frame.cancel_button.SetToolTip(
        wxToolTip('Close this dialogue without applying changes.'))
    EVT_BUTTON(view_frame, wxID_CANCEL,
               lambda e, vf=view_frame: vf.Show(false))

    view_frame.ok_button.SetToolTip(
        wxToolTip('Apply changes, then close this dialogue.'))
    EVT_BUTTON(view_frame, wxID_OK,
               lambda e, m=module, vf=view_frame: (m.applyViewToLogic(),
                                                   vf.Show(false)))

    view_frame.sync_button.SetToolTip(
        wxToolTip('Synchronise dialogue with configuration of underlying '
                  'system.'))
    EVT_BUTTON(view_frame, view_frame.SYNC_ID,
               lambda e, m=module: m.syncViewWithLogic())

    view_frame.apply_button.SetToolTip(
        wxToolTip('Modify configuration of underlying system as specified by '
                  'this dialogue.'))
    EVT_BUTTON(view_frame, view_frame.APPLY_ID,
               lambda e, m=module: m.applyViewToLogic())

    view_frame.execute_button.SetToolTip(
        wxToolTip('Apply changes, then execute the module.'))
    # very importantly, make the Execute button the default
    view_frame.execute_button.SetDefault()
    EVT_BUTTON(view_frame, view_frame.EXECUTE_ID,
               lambda e, m=module: (m.applyViewToLogic(),
                                    m.executeModule()))

    # setup some hotkeys as well
    accel_table = wxAcceleratorTable(
        [(wxACCEL_NORMAL, WXK_ESCAPE, wxID_CANCEL)])
    view_frame.SetAcceleratorTable(accel_table)

def createStandardObjectAndPipelineIntrospection(d3module,
                                                 viewFrame, viewFramePanel,
                                                 objectDict, renderWindow):
       
    """Given a dscas3 module and its viewframe, this will create a
    standard wxChoice and wxButton (+ labels) UI for object and
    pipeline introspection.  In addition, it'll call
    setupObjectAndPipelineIntrospection in order to bind events to these
    controls.

    In order to use this, the module HAS to use the
    vtkPipelineConfigModuleMixin.

    IMPORTANT: viewFrame must have a top-level sizer that contains ONLY
    the viewFramePanel.  This is the default for wxGlade created dialogs
    with a top-level panel.  The viewFramePanel's sizer must be a
    vertical box sizer.
    
    """

    ocLabel = wxStaticText(viewFramePanel, -1, "Examine the")
    objectChoiceId = wxNewId()
    objectChoice = wxChoice(viewFramePanel, objectChoiceId, choices=[])
    pbLabel = wxStaticText(viewFramePanel, -1, "or")
    pipelineButtonId = wxNewId()
    pipelineButton = wxButton(viewFramePanel, pipelineButtonId, "Pipeline")

    hSizer = wxBoxSizer(wxHORIZONTAL)
    hSizer.Add(ocLabel, 0, wxLEFT|wxRIGHT|wxALIGN_CENTER_VERTICAL, 2)
    hSizer.Add(objectChoice, 1, wxEXPAND|wxALIGN_CENTER_VERTICAL, 0)
    hSizer.Add(pbLabel, 0, wxLEFT|wxRIGHT|wxALIGN_CENTER_VERTICAL, 2)
    hSizer.Add(pipelineButton, 0, wxALIGN_CENTER_VERTICAL, 0)

    viewFramePanel.GetSizer().Add(hSizer, 1, wxALL|wxEXPAND, 5)

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
    viewFrame.GetSizer().Add(viewFramePanel, 1, wxEXPAND, 0)
    # WORKAROUND ENDS
    viewFrame.GetSizer().Layout() # this should update the minimum size
    viewFrame.GetSizer().Fit(viewFrame)
    viewFrame.GetSizer().SetSizeHints(viewFrame)
    
    # finally do the actual event setup
    setupObjectAndPipelineIntrospection(d3module, viewFrame, objectDict,
                                        renderWindow,
                                        objectChoice, objectChoiceId,
                                        pipelineButtonId)

def setupObjectAndPipelineIntrospection(d3module, viewFrame, objectDict,
                                        renderWindow,
                                        objectChoice, objectChoiceId,
                                        pipelineButtonId):
    """Setup all object and pipeline introspection for standard module
    views with a choice for objects and a button for pipeline
    introspection.  Call this if you have a wxChoice and wxButton ready!

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
    EVT_CHOICE(viewFrame, objectChoiceId,
               lambda e: d3module._defaultObjectChoiceCallback(
        viewFrame, renderWindow, objectChoice, objectDict))

    EVT_BUTTON(viewFrame, pipelineButtonId,
               lambda e: d3module._defaultPipelineCallback(
        viewFrame, renderWindow, objectDict))


