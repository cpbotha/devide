# $Id: module_utils.py,v 1.9 2003/01/28 18:13:31 cpbotha Exp $

from wxPython.wx import *
from wxPython.xrc import *
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
    

def bind_CSAEO2(module, view_frame):
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
               lambda e, m=module, vf=view_frame: (m.syncConfigWithView(),
                                                   m.applyConfigToLogic(),
                                                   vf.Show(false)))

    view_frame.sync_button.SetToolTip(
        wxToolTip('Synchronise dialogue with configuration of underlying '
                  'system.'))
    EVT_BUTTON(view_frame, view_frame.SYNC_ID,
               lambda e, m=module: (m.sync_config())

    view_frame.apply_button.SetToolTip(
        wxToolTip('Modify configuration of underlying system as specified by '
                  'this dialogue.'))
    EVT_BUTTON(view_frame, view_frame.APPLY_ID,
               lambda e, m=module: m.apply_config())

    view_frame.execute_button.SetToolTip(
        wxToolTip('Apply changes, then execute the module.'))
    EVT_BUTTON(view_frame, view_frame.EXECUTE_ID,
               lambda e, m=module: (m.apply_config(),
                                    m.execute_module()))

    # setup some hotkeys as well
    accel_table = wxAcceleratorTable(
        [(wxACCEL_NORMAL, WXK_ESCAPE, wxID_CANCEL),
         (wxACCEL_NORMAL, WXK_RETURN, wxID_OK)])
    view_frame.SetAcceleratorTable(accel_table)


