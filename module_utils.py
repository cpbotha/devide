# $Id: module_utils.py,v 1.3 2002/04/30 01:55:17 cpbotha Exp $

from wxPython.wx import *
from wxPython.xrc import *
import Pmw
import Tkinter
import tkFileDialog
from vtkPipeline.vtkPipeline import \
     vtkPipelineBrowser
from vtkPipeline.ConfigVtkObj import ConfigVtkObj

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
    

def CSAEO_box(module, parent_window):
    """Adds button box with cancel, sync, apply, execute and ok buttons.
    
    This is standard for many of the modules.  The methods sync_config(),
    apply_config() and execute_module() have to be defined.
    """

    box2 = Pmw.ButtonBox(parent_window)
    box2.add('Cancel', command=parent_window.withdraw)
    # synch settings with underlying code
    box2.add('Sync', command=module.sync_config)
    # apply settings
    box2.add('Apply', command=module.apply_config)
    # apply and execute
    box2.add('Execute', command=lambda module=module:
             (module.apply_config(), module.execute_module()))
    # apply and close dialog
    box2.add('Ok', command=lambda module=module, parent_window=parent_window:
             (module.apply_config(), parent_window.withdraw()))
    
    balloon = Pmw.Balloon(parent_window)
    balloon.bind(box2.button(0),
                 balloonHelp='Close this dialogue without applying.')
    balloon.bind(box2.button(1),
                 balloonHelp='Synchronise dialogue with configuration '
                 'of underlying system.')
    balloon.bind(box2.button(2),
                 balloonHelp='Modify configuration of underlying system '
                 'as specified by this dialogue.')
    balloon.bind(box2.button(3),
                 balloonHelp='Apply, then execute the module.')
    balloon.bind(box2.button(4),
                     balloonHelp='Apply, then close the window.')
    
    return box2
    
def browse_vtk_pipeline(vtk_objects,
                        parent_window=None, render_window=None):
    """Helper function for all derived classes.
    
    They can call this method from their configure methods to start a vtk
    pipeline browsers on their internal VTK objects.
    """
    
    pipeline_browser_window = Tkinter.Toplevel(parent_window)
    # we don't have access to a renderer right now
    pipeline_browser = vtkPipelineSegmentBrowser(pipeline_browser_window,
                                                 vtk_objects)
    # pack it
    pipeline_browser.pack (side='top', expand = 1, fill = 'both' )
    
def configure_vtk_object(vtk_object,
                         parent_window=None, render_window=None):
    """Helper method for all derived classes.
    
    They can call this method from their view methods to start Prabhu's
    vtk object configurator on an internal vtk object.
    """
    conf = ConfigVtkObj(render_window)
    conf.set_update_method(vtk_object.Update)
    conf.configure(parent_window, vtk_object)

def fileopen_stringvar(filespec, stringvar):
    """Utility function to offer file open dialog and modify stringvar.
    """
        
    filename = tkFileDialog.askopenfilename(filetypes=filespec)
    if len(filename) > 0:
        stringvar.set(filename)
    
def vtk_progress_callback(process_object):
    """Default callback that can be used for VTK ProcessObject callbacks.
    
    In all VTK-using child classes, this method can be used if such a
    class wants to show its process graphically.
    """
    
    print "progress! %s" % (process_object.GetProgress())
