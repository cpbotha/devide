# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

# FIXME: def show() should really be moved a level up!!

# left click on glyph: select and drag
# left click on canvas: rubberband select
# right click on glyph: glyph context menu
# right click on canvas: canvas context menu
# middle click: pan
# shift-middle click up and down: zoom out and in
# mouse wheel: zoom

import copy
import cPickle
from internal.devide_canvas.devide_canvas import DeVIDECanvas 
from internal.devide_canvas.devide_canvas_object import \
DeVIDECanvasGlyph, DeVIDECanvasLine, DeVIDECanvasSimpleLine, \
DeVIDECanvasRBBox
import genUtils
from moduleManager import ModuleManagerException
import moduleUtils # for getModuleIcon
import os
import re
import string
import sys
import time
import weakref
import wx

# so we're using VTK here for doing the graph layout.
import vtk

from module_kits.misc_kit import dprint


# ----------------------------------------------------------------------------
class geCanvasDropTarget(wx.PyDropTarget):
    def __init__(self, graphEditor):
        wx.PyDropTarget.__init__(self)
        self._graphEditor = graphEditor

        do = wx.DataObjectComposite()
        tdo = wx.TextDataObject()
        fdo = wx.FileDataObject()
        do.Add(tdo)
        do.Add(fdo)
        self._tdo = tdo
        self._fdo = fdo

        self.SetDataObject(do)
        self._dataObject = do
        

    def OnDrop(self, x, y):
        return True

    def OnData(self, x, y, d):
        # when we are a drag source, we get blocked throughout the
        # drag, which means that our picked_cobject doesn't get
        # updated, which means that drops on glyphs don't get handled.
        # so here we make sure that the correct picked_cobject is
        # selected right before we actually handle the drop:
        self._graphEditor.canvas.update_picked_cobject_at_drop(x, y)
        
        if self.GetData():
            text = self._tdo.GetText()
            filenames = self._fdo.GetFilenames()
            
            if len(text) > 0:
                # set the string to zero so we know what to do when
                self._tdo.SetText('')
                self._graphEditor.canvasDropText(x,y,text)

            elif len(filenames) > 0:
                # handle the list of filenames
                dropFilenameErrors = self._graphEditor.canvasDropFilenames(
                    x,y,filenames)

                if len(dropFilenameErrors) > 0:
                    em = ['The following dropped files could not '
                          'be handled:']
                    for i in dropFilenameErrors:
                        em.append(
                            '%s: %s' % (i))
                        
                    self._graphEditor._interface.log_warning(
                        '\n'.join(em))

        # d is the recommended drag result.  we could also return
        # wx.DragNone if we don't want whatever's been dropped.
        return d
        
        

# ----------------------------------------------------------------------------
class GlyphSelection:
    """Abstraction for any selection of glyphs.

    This is used for the default selection and for the blocked glyph selection
    currently. 
    """
    
    def __init__(self, canvas, glyph_flag):
        """
        @param glyph_flag: string name of glyph attribute that will be set
        to true or false depending on the selection that it belongs to.
        """
        
        self._canvas = canvas
        self._glyph_flag = glyph_flag
        self._selectedGlyphs = []
        

    def close(self):
        # take care of all references
        self.removeAllGlyphs()

    def addGlyph(self, glyph):
        """Add a glyph to the selection.
        """

        if glyph in self._selectedGlyphs:
            # it's already selected, ignore
            return

        # add it to our structures
        self._selectedGlyphs.append(glyph)
        # tell it that it's the chosen one (ha ha)
        setattr(glyph, self._glyph_flag, True)
        #glyph.selected = True
        # redraw it
        glyph.update_geometry()

    def getSelectedGlyphs(self):
        """Returns a list with the selected glyphs.  Do not modify externally.
        """
        return self._selectedGlyphs

    def removeGlyph(self, glyph):
        """Remove a glyph from the selection.
        """
        if not glyph in self._selectedGlyphs:
            # it's not in the selection, do nothing.
            return

        del self._selectedGlyphs[self._selectedGlyphs.index(glyph)]
        setattr(glyph, self._glyph_flag, False)
        #glyph.selected = False
        glyph.update_geometry()

    def removeAllGlyphs(self):
        """Remove all glyphs from selection.
        """
        for glyph in self._selectedGlyphs:
            glyph.selected = False
            glyph.update_geometry()

        self._selectedGlyphs = []
        
    def selectGlyph(self, glyph):
        """Set the selection on one single glyph.  All others must be
        unselected.
        """

        self.removeAllGlyphs()
        self.addGlyph(glyph)

# ----------------------------------------------------------------------------

class GraphEditor:
    def __init__(self, interface, devideApp):
        # initialise vars
        self._interface = interface
        self._devide_app = devideApp

        mf = self._interface._main_frame
        em = mf.edit_menu
        self._appendEditCommands(em,
                                 mf,
                                 (0,0), False)

        self._append_network_commands(mf.network_menu,
                                      mf, False)
        

        wx.EVT_MENU(mf, mf.id_modules_search,
                    self._handler_modules_search)

        wx.EVT_MENU(mf, mf.id_rescan_modules,
                    lambda e, s=self: s.fillModuleLists())

        wx.EVT_MENU(mf, mf.id_refresh_module_kits,
                    self._handler_refresh_module_kits)

        wx.EVT_MENU(mf, mf.fileNewId,
                    self._fileNewCallback)

        wx.EVT_MENU(mf, mf.fileExitId,
                    self._fileExitCallback)

        wx.EVT_MENU(mf, mf.fileOpenId,
                    self._fileOpenCallback)

        wx.EVT_MENU(mf,
                    mf.fileOpenSegmentId,
                    self._handlerFileOpenSegment)

        wx.EVT_MENU(mf, mf.fileSaveId,
                 self._fileSaveCallback)

        wx.EVT_MENU(mf, mf.id_file_save_as,
                self._handler_file_save_as)

        wx.EVT_MENU(mf, mf.fileSaveSelectedId,
                 self._handlerFileSaveSelected)

        wx.EVT_MENU(mf, mf.fileExportAsDOTId,
                 self._handlerFileExportAsDOT)

        wx.EVT_MENU(mf,
                    mf.fileExportSelectedAsDOTId,
                    self._handlerFileExportSelectedAsDOT)

        wx.EVT_MENU(mf,
                    mf.helpShowHelpId,
                    self._handlerHelpShowHelp)

        # every time a normal character is typed
        mf.search.Bind(wx.EVT_TEXT, self._handler_search)

        # we do this to capture enter, escape and up and down
        # we need this nasty work-around on win and gtk: the
        # SearchCtrl doesn't trigger the necessary events itself.
        if wx.Platform in ['__WXMSW__', '__WXGTK__']:
            for child in mf.search.GetChildren():
                if isinstance(child, wx.TextCtrl):
                    child.Bind(wx.EVT_CHAR, 
                            self._handler_search_char)
                    break
        else:
            mf.search.Bind(wx.EVT_CHAR, 
                    self._handler_search_char)

        # user clicks on x, search box is emptied.
        mf.search.Bind(wx.EVT_SEARCHCTRL_CANCEL_BTN,
                self._handler_search_x_button)

        # not currently using wx.EVT_SEARCHCTRL_SEARCH_BTN

        
        wx.EVT_LISTBOX(mf,
                       mf.module_cats_list_box.GetId(),
                       self._update_search_results)

        wx.EVT_LISTBOX(mf,
                       mf.module_list_box.GetId(),
                       self._handlerModulesListBoxSelected)

        # this will be filled in by self.fill_module_tree; it's here for
        # completeness
        self._availableModules = None

        # this is usually shortly after initialisation, so a module scan
        # should be available.  Actually, the user could be very naughty,
        # but let's not think about that.
        self.fillModuleLists(scan_modules=False)

        wx.EVT_MOUSE_EVENTS(mf.module_list_box,
                            self._handlerModulesListBoxMouseEvents)


        # instantiate the canvas.
        self.canvas = DeVIDECanvas(mf._rwi, mf._ren)

        # the canvas is a drop target
        self._canvasDropTarget = geCanvasDropTarget(self)
        # the vtkRenderWindowInteractor is also a WX construct.
        mf._rwi.SetDropTarget(self._canvasDropTarget)
        
        # bind events on the canvas
        self.canvas.add_observer('left_button_down',
                              self._observer_canvas_left_down)
        self.canvas.add_observer('right_button_down',
                              self._observer_canvas_right_down)
        self.canvas.add_observer('left_button_up',
                                 self._observer_canvas_left_up)
        self.canvas.add_observer('dragging',
                              self._observer_canvas_drag)

        # initialise selection
        self._selected_glyphs = GlyphSelection(self.canvas,
                                              'selected')

        self._blocked_glyphs = GlyphSelection(self.canvas,
                                              'blocked')

        # we'll use this to keep track of the rubber-band box
        self._rbb_box = None

        # line used for previewing possible connections
        self._preview_line = None

        # initialise cut/copy/paste buffer
        self._copyBuffer = None

        # initialise current filename
        self.set_current_filename(None)

        # On Windows, file open/save dialogs remember where you last
        # used them.  On Linux, we have to do this ourselves.  If we
        # don't, every new selection dialog starts on the current
        # directory.
        self._last_fileselector_dir = ''

        # instrument network_manager with handler so we can autosave
        # before a network gets executed
        self._devide_app.network_manager.add_observer(
                'execute_network_start',
                self._observer_network_manager_ens)


        # now display the shebang
        # (GraphEditor controls the GraphEditor bits...)
        self.show()

    def _handler_modules_search(self, event):
        self._interface._main_frame.search.SetFocus()

    def _handler_refresh_module_kits(self, event):
        mm = self._devide_app.get_module_manager()
        mm.refresh_module_kits()

    def _handler_search(self, event):
        """Handler for when the user types into the search box.
        """
        self._update_search_results()

    def _place_current_module_at_convenient_pos(self):
        """Place currently selected module (in the Module List subwindow) at
        an open position on the canvas.

        This method is called when the user double clicks on a module in the
        module list or when she presses <enter> during module searching.

        FIXME: improve this!!  Just plonk the glyph down in the middle
        of the canvas, avoiding any other glyph there at this moment.
        """
        
        # place currently selected module below the bottom-most module
        # on the canvas
        mlb = self._interface._main_frame.module_list_box

        # _update_search_results() makes sure the first selectable
        # item is selected
        sel = mlb.GetSelection()

        shortName, moduleName = (mlb.GetString(sel),
                                 mlb.GetClientData(sel))

        if moduleName:

            # default position
            x, y = (10,10)

            canvas = self.canvas
            all_glyphs = canvas.getObjectsOfClass(DeVIDECanvasGlyph)

            # rx and ry will contain the first position to the right of
            # the bounding box of all glyphs, ry the first position below
            # the bounding box of all glyphs
            rx, ry = x, y
            for glyph in all_glyphs:
                # this is the bottom right; (0,0) is bottom left
                cx,cy = glyph.get_position()

                if cx >= rx:
                    rx = cx + glyph.get_bounds()[0] + 20
                
                if cy <= ry:
                    ry = cy - glyph.get_bounds()[1] - 20

            y = ry


            modp = 'module:'
            segp = 'segment:'
            if moduleName.startswith(modp):
                # the coordinates are canvas-absolute already
                self.create_module_and_glyph(x, y, moduleName[len(modp):])

            elif moduleName.startswith(segp):
                self._loadAndRealiseNetwork(moduleName[len(segp):], (x,y),
                                            reposition=True)

            else:
                # this could happen, I've no idea how though.
                return False
                
            # module or segment successfully created
            return True

        # no module or segment was created
        return False
        

    def _handler_search_char(self, event):
        key_code = event.GetKeyCode()

        if key_code == wx.WXK_ESCAPE:
            self._interface._main_frame.search.SetValue('')

        elif key_code == wx.WXK_RETURN:
            self._place_current_module_at_convenient_pos()
            self._interface._main_frame.search.SetFocus()

        elif key_code in [wx.WXK_UP, wx.WXK_DOWN]:

            mlb = self._interface._main_frame.module_list_box
            sel = mlb.GetSelection()

            if sel >= 0:
                if key_code == wx.WXK_UP:
                    sel -= 1
                else:
                    sel += 1

                if sel >= 0 and sel < mlb.GetCount():
                    # this SetSelection doesn't seem to call the
                    # event handlers for the mlb (thus updating the help)
                    mlb.SetSelection(sel)
                    # so we call it manually
                    self._handlerModulesListBoxSelected(None)
            
        else:
            event.Skip()

    def _handler_search_x_button(self, event):
        self._interface._main_frame.search.SetValue('')

    def _handlerModulesListBoxMouseEvents(self, event):
        if event.ButtonDClick():
            self._place_current_module_at_convenient_pos()
            # user has dragged and dropped module, if a viewer module
            # has taken focus with Raise(), we have to take it back.
            self.canvas._rwi.SetFocus()
            wx.SafeYield()
            return
        
        if not event.Dragging():
            # if no dragging is taking place, let somebody else
            # handle this event...
            event.Skip()
            return
        
        mlb = self._interface._main_frame.module_list_box

        sel = mlb.GetSelection()
        if sel >= 0:
            shortName, moduleName = mlb.GetString(sel), mlb.GetClientData(sel)
            
            if type(moduleName) != str:
                return
        
            dataObject = wx.TextDataObject(moduleName)
            dropSource = wx.DropSource(self._interface._main_frame.module_list_box)
            dropSource.SetData(dataObject)
            # we don't need the result of the DoDragDrop call (phew)
            # the param is supposedly the copy vs. move flag; True is move.
            # on windows, setting it to false disables the drop on the canvas.
            dropSource.DoDragDrop(True)

        # event processing has to continue, else the listbox keeps listening
        # to mouse movements after the glyph has been dropped
        #event.Skip()

    def _blockmodule(self, glyph):
        """Block the module represented by glyph.

        This does does not invoke a canvas redraw, as these methods
        can be called in batches.  Invoking code should call redraw. 
        """
        # first get the module manager to block this
        mm = self._devide_app.get_module_manager()
        mm.blockmodule(mm.get_meta_module(glyph.moduleInstance))
        # then tell the glyph about it
        self._blocked_glyphs.addGlyph(glyph)
        # finally tell the glyph to update its geometry
        glyph.update_geometry()

    def _unblockmodule(self, glyph):
        """Unblock the module represented by glyph.

        This does does not invoke a canvas redraw, as these methods
        can be called in batches.  Invoking code should call redraw. 
        """
        # first get the module manager to unblock this
        mm = self._devide_app.get_module_manager()
        mm.unblockmodule(mm.get_meta_module(glyph.moduleInstance))
        # then tell the glyph about it
        self._blocked_glyphs.removeGlyph(glyph)
        # finally tell the glyph to update its geometry
        glyph.update_geometry()

    def _execute_modules(self, glyphs):
        """Given a list of glyphs, request the scheduler to execute only those
        modules.

        Of course, producers of selected modules will also be asked to resend
        their output, even although they are perhaps not part of the
        selection.

        This method is called by event handlers in the GraphEditor.
        """
        
        instances = [g.moduleInstance for g in glyphs]
        mm = self._devide_app.get_module_manager()
        allMetaModules = [mm._moduleDict[instance]
                          for instance in instances]

        try:
            self._devide_app.network_manager.execute_network(allMetaModules)
        except Exception, e:
            self._devide_app.log_error_with_exception(str(e))

    def _handler_blockmodules(self, event):
        """Block all selected glyphs and their modules.
        """

        for glyph in self._selected_glyphs.getSelectedGlyphs():
            self._blockmodule(glyph)

        # then update the display
        self.canvas.redraw()

    def _handler_unblockmodules(self, event):
        """Unblock all selected glyphs and their modules.
        """

        for glyph in self._selected_glyphs.getSelectedGlyphs():
            self._unblockmodule(glyph)

        # then update the display
        self.canvas.redraw()

    def _handler_execute_network(self, event):
        """Event handler for 'network|execute' menu call.

        Gets list of all instances in current network, converts these
        to scheduler modules and requests the scheduler to execute them.
        """

        allGlyphs = self.canvas.getObjectsOfClass(DeVIDECanvasGlyph)

        self._execute_modules(allGlyphs)

    def _handler_execute_selected(self, event):
        self._execute_modules(self._selected_glyphs.getSelectedGlyphs())

    def canvasDropText(self, x, y, itemText):
        """itemText is a complete module or segment spec, e.g.
        module:modules.Readers.dicomRDR or
        segment:/home/cpbotha/work/code/devide/networkSegments/blaat.dvn

        x,y are in wx coordinates.
        """

        modp = 'module:'
        segp = 'segment:'

        w_x,w_y,w_z = self.canvas.display_to_world((x,self.canvas.flip_y(y)))
        
        if itemText.startswith(modp):
            self.create_module_and_glyph(w_x, w_y, itemText[len(modp):])

            # if the user has dropped a module on the canvas, we want
            # the focus to return to the canvas, as the user probably
            # wants to connect the thing up.  if we don't do this,
            # some viewer modules takes focus.  Thanks Peter Krekel.
            self.canvas._rwi.SetFocus()
            wx.SafeYield()
          

        elif itemText.startswith(segp):
            self._loadAndRealiseNetwork(itemText[len(segp):], (w_x,w_y),
                                        reposition=True)

            # see explanation above for the SetFocus
            self.canvas._rwi.SetFocus()
            wx.SafeYield()
            


    def canvasDropFilenames(self, x, y, filenames):
        """Event handler for when the user drops a list of filenames
        on the canavs.

        @param x,y: coordinates in the wx system.
        """

        # before we do anything, convert to world coordinates
        w_x,w_y,w_z = \
            self.canvas.display_to_world((x,self.canvas.flip_y(y)))
        
        def createModuleOneVar(moduleName, configVarName, configVarValue,
                               newModuleName=None):
            """This method creates a moduleName (e.g. modules.Readers.vtiRDR)
            at position x,y.  It then sets the 'configVarName' attribute to
            value configVarValue.
            """
            (mod, glyph) = self.create_module_and_glyph(w_x, w_y, moduleName)
            if mod:
                cfg = mod.get_config()
                setattr(cfg, configVarName, filename)
                mod.set_config(cfg)

                if newModuleName:
                    r = self._renameModule(mod, glyph, newModuleName)
                    #i = 0
                    #while not r:
                    #    i += 1
                    #    r = self._renameModule(mod, glyph, '%s (%d)' %
                    #                           (newModuleName, i))

        def handle_drop_on_glyph(glyph, filename):
            """Adds whole list of filenames to dicomRDR list, or adds
            first filename in list if its any other module with a
            filename attribute in its config struct.
            """
            mi = g.moduleInstance
            c = mi.get_config()
            mm = self._devide_app.get_module_manager()

            if mi.__class__.__name__ == 'dicomRDR':
                c = mi.get_config()
                del c.dicomFilenames[:] 
                c.dicomFilenames.extend(filenames)
                # this will do the whole config -> logic -> view dance
                # view is only done if view_initialised is True
                mi.set_config(c)

                return True

            elif mi.__class__.__name__ == 'DICOMReader':
                c = mi.get_config()
                del c.dicom_filenames[:]
                c.dicom_filenames.extend(filenames)
                mi.set_config(c)

                return True

            elif hasattr(c, 'filename'):
                c = mi.get_config()
                c.filename = filenames[0]
                mi.set_config(c)

                return True

            else:
                return False
                       
            
        
        actionDict = {'vti' : ('modules.readers.vtiRDR', 'filename'),
                      'vtp' : ('modules.readers.vtpRDR', 'filename'),
                      'mha' : ('modules.readers.metaImageRDR', 'filename'),
                      'mhd' : ('modules.readers.metaImageRDR', 'filename'),
                      'stl' : ('modules.readers.stlRDR', 'filename')}

        # list of tuples: (filename, errormessage)
        dropFilenameErrors = []

        # shortcut for later
        canvas = self.canvas

        # filename mod code =========================================
        # dropping a filename on an existing module will try to change
        # that module's config.filename (if it exists) to the dropped
        # filename.  if not successful, the normal logic for dropped
        # filenames applies.

        
        #g = canvas.get_glyph_on_coords(rx,ry)
        g = canvas.event.picked_cobject
        dprint("canvasDropFilename:: picked_cobject", g)
        if g:
            # returns True if glyph did something with drop...
            ret = handle_drop_on_glyph(g, filenames)
            if ret:
                return dropFilenameErrors
                
        # end filename mod code

        dcmFilenames = []
        for filename in filenames:
            if filename.lower().endswith('.dvn'):
                # we have to convert the event coords to real coords
                self._loadAndRealiseNetwork(filename, (w_x,w_y),
                                            reposition=True)

                # some DVNs contain viewer modules that take the focus
                # (due to Raise).  Here we take it back to the canvas,
                # most logical thing we can do.
                self.canvas._rwi.SetFocus()
                wx.SafeYield()



            elif filename.lower().endswith('.vtk'):
                # for this type we have to do some special handling.
                # it could be a structuredpoints or a polydata, so we
                # have to read the first few lines to determine
                
                try:
                    # read first four lines of file, fourth is what we want
                    f = file(filename)
                    for i in range(4):
                        fline = f.readline()

                    fline = fline.strip().lower()

                except Exception, e:
                    dropFilenameErrors.append(
                        (filename,
                         'Could not parse VTK file to distinguish type.'))

                else:
                    # this only executes if there was no exception
                    if fline.endswith('structured_points'):
                        createModuleOneVar(
                            'modules.readers.vtkStructPtsRDR',
                            'filename', filename,
                            os.path.basename(filename))
                        
                    elif fline.lower().endswith('polydata'):
                        createModuleOneVar(
                            'modules.readers.vtkPolyDataRDR',
                            'filename', filename,
                            os.path.basename(filename))

                    else:
                        dropFilenameErrors.append(
                            (filename,
                             'Could not distinguish type of VTK file.'))
                

            elif filename.lower().endswith('.dcm'):
                dcmFilenames.append(filename)

            else:
                ext = filename.split('.')[-1].lower()
                if ext in actionDict:
                    createModuleOneVar(actionDict[ext][0], actionDict[ext][1],
                                       filename,
                                       os.path.basename(filename))

                else:
                    dropFilenameErrors.append(
                        (filename, 'File extension not known.'))

        # ends for filename in filenames

        if len(dcmFilenames) > 0:
            (mod,glyph) = self.create_module_and_glyph(
                    w_x, w_y, 'modules.readers.DICOMReader')
            
            if mod:
                try:
                    cfg = mod.get_config()
                    cfg.dicom_filenames.extend(dcmFilenames)
                    mod.set_config(cfg)
                except Exception, e:
                    dropFilenameErrors.append(
                        ('DCM files', 'Error loading DICOM files: %s.' % 
                         (str(e),)))

        return dropFilenameErrors

    def close(self):
        """This gracefull takes care of all graphEditor shutdown and is mostly
        called at application shutdown.
        """

        # remove the observer we have placed on the network manager
        self._devide_app.network_manager.remove_observer(
                'execute_network_start',
                self._observer_network_manager_ens)

        # make sure no refs are stuck in the selection
        self._selected_glyphs.close()
        # this should take care of just about everything!
        self.clearAllGlyphsFromCanvas()

        # this will take care of all cleanup (including the VTK stuff)
        # and then Destroy() the main WX window.
        self._interface._main_frame.close()

    def _appendEditCommands(self, pmenu, eventWidget, origin, disable=True):
        """Append copy/cut/paste/delete commands and the default handlers
        to a given menu.  Origin is used by the paste command, and should be
        the REAL canvas coordinates, i.e. with scroll position taken into
        account.
        """
        
        copyId = wx.NewId()
        ni = wx.MenuItem(pmenu, copyId, '&Copy Selected\tCtrl-C',
                        'Copy the selected glyphs into the copy buffer.')
        pmenu.AppendItem(ni)
        wx.EVT_MENU(eventWidget, copyId,
                 self._handlerCopySelected)
        if disable:
            if not self._selected_glyphs.getSelectedGlyphs():
                ni.Enable(False)
            
        cutId = wx.NewId()
        ni = wx.MenuItem(pmenu, cutId, 'Cu&t Selected\tCtrl-X',
                        'Cut the selected glyphs into the copy buffer.')
        pmenu.AppendItem(ni)
        wx.EVT_MENU(eventWidget, cutId,
                 self._handlerCutSelected)
        if disable:
            if not self._selected_glyphs.getSelectedGlyphs():
                ni.Enable(False)
            
        pasteId = wx.NewId()
        ni = wx.MenuItem(
            pmenu, pasteId, '&Paste\tCtrl-V',
            'Paste the contents of the copy buffer onto the canvas.')
        pmenu.AppendItem(ni)
        wx.EVT_MENU(eventWidget, pasteId,
                 lambda e: self._handlerPaste(e, origin))
        if disable:
            if not self._copyBuffer:
                ni.Enable(False)
        
        deleteId = wx.NewId()
        ni = wx.MenuItem(pmenu, deleteId, '&Delete Selected\tCtrl-D',
                        'Delete all selected glyphs.')
        pmenu.AppendItem(ni)
        wx.EVT_MENU(eventWidget, deleteId,
                 lambda e: self._deleteSelectedGlyphs())
        if disable:
            if not self._selected_glyphs.getSelectedGlyphs():
                ni.Enable(False)


        testId = wx.NewId()
        ni = wx.MenuItem(pmenu, testId, 'Test Selected',
                        'Test all selected glyphs.')
        pmenu.AppendItem(ni)
        wx.EVT_MENU(eventWidget, testId,
                 lambda e: self._testSelectedGlyphs())
        if disable:
            if not self._selected_glyphs.getSelectedGlyphs():
                ni.Enable(False)

    def _append_network_commands(self, pmenu, eventWidget, disable=True):
        """Append copy/cut/paste/delete commands and the default handlers
        to a given menu.  
        """

        #############################################################
        execute_id = wx.NewId()
        ni = wx.MenuItem(pmenu, execute_id, 'E&xecute network\tF5',
                         'Execute the complete network.')
        pmenu.AppendItem(ni)
        wx.EVT_MENU(eventWidget, execute_id,
                    self._handler_execute_network)

        #############################################################
        execute_selected_id = wx.NewId()
        ni = wx.MenuItem(pmenu, execute_selected_id,
                         'E&xecute selected modules',
                         'Execute only the selected modules.')
        pmenu.AppendItem(ni)
        wx.EVT_MENU(eventWidget, execute_selected_id,
                    self._handler_execute_selected)

        if disable:
            if not self._selected_glyphs.getSelectedGlyphs():
                ni.Enable(False)

        ############################################################# 
        block_id = wx.NewId()
        ni = wx.MenuItem(pmenu, block_id, '&Block Selected\tCtrl-B',
                         'Block selected modules from executing.')
        pmenu.AppendItem(ni)
        wx.EVT_MENU(eventWidget, block_id,
                    self._handler_blockmodules)

        if disable:
            if not self._selected_glyphs.getSelectedGlyphs():
                ni.Enable(False)
            
        #############################################################
        unblock_id = wx.NewId()
        ni = wx.MenuItem(pmenu, unblock_id, '&Unblock Selected\tCtrl-U',
                         'Unblock selected modules so that they can execute.')
        pmenu.AppendItem(ni)
        wx.EVT_MENU(eventWidget, unblock_id,
                    self._handler_unblockmodules)

        if disable:
            if not self._selected_glyphs.getSelectedGlyphs():
                ni.Enable(False)

        #############################################################
        if False:
            layout_sucky_id = wx.NewId()
            ni = wx.MenuItem(pmenu, layout_sucky_id, 'Sucky graph layout\tF7',
                             'Perform SUCKY(tm) graph layout.')
            pmenu.AppendItem(ni)
            wx.EVT_MENU(eventWidget, layout_sucky_id,
                    lambda e: self._layout_network_sucky())

        reset_graph_view_id = wx.NewId()
        ni = wx.MenuItem(pmenu, reset_graph_view_id, 
        'Reset Graph Canvas view\tCtrl-R', 
        'Reset Graph Canvas view so that whole network is visible.')
        pmenu.AppendItem(ni)
        wx.EVT_MENU(eventWidget, reset_graph_view_id,
                lambda e: self.canvas.reset_view())


    def _testSelectedGlyphs(self):
        si = [i.moduleInstance
              for i in self._selected_glyphs.getSelectedGlyphs()]

    def createGlyph(self, rx, ry, labelList, moduleInstance):
        """Create only a glyph on the canvas given an already created
        moduleInstance.  labelList is a list of strings that will be printed
        inside the glyph representation.  The glyph instance is returned.

        @param rx,ry: world coordinates of new glyph.
        """
        
        co = DeVIDECanvasGlyph(self.canvas, (rx, ry),
                          len(moduleInstance.get_input_descriptions()),
                          len(moduleInstance.get_output_descriptions()),
                          labelList, moduleInstance)
        
        self.canvas.add_object(co)


        co.add_observer('motion', self._observer_glyph_motion)
                    
        co.add_observer('left_button_down',
                       self._observer_glyph_left_button_down)
        co.add_observer('right_button_down',
                       self._observer_glyph_right_button_down)
        co.add_observer('left_button_up',
                       self._observer_glyph_left_button_up)
        co.add_observer('dragging',
                       self._observer_glyph_dragging)
        co.add_observer('left_button_dclick',
                       self._observer_glyph_left_button_dclick)

        # make sure we are redrawn.
        self.canvas.redraw()

        # the network loading needs this
        return co
    
    def create_module_and_glyph(self, x, y, moduleName):
        """Create a DeVIDE and a corresponding glyph at world
        coordinates x,y.

        @return: a tuple with (module_instance, glyph) if successful, (None,
        None) if not.
        """
        
        # check that it's a valid module name
        if moduleName in self._availableModules:
            # we have a valid module, we should try and instantiate
            mm = self._devide_app.get_module_manager()
            try:
                temp_module = mm.createModule(moduleName)
            except ModuleManagerException, e:
                self._devide_app.log_error_with_exception(
                    'Could not create module %s: %s' % (moduleName, str(e)))
                return (None, None)
                
            # if the module_manager did its trick, we can make a glyph
            if temp_module:

                # the modulemanager generates a random module name, which
                # we can query with mm.get_instance_name(temp_module).  However,
                # this is a new module, so we don't actually display the name
                # in the glyph label.
                gLabel = [moduleName.split('.')[-1]]
                glyph = self.createGlyph(x,y,gLabel,temp_module)

                # route all lines
                self._route_all_lines()

                return (temp_module, glyph)

    def _execute_module(self, moduleInstance):
        """Ask the moduleManager to execute the devide module represented by
        the parameter moduleInstance.
        """
        
        mm = self._devide_app.get_module_manager()
        mm.execute_module(moduleInstance)

    def _module_doc_to_html(self, full_module_name, doc):
        # do rudimentary __doc__ -> html conversion
        docLines = string.split(doc.strip(), '\n')
        for idx in range(len(docLines)):
            docLine = docLines[idx].strip()
            if docLine == '':
                docLines[idx] = '<br><br>'

        # add pretty heading
        htmlDoc = '<center><b>%s</b></center><br><br>' % \
                  (full_module_name,) + string.join(docLines, '\n')

        # finally change the contents of the new/existing module help window
        return '<html><body>%s</body></html>' % (htmlDoc,)
        
	

    def fillModuleLists(self, scan_modules=True):
        """Build up the module tree from the list of available modules
        supplied by the moduleManager.  At the moment, things will look
        a bit strange if the module tree goes deeper than one level, but
        everything will still work.
        """

        mm = self._devide_app.get_module_manager()
        if scan_modules:
            mm.scanModules()
            
        self._availableModules = mm.getAvailableModules()

        self._moduleCats = {}
        # let's build up new dictionary with categoryName as key and
        # list of complete moduleNames as value - check for 'Segments',
        # that's reserved
        for mn,module_metadata in self._availableModules.items():
            # we add an ALL category implicitly to all modules
            for cat in module_metadata.cats + ['ALL']:
                if cat in self._moduleCats:
                    self._moduleCats[cat].append('module:%s' % (mn,))
                else:
                    self._moduleCats[cat] = ['module:%s' % (mn,)]


        # list of DVN filenames
        if len(mm.availableSegmentsList) > 0:
            self._moduleCats['Segments'] = ['segment:%s' % (i,) for i in
                                            mm.availableSegmentsList]
            # this should add all segments to the 'ALL' category
            self._moduleCats['ALL'] += self._moduleCats['Segments']

        # setup all categories
        self._interface._main_frame.module_cats_list_box.Clear()
        idx = 0

        cats = self._moduleCats.keys()
        cats.sort()

        # but make sure that ALL is up front, no matter what
        del cats[cats.index('ALL')]
        cats = ['ALL'] + cats

        for cat in cats:
            self._interface._main_frame.module_cats_list_box.Append(cat)

        self._interface._main_frame.module_cats_list_box.Select(0)

        #self._handlerModuleCatsListBoxSelected(None)
        self._update_search_results()

    def find_glyph(self, meta_module):
        """Given a meta_module, return the glyph that contains it.

        @return: glyph if found, None otherwise.
        """

        all_glyphs = self.canvas.getObjectsOfClass(DeVIDECanvasGlyph)

        found = False
        for glyph in all_glyphs:
            if glyph.moduleInstance == meta_module.instance:
                found = True
                break # get out of this for

        if found:
            return glyph
        else:
            return None

    def _handlerGraphFrameClose(self, event):
        self.hide()

    def show(self):
        # this is BAD.  why is the graph editor doing all of this and
        # not the interface?
        self._interface._main_frame.Show(True)
        self._interface._main_frame.Iconize(False)
        self._interface._main_frame.Raise()
        self.canvas.redraw()
        # we have to call into wx to get everything to actually
        # display.
        wx.SafeYield()

    def _handlerFileExportAsDOT(self, event):
        # make a list of all glyphs
        allGlyphs = self.canvas.getObjectsOfClass(DeVIDECanvasGlyph)
        
        if allGlyphs:
            filename = wx.FileSelector(
                "Choose filename for GraphViz DOT file",
                self._last_fileselector_dir, "", "dot",
                "GraphViz DOT files (*.dot)|*.dot|All files (*.*)|*.*",
                wx.SAVE)
        
            if filename:
                # save directory for future use
                self._last_fileselector_dir = \
                        os.path.dirname(filename)

                # if the user has NOT specified any fileextension, we
                # add .dot.  (on Win this gets added by the
                # FileSelector automatically, on Linux it doesn't)
                if os.path.splitext(filename)[1] == '':
                    filename = '%s.dot' % (filename,)

                self._exportNetworkAsDOT(allGlyphs, filename)

    def _handlerFileExportSelectedAsDOT(self, event):
        glyphs = self._selected_glyphs.getSelectedGlyphs()
        if glyphs:
            filename = wx.FileSelector(
                "Choose filename for GraphViz DOT file",
                self._last_fileselector_dir, "", "dot",
                "GraphViz DOT files (*.dot)|*.dot|All files (*.*)|*.*",
                wx.SAVE)
                    
            if filename:
                # save directory for future use
                self._last_fileselector_dir = \
                        os.path.dirname(filename)

                # if the user has NOT specified any fileextension, we
                # add .dot.  (on Win this gets added by the
                # FileSelector automatically, on Linux it doesn't)
                if os.path.splitext(filename)[1] == '':
                    filename = '%s.dot' % (filename,)

                self._exportNetworkAsDOT(glyphs, filename)
    

    def _handlerFileOpenSegment(self, event):
        filename = wx.FileSelector(
            "Choose DeVIDE network to load into copy buffer",
            self._last_fileselector_dir, "", "dvn",
            "DeVIDE networks (*.dvn)|*.dvn|All files (*.*)|*.*",
            wx.OPEN)
        
        if filename:
            # save directory for future use
            self._last_fileselector_dir = \
                    os.path.dirname(filename)

            self._loadNetworkIntoCopyBuffer(filename)

    def _handlerFileSaveSelected(self, event):
        glyphs = self._selected_glyphs.getSelectedGlyphs()
        if glyphs:
            filename = wx.FileSelector(
                "Choose filename for DeVIDE network",
                self._last_fileselector_dir, "", "dvn",
                "DeVIDE networks (*.dvn)|*.dvn|All files (*.*)|*.*",
                wx.SAVE)
                    
            if filename:
                # save directory for future use
                self._last_fileselector_dir = \
                        os.path.dirname(filename)

                # if the user has NOT specified any fileextension, we
                # add .dvn.  (on Win this gets added by the
                # FileSelector automatically, on Linux it doesn't)
                if os.path.splitext(filename)[1] == '':
                    filename = '%s.dvn' % (filename,)

                self._saveNetwork(glyphs, filename)

    def _update_search_results(self, event=None):
        """Each time the user modifies the module search string or the
        category selection, this method is called to update the list of
        modules that can be selected.
        """

        mf = self._interface._main_frame

        # get complete search results for this search string
        t = mf.search.GetValue()
        if t:
            mm = self._devide_app.get_module_manager()
            search_results = mm.module_search.find_matches(t)
            # search_results is dictionary {'name' : {'module.name' : 1,
            # 'other.module.name' : 1}, 'keywords' : ...

        else:
            # None is different from an empty dictionary
            search_results = None

        mclb = mf.module_cats_list_box
        sels = mclb.GetSelections()

        selectedCats = {}
        for sel in sels:
            selectedCats[mclb.GetString(sel)] = 1

        results_disp = {'misc' : [], 'name' : [],
                        'keywords' : [], 'help' : []}        

        # now go through search results adding all modules that have
        # the correct categories
        if search_results is not None:
            
            for srkey in search_results:
                # srkey is a full module name and is guaranteed to be unique
                cat_found = False
                if 'ALL' in selectedCats:
                    # we don't have to check categories
                    cat_found = True
                    
                else:
                    if srkey.startswith('segment:'):
                        if 'Segments' in selectedCats:
                            cat_found = True
                            
                    else:
                        # srkey starts with module: or segment:, we have to
                        # remove this
                        module_name = srkey.split(':')[1]
                        for c in mm._availableModules[module_name].cats:
                            if c in selectedCats:
                                cat_found = True
                                # stop with for iteration
                                break

                if cat_found:
                    # now go through the different where-founds
                    # wfs is a dict {'wf1' : 1, 'wf2' : 1}
                    wfs = search_results[srkey]
                    for wf in wfs:
                        results_disp[wf].append('%s' % (srkey,))

        else: # no search string, only selected categories
            uniq_dict = {}
            for cat in selectedCats:
                for mn in self._moduleCats[cat]:
                    # the dict eliminates duplicates
                    # we set value to 'cat' so we can later check whether this
                    # thing is a segment
                    uniq_dict[mn] = 1

            results_disp['misc'] = uniq_dict.keys()

        # make sure separate results are sorted
        for where_found in results_disp:
            results_disp[where_found].sort()

        # now populate the mlb
        mlb = mf.module_list_box
        mlb.Clear()

        for section in ['misc', 'name', 'keywords', 'help']:
            if section != 'misc' and len(results_disp[section]) > 0:
                mlb.Append('<b><center>- %s match -</center></b>' %
                           (section.upper(),), data=None,
                           refresh=False)
                
            for mn in results_disp[section]:

                if mn.startswith('segment'):
                    shortname = os.path.splitext(os.path.basename(mn))[0]

                else:
                    mParts = mn.split('.')
                    shortname = mParts[-1]
                
                mlb.Append(shortname, mn, refresh=False)

        # make sure the list is actually updated (we've appended a bunch
        # of things with refresh=False
        mlb.DoRefresh()

        # and select the first selectable item in the mlb
        # only the actual modules and segments have module_names
        sel = -1
        module_name = None
        while module_name is None and sel < mlb.GetCount():
            module_name = mlb.GetClientData(sel)
            sel += 1

        if module_name:
            # this setselection does not fire the listbox event
            mlb.SetSelection(sel-1)
            # so we call the handler manually (so help is updated)
            self._handlerModulesListBoxSelected(None)

    def _handler_inject_module(self, module_instance):
        pyshell = self._devide_app.get_interface()._python_shell
        if not pyshell:
            self._devide_app.get_interface().log_message(
            'Please activate Python Shell first.')
            return

        mm = self._devide_app.get_module_manager()
        bname = wx.GetTextFromUser(
                'Enter a name to which the instance should be bound.',
                'Input text',
                mm.get_instance_name(module_instance))

        # we inject a weakref to the module, so that it can still be
        # destroyed when the user wishes to do that.
        if bname:
            pyshell.inject_locals(
                    {bname : weakref.proxy(module_instance)})

    def _reload_module(self, module_instance, glyph):
        """Reload a module by storing all configuration information, deleting
        the module, and then recreating and reconnecting it.

        @param module_instance: the instance that's to be reloaded.
        @param glyph: the glyph that represents the module.
        """
        
        mm = self._devide_app.get_module_manager()
        meta_module = mm.get_meta_module(module_instance)

        # prod_tuple contains a list of (prod_meta_module, output_idx,
        # input_idx) tuples
        prod_tuples = mm.getProducers(meta_module)
        # cons_tuples contains a list of (output_index, consumer_meta_module,
        # consumer input index)
        cons_tuples = mm.getConsumers(meta_module)
        # store the instance name
        instance_name = meta_module.instanceName
        # and the full module spec name
        full_name = meta_module.module_name
        # and get the module state (we make a deep copy just in case)
        module_config = copy.deepcopy(meta_module.instance.get_config())
        # and even the glyph position
        gp_x, gp_y = glyph.get_position()

        # now disconnect and nuke the old module
        self._deleteModule(glyph)

        # FIXME: error checking
        # create a new one (don't convert my coordinates)
        new_instance, new_glyph = self.create_module_and_glyph(
            gp_x, gp_y, full_name)

        if new_instance and new_glyph:
            # give it its name back
            self._renameModule(new_instance, new_glyph, instance_name)

            try:
                # and its config (FIXME: we should honour pre- and
                # post-connect config!)
                new_instance.set_config(module_config)
                
            except Exception, e:
                self._devide_app.log_error_with_exception(
                    'Could not restore state/config to module %s: %s' %
                    (new_instance.__class__.__name__, e)                    
                    )

            # connect it back up
            for producer_meta_module, output_idx, input_idx in prod_tuples:
                producer_glyph = self.find_glyph(producer_meta_module)
                # connect reports the error internally, so we'll just
                # continue trying to connect up things
                self._connect(producer_glyph, output_idx,
                              new_glyph, input_idx)

            for output_idx, consumer_meta_module, input_idx in cons_tuples:
                consumer_glyph = self.find_glyph(consumer_meta_module)
                self._connect(new_glyph, output_idx,
                              consumer_glyph, input_idx)

        self.canvas.redraw()

        wx.SafeYield()


    def _renameModule(self, module, glyph, newModuleName):
        if newModuleName:
            # try to rename the module...
            if self._devide_app.get_module_manager().renameModule(
                module,newModuleName):

                # if no conflict, set label and redraw
                ll = [module.__class__.__name__]
                if not newModuleName.startswith('dvm'):
                    ll.append(newModuleName)

                # change the list of labels
                glyph.setLabelList(ll)
                # which means we have to update the geometry (so they
                # are actually rendered)
                glyph.update_geometry()
                # which means we probably have to reroute lines as the
                # module might have changed size
                self._route_all_lines()

                self.canvas.redraw()

                return True
            
            else:
                # there was a conflict, return false
                return False

        else:
            # the user has given us a blank or None modulename... we'll rename
            # the module with an internal random name and remove its label
            uin = self._devide_app.get_module_manager()._makeUniqueInstanceName()
            rr = self._devide_app.get_module_manager().renameModule(module, uin)
            if rr:
                glyph.setLabelList([module.__class__.__name__])
                self.canvas.redraw()
                return True

            else:
                return False

    def _handler_reload_module(self, module_instance, glyph):
        self._reload_module(module_instance, glyph)
        
                
    def _handlerRenameModule(self, module, glyph):
        newModuleName = wx.GetTextFromUser(
            'Enter a new name for this module.',
            'Rename Module',
            self._devide_app.get_module_manager().get_instance_name(module))

        if newModuleName:
            self._renameModule(module, glyph, newModuleName)

    def _handlerModulesListBoxSelected(self, event):
        mlb = self._interface._main_frame.module_list_box
        idx = mlb.GetSelection()

        if idx >= 0:
            cdata = mlb.GetClientData(idx)
            if cdata is not None:
                self._interface._main_frame.GetStatusBar().SetStatusText(cdata)

            self.show_module_help(cdata)

    def _handlerPaste(self, event, position):
        if self._copyBuffer:
            self._realiseNetwork(
                # when we paste, we want the thing to reposition!
                self._copyBuffer[0], self._copyBuffer[1], self._copyBuffer[2],
                position, True)

    def _handlerHelpShowHelp(self, event):
        self._interface.showHelp()
            
    def _handlerCopySelected(self, event):
        if self._selected_glyphs.getSelectedGlyphs():
            self._copyBuffer = self._serialiseNetwork(
                self._selected_glyphs.getSelectedGlyphs())

    def _handlerCutSelected(self, event):
        if self._selected_glyphs.getSelectedGlyphs():
            self._copyBuffer = self._serialiseNetwork(
                self._selected_glyphs.getSelectedGlyphs())
        
            self._deleteSelectedGlyphs()

    def hide(self):
        self._interface._main_frame.Show(False)

    def _draw_preview_line(self, src, dst):
        """Draw / update a preview line from 3-D world position src to
        dst.
        """

        if self._preview_line is None:
            self._preview_line = DeVIDECanvasSimpleLine(self.canvas, src, dst)
            self.canvas.add_object(self._preview_line)

        else:
            self._preview_line.src = src
            self._preview_line.dst = dst
            self._preview_line.update_geometry()

        self.canvas.redraw() # this shouldn't be here...

    def _kill_preview_line(self):
        if not self._preview_line is None:
            self.canvas.remove_object(self._preview_line)
            self._preview_line.close()
            self._preview_line = None

    def _draw_rubberband(self, cur_pos):
        if self._rbb_box is None:
            self._rbb_box = DeVIDECanvasRBBox(self.canvas, cur_pos,
                    (0.1,0.1))
            self.canvas.add_object(self._rbb_box)

        else:
            # just update the width and the height!
            # (these can be negative)
            w = cur_pos[0] - self._rbb_box.corner_bl[0]
            h = cur_pos[1] - self._rbb_box.corner_bl[1]
            self._rbb_box.width, self._rbb_box.height = w,h

            self._rbb_box.update_geometry()

    def _end_rubberbanding(self):
        """See stopRubberBanding: we need some more data!

        actually we don't: we have self.canvas too (with an
        event.wx_event)
        """
        
        if not self._rbb_box is None:
            # store coords of rubber-band box
            c_bl = self._rbb_box.corner_bl
            w = self._rbb_box.width
            h = self._rbb_box.height

            # remove it from the canvas
            self.canvas.remove_object(self._rbb_box)
            self._rbb_box.close()
            self._rbb_box = None

            # now determine which glyphs were inside
            all_glyphs = self._get_all_glyphs()
            glyphs_in_rb = []
            for g in all_glyphs:
                if g.is_inside_rect(c_bl, w, h):
                    glyphs_in_rb.append(g)

            wxe = self.canvas.event.wx_event
            if not wxe.ControlDown() and not wxe.ShiftDown():
                self._selected_glyphs.removeAllGlyphs()

            for g in glyphs_in_rb:
                self._selected_glyphs.addGlyph(g)



    def _disconnect(self, glyph, inputIdx):
        """Disconnect inputIdx'th input of glyph, also remove line
        from canvas.
        """

        try:
            # first disconnect the actual modules
            mm = self._devide_app.get_module_manager()
            mm.disconnectModules(glyph.moduleInstance, inputIdx)

        except Exception, e:
            self._devide_app.log_error_with_exception(
                'Could not disconnect modules (removing link '
                'from canvas anyway): %s' \
                % (str(e)))

        # we did our best, the module didn't want to comply
        # we're going to nuke it anyway
        deadLine = glyph.inputLines[inputIdx]
        if deadLine:
            # remove the line from the destination module input lines
            glyph.inputLines[inputIdx] = None
            # and for the source module output lines
            outlines = deadLine.fromGlyph.outputLines[
                deadLine.fromOutputIdx]
            del outlines[outlines.index(deadLine)]

            # also update geometry on both glyphs
            glyph.update_geometry()
            deadLine.fromGlyph.update_geometry()
            
            # and from the canvas
            self.canvas.remove_object(deadLine)
            deadLine.close()

            
            
    def _observer_canvas_left_down(self, canvas):
        """If user left-clicks on canvas and there's a selection, the
        selection should be canceled.  However, if control or shift is
        being pressed, it could mean the user is planning to extend a
        selection with for example a rubber-band drag.
        """
        
        wxe = canvas.event.wx_event
        if not wxe.ControlDown() and not wxe.ShiftDown() and \
            len(self._selected_glyphs.getSelectedGlyphs()) > 0:
            self._selected_glyphs.removeAllGlyphs()
            self.canvas.update_all_geometry()
            self.canvas.redraw()


    def _observer_canvas_right_down(self, canvas):
        pmenu = wx.Menu('Canvas Menu')

        # fill it out with edit (copy, cut, paste, delete) commands
        self._appendEditCommands(pmenu, canvas._rwi,
                (canvas.event.world_pos[0:2]))

        pmenu.AppendSeparator()

        self._append_network_commands(pmenu, canvas._rwi)
        

        self.canvas._rwi.PopupMenu(pmenu, 
                wx.Point(canvas.event.pos[0], 
                    canvas.event.pos[1]))


    def _observer_canvas_left_up(self, canvas):
        dprint("_observer_canvas_left_up::")
        
        # whatever the case may be, stop rubber banding.
        if self._rbb_box:
            self._end_rubberbanding()
            # this might mean double redraws, cache it?
            self.canvas.redraw()

        # any dragged objects?
        if canvas.getDraggedObject() and \
               canvas.getDraggedObject().draggedPort and \
               canvas.getDraggedObject().draggedPort != (-1,-1):

            if canvas.getDraggedObject().draggedPort[0] == 0:
                # the user was dragging an input port and dropped it
                # on the canvas, so she probably wants us to disconnect
                inputIdx = canvas.getDraggedObject().draggedPort[1]
                self._disconnect(canvas.getDraggedObject(),
                                 inputIdx)

            # we were dragging a port, so there was a preview line,
            # which we now can discard
            self._kill_preview_line()

            self.canvas.redraw()



    def _observer_canvas_drag(self, canvas):
        if canvas.event.left_button:
            self._draw_rubberband(canvas.event.world_pos)
            canvas.redraw()

    def _checkAndConnect(self, draggedObject, draggedPort,
                         droppedObject, droppedInputPort):
        """Check whether the proposed connection can be made and make
        it.  Also takes care of putting a new connection line on the
        canvas, and redrawing.
        """

        if droppedObject.inputLines[droppedInputPort]:
            # the user dropped us on a connected input, we can just bail
            return
            
        if draggedPort[0] == 1:
            # this is a good old "I'm connecting an output to an input"
            self._connect(draggedObject, draggedPort[1],
                          droppedObject, droppedInputPort)
            
            self.canvas.redraw()

        elif draggedObject.inputLines[draggedPort[1]]:
            # this means the user was dragging a connected input port and has
            # now dropped it on another input port... (we've already eliminated
            # the case of a drop on an occupied input port, and thus also
            # a drop on the dragged port)

            oldLine = draggedObject.inputLines[draggedPort[1]]
            fromGlyph = oldLine.fromGlyph
            fromOutputIdx = oldLine.fromOutputIdx
            toGlyph = oldLine.toGlyph
            toInputIdx = oldLine.toInputIdx

            # delete the old one
            self._disconnect(toGlyph, toInputIdx)

            # connect up the new one
            self._connect(fromGlyph, fromOutputIdx,
                          droppedObject, droppedInputPort)

            self.canvas.redraw()
    def _observer_network_manager_ens(self, network_manager):
        """Autosave file, only if we have a _current_filename
        """

        if self._current_filename is None:
            return

        all_glyphs = self.canvas.getObjectsOfClass(
            DeVIDECanvasGlyph)

        if all_glyphs:
            # create new filename
            fn = self._current_filename
            f, e = os.path.splitext(fn)
            new_fn = '%s_autosave%s' % (f, e)

            # auto-save the network to that file
            self._saveNetwork(all_glyphs, new_fn)

            msg1 = 'Auto-saved %s' % (new_fn,)
            # set message on statusbar
            self._interface.set_status_message(
                    '%s - %s' % 
                    (msg1,time.ctime(time.time())))
            # and also in log window
            self._interface.log_info(msg1)
       

    def clearAllGlyphsFromCanvas(self):
        allGlyphs = self.canvas.getObjectsOfClass(DeVIDECanvasGlyph)

        mm = self._devide_app.get_module_manager()

        # we take care of the "difficult" modules first, so sort module
        # types from high to low
        maxConsumerType = max(mm.consumerTypeTable.values())

        # go through consumerTypes from high to low, building up a list
        # with glyph in the order that we should destroy them
        # we should probably move this logic to the moduleManager as a
        # method getModuleDeletionOrder() or somesuch
        glyphDeletionSchedule = []
        for consumerType in range(maxConsumerType, -1, -1):
            for glyph in allGlyphs:
                moduleClassName = glyph.moduleInstance.__class__.__name__
                if moduleClassName in mm.consumerTypeTable:
                    currentConsumerType = mm.consumerTypeTable[
                        moduleClassName]
                    
                else:
                    # default filter
                    currentConsumerType = 1

                if currentConsumerType == consumerType:
                    glyphDeletionSchedule.append(glyph)

        # now actually delete the glyphs in the correct order
        for glyph in glyphDeletionSchedule:
            self._deleteModule(glyph)

        # only here!
        self.canvas.redraw()

    def _createLine(self, fromObject, fromOutputIdx, toObject, toInputIdx):
        l1 = DeVIDECanvasLine(self.canvas, fromObject, fromOutputIdx,
                         toObject, toInputIdx)
        dprint("_createLine:: calling canvas.add_object")
        self.canvas.add_object(l1)
            
        # also record the line in the glyphs
        toObject.inputLines[toInputIdx] = l1
        fromObject.outputLines[fromOutputIdx].append(l1)

        # REROUTE THIS LINE
        self._route_line(l1)

    def _connect(self, fromObject, fromOutputIdx,
                 toObject, toInputIdx):

        success = True
        try:
            # connect the actual modules
            mm = self._devide_app.get_module_manager()
            mm.connectModules(fromObject.moduleInstance, fromOutputIdx,
                              toObject.moduleInstance, toInputIdx)

            # if that worked, we can make a linypoo
            self._createLine(fromObject, fromOutputIdx, toObject, toInputIdx)

            # have to call update_geometry (the glyphs have new
            # colours!)
            fromObject.update_geometry()
            toObject.update_geometry()

        except Exception, e:
            success = False
            self._devide_app.log_error_with_exception(
                'Could not connect modules: %s' % (str(e)))

        return success

    def _deleteSelectedGlyphs(self):
        """Delete all currently selected glyphs.
        """

        # we have to make a deep copy, as we're going to be deleting stuff
        # from this list
        deadGlyphs = [glyph for glyph in \
                      self._selected_glyphs.getSelectedGlyphs()]
        
        for glyph in deadGlyphs:
            # delete the glyph, do not refresh the canvas
            self._deleteModule(glyph, False)

        # finally we can let the canvas redraw
        self.canvas.redraw()

    def _realiseNetwork(self, pmsDict, connectionList, glyphPosDict,
                        origin=(0,0), reposition=False):
        """Given a pmsDict, connectionList and glyphPosDict, recreate
        the network described by those structures.  The origin of the glyphs
        will be set.  If reposition is True, the uppermost and leftmost
        coordinates of all glyphs in glyphPosDict is subtracted from all
        stored glyph positions before adding the origin.
        """
        
        # get the network_manager to realise the network
        nm = self._devide_app.network_manager
        newModulesDict, newConnections = nm.realise_network(
            pmsDict, connectionList)
            
        # newModulesDict and newConnections contain the modules and
        # connections which were _actually_ realised... let's draw
        # glyphs!

        if reposition:
            coords = glyphPosDict.values()
            minX = min([coord[0] for coord in coords])
            minY = min([coord[1] for coord in coords])
            reposCoords = [minX, minY]
            
        else:
            reposCoords = [0, 0]

        # store the new glyphs in a dictionary keyed on OLD pickled
        # instanceName so that we can connect them up in the next step
        mm = self._devide_app.get_module_manager()
        newGlyphDict = {} 
        for newModulePickledName in newModulesDict.keys():
            position = glyphPosDict[newModulePickledName]
            moduleInstance = newModulesDict[newModulePickledName]
            gLabel = [moduleInstance.__class__.__name__]
            instname = mm.get_instance_name(moduleInstance)
            if not instname.startswith('dvm'):
                gLabel.append(instname)
                
            newGlyph = self.createGlyph(
                position[0] - reposCoords[0] + origin[0],
                position[1] - reposCoords[1] + origin[1],
                gLabel,
                moduleInstance)
            newGlyphDict[newModulePickledName] = newGlyph

        # now make lines for all the existing connections
        # note that we use "newConnections" and not connectionList
        for connection in newConnections:
            sGlyph = newGlyphDict[connection.sourceInstanceName]
            tGlyph = newGlyphDict[connection.targetInstanceName]
            self._createLine(sGlyph, connection.outputIdx,
                             tGlyph, connection.inputIdx)

        # finally we can let the canvas redraw
        self.canvas.update_all_geometry()
        self.canvas.redraw()

    def _layout_network_sucky(self):

        # I've done it this way so that I can easily paste this method
        # into the main DeVIDE introspection window.

        #from internal.wxPyCanvas import wxpc
        iface = self._interface
        #iface = devide_app.get_interface()
        canvas = self.canvas
        ge = iface._graph_editor
        mm = self._devide_app.get_module_manager()
        #mm = devide_app.get_module_manager()

        

        all_glyphs = self.canvas.getObjectsOfClass(
            DeVIDECanvasGlyph)
        num_glyphs = len(all_glyphs)

        # we can only do this if we have more than one glyph to
        # move around.
        if num_glyphs <= 1:
            return

        (pmsDict, connection_list, glyphPosDict) = \
                  ge._serialiseNetwork(all_glyphs)

        # first convert all glyph positions to points and connections
        # to polylines.
        polynet = vtk.vtkPolyData()
        points = vtk.vtkPoints()
        points.Allocate(num_glyphs, 10)
        lines = vtk.vtkCellArray()
        lines.Allocate(len(connection_list), 10)

        # for each glyph, we store in a dict its pointid in the
        # polydata
        name2ptid = {}
        ptid2glyph = {}


        for glyph in all_glyphs:
            pos = glyph.get_position()

            new_pos = pos + (0.0,)
            ptid = points.InsertNextPoint(new_pos)
            instance_name = mm.get_instance_name(glyph.moduleInstance)
            name2ptid[instance_name] = ptid
            ptid2glyph[ptid] = glyph

        condone = {} # we use this dict to add each connection once
        for connection in connection_list:
            prod_ptid = name2ptid[connection.sourceInstanceName]
            cons_ptid = name2ptid[connection.targetInstanceName]

            # we keep this for now, we want the number of connections
            # between two modules to play a role in the layout.
            #if (prod_ptid, cons_ptid) in condone:
            #    continue
            #else:
            #    condone[(prod_ptid, cons_ptid)] = 1

            v = vtk.vtkIdList()
            v.InsertNextId(prod_ptid)
            v.InsertNextId(cons_ptid)
            lines.InsertNextCell(v)

        # we can also add an extra connection from each glyph to EVERY
        # other glyph to keep things more balanced...  (SIGH)
        for iglyph in all_glyphs:
            iptid = name2ptid[mm.get_instance_name(iglyph.moduleInstance)]
            for jglyph in all_glyphs:
                if iglyph is not jglyph:
                    jptid = name2ptid[mm.get_instance_name(jglyph.moduleInstance)]
                    v = vtk.vtkIdList()
                    v.InsertNextId(iptid)
                    v.InsertNextId(jptid)
                    lines.InsertNextCell(v)


        polynet.SetPoints(points)
        polynet.SetLines(lines)

        lf = vtk.vtkGraphLayoutFilter()
        lf.SetThreeDimensionalLayout(0)
        lf.SetAutomaticBoundsComputation(0)
        minx, miny = canvas.GetViewStart()[0] + 50, canvas.GetViewStart()[1] + 50

        maxx, maxy = canvas.GetClientSize()[0] + minx - 100, canvas.GetClientSize()[1] + miny - 100
        lf.SetGraphBounds(minx, maxx, miny, maxy, 0.0, 0.0)

        # i've tried a number of things, they all suck.
        lf.SetCoolDownRate(1000) # default 10
        lf.SetMaxNumberOfIterations(10) # default 50

        lf.SetInput(polynet)
        lf.Update()

        new_pts = lf.GetOutput()
        for ptid, glyph in ptid2glyph.items():
            new_pos = new_pts.GetPoint(ptid)
            glyph.setPosition(new_pos[0:2]) 

        ge._route_all_lines()

    def _loadAndRealiseNetwork(self, filename, position=(0,0),
                               reposition=False):
        """Attempt to load (i.e. unpickle) a DVN network file and recreate
        this network on the canvas.

        @param position: start position of new network in world
        coordinates.
        """

        try:
            ln = self._devide_app.network_manager.load_network
            pmsDict, connectionList, glyphPosDict = ln(filename)
            self._realiseNetwork(pmsDict, connectionList, glyphPosDict,
                                 position, reposition)
        except Exception, e:
            self._devide_app.log_error_with_exception(str(e))

    def _loadNetworkIntoCopyBuffer(self, filename):
        """Attempt to load (i.e. unpickle) a DVN network and bind the
        tuple to self._copyBuffer.  When the user pastes, the network will
        be recreated.  DANG!
        """

        try:
            ln = self._devide_app.network_manager.load_network
            pmsDict, connectionList, glyphPosDict = ln(filename)
            self._copyBuffer = (pmsDict, connectionList, glyphPosDict)

        except Exception, e:
            self._devide_app.log_error_with_exception(str(e))


    def _saveNetwork(self, glyphs, filename):
        (pmsDict, connectionList, glyphPosDict) = \
                  self._serialiseNetwork(glyphs)

        # change the serialised moduleInstances to a pickled stream
        headerAndData = (('DVN', 1, 0, 0), \
                        (pmsDict, connectionList, glyphPosDict))
        stream = cPickle.dumps(headerAndData, True)
            
        f = None
        try:
            f = open(filename, 'wb')
            f.write(stream)
        except Exception, e:
            self._devide_app.log_error_with_exception(
                'Could not write network to %s: %s' % (filename,
                                                       str(e)))
                                                                     
        if f:
            f.close()

    def _exportNetworkAsDOT(self, glyphs, filename):
        (pmsDict, connectionList, glyphPosDict) = \
                  self._serialiseNetwork(glyphs)

        # first work through the module instances
        dotModuleDefLines = []

        for instanceName, pickledModule in pmsDict.items():
            configKeys = [i for i in dir(pickledModule.moduleConfig) if
                          not i.startswith('__')]

            configList = []
            for configKey in configKeys:
                cValStr = str(getattr(pickledModule.moduleConfig, configKey))
                if len(cValStr) > 80:
                    cValStr = 'Compacted'

                # just replace all \'s with /'s... else we have to futz
                # with raw strings all the way through!
                configList.append('%s : %s' %
                                  (configKey,
                                   cValStr.replace('\\', '/')))

            configString = '\\n'.join(configList)
            
            
            dotModuleDefLines.append(
                '%s [shape=box, label="%s %s\\n%s"];\n' % \
                (instanceName,
                 pickledModule.moduleName,
                 instanceName,
                 configString))

        # then the connections
        # connectionList is a list of pickledConnections

        connectionLines = []
        mm = self._devide_app.get_module_manager()
        
        for connection in connectionList:

            mi = mm.get_instance(connection.sourceInstanceName)
            outputName = ''
            if mi:
                outputName = mi.get_output_descriptions()[connection.outputIdx]
                
            connectionLines.append('%s -> %s [label="%s"];\n' % \
                                   (connection.sourceInstanceName,
                                    connection.targetInstanceName,
                                    outputName
                                    ))

        f = None
        try:
            f = open(filename, 'w')

            f.write('/* GraphViz DOT file generated by DeVIDE */\n')
            f.write('/* Example: dot -Tps filename.dot -o filename.ps */\n')
            f.write('digraph DeVIDE_Network {\n')
            f.write('ratio=auto;\n');
            # a4 is 8.something by 11.something
            f.write('size="7,10";\n');
       
            f.writelines(dotModuleDefLines)
            f.writelines(connectionLines)
            f.write('}')
            
        except Exception, e:
            self._devide_app.log_error_with_exception(
                'Could not write network to %s: %s' % (filename,
                                                       str(e)))
                                                                     
        if f:
            f.close()
        
        

    def _serialiseNetwork(self, glyphs):
        """Given a list of glyphs, return a tuple containing pmsDict,
        connectionList and glyphPosDict.  This can be used to reconstruct the
        whole network from scratch and is used for saving and
        cutting/copying.

        glyphPosDict is a dictionary mapping from instance_name to
        glyph position.
        pmsDict maps from instance_name to pickledModuleState, an
        object with attributes (moduleConfig, moduleName,
        instanceName)
        connectionList is a list of pickledConnection, each containing
        (producer_instance_name, output_idx, consumer_instance_name,
        input_idx)
        """

        moduleInstances = [glyph.moduleInstance for glyph in glyphs]
        mm = self._devide_app.get_module_manager()

        # let the moduleManager serialise what it can
        pmsDict, connectionList = mm.serialiseModuleInstances(
            moduleInstances)

        savedInstanceNames = [pms.instanceName for pms in pmsDict.values()]
                                  
        # now we also get to store the coordinates of the glyphs which
        # have been saved (keyed on instanceName)
        savedGlyphs = [glyph for glyph in glyphs
                       if mm.get_instance_name(glyph.moduleInstance)\
                       in savedInstanceNames]
            
        glyphPosDict = {}
        for savedGlyph in savedGlyphs:
            instanceName = mm.get_instance_name(savedGlyph.moduleInstance)
            glyphPosDict[instanceName] = savedGlyph.get_position()

        return (pmsDict, connectionList, glyphPosDict)
        

    def update_port_info_statusbar(self, glyph, port_inout, port_idx):
        
        """This is only called if port_inout is >= 0, i.e. there is
        valid information concerning a glyph, port side and port index
        under the mouse at the moment.

        Called by _observer_glyph_motion().
        """
        
        msg = ''
        canvas = self.canvas
    
        from_port = False
        draggedObject = canvas.getDraggedObject()
        if draggedObject and draggedObject.draggedPort and \
               draggedObject.draggedPort != (-1, -1):

            if draggedObject.draggedPort[0] == 0:
                pstr = draggedObject.moduleInstance.get_input_descriptions()[
                    draggedObject.draggedPort[1]]
            else:
                pstr = draggedObject.moduleInstance.get_output_descriptions()[
                    draggedObject.draggedPort[1]]

            from_descr = '|%s|-[%s]' % (draggedObject.getLabel(), pstr)
            from_port = True

            # see if dragged port is the same as the port currently
            # under the mouse
            same_port = draggedObject == glyph and \
                    draggedObject.draggedPort[0] == port_inout and \
                    draggedObject.draggedPort[1] == port_idx

        if port_inout == 0:
            pstr = glyph.moduleInstance.get_input_descriptions()[
                port_idx]
        else:
            pstr = glyph.moduleInstance.get_output_descriptions()[
                port_idx]
             
        to_descr = '|%s|-[%s]' % (glyph.getLabel(), pstr)

        # if we have a dragged port (i.e. a source) and a port
        # currently under the mouse which is NOT the same port, show
        # the connection that the user would make if the mouse would
        # now be released.
        if from_port and not same_port:
            msg = '%s ===>> %s' % (from_descr, to_descr)

        # otherwise, just show the port under the mouse at the moment.
        else:
            msg = to_descr

        self._interface._main_frame.GetStatusBar().SetStatusText(msg)            
                                   
    def _fileExitCallback(self, event):
        # call the interface quit handler (we're its child)
        self._interface.quit()

    def _fileNewCallback(self, event):
        self.clearAllGlyphsFromCanvas()
        self.set_current_filename(None)

    def _fileOpenCallback(self, event):
        filename = wx.FileSelector(
            "Choose DeVIDE network to load",
            self._last_fileselector_dir, "", "dvn",
            "DeVIDE networks (*.dvn)|*.dvn|All files (*.*)|*.*",
            wx.OPEN)
        
        if filename:
            # save the directory part of whatever was selected for
            # future use.
            self._last_fileselector_dir = \
                    os.path.dirname(filename)

            self.clearAllGlyphsFromCanvas()
            self._loadAndRealiseNetwork(filename)
            # make sure that the newly realised network is nicely in
            # view
            self.canvas.reset_view()
            self.set_current_filename(filename)

    def _helper_file_save(self, always_ask=True):
        """Save current network to file.

        If always_ask is True, will popup a file selector dialogue.
        If always_ask is False, will only popup a file selector
        dialogue if there is no current filename set.
        """
        # make a list of all glyphs
        allGlyphs = self.canvas.getObjectsOfClass(
            DeVIDECanvasGlyph)
        
        if allGlyphs:
            if always_ask or self._current_filename is None:
                filename = wx.FileSelector(
                    "Choose filename for DeVIDE network",
                    self._last_fileselector_dir, "", "dvn",
                    "DeVIDE networks (*.dvn)|*.dvn|All files (*.*)|*.*",
                    wx.SAVE)
            else:
                filename = self._current_filename
       
            if filename:
                # save directory for future use
                self._last_fileselector_dir = \
                        os.path.dirname(filename)

                # if the user has NOT specified any fileextension, we
                # add .dvn.  (on Win this gets added by the
                # FileSelector automatically, on Linux it doesn't)
                if os.path.splitext(filename)[1] == '':
                    filename = '%s.dvn' % (filename,)

                self.set_current_filename(filename)
                self._saveNetwork(allGlyphs, filename)

                msg1 = 'Saved %s' % (filename,)
                # set message on statusbar
                self._interface.set_status_message(
                        '%s - %s' % 
                        (msg1,time.ctime(time.time())))
                # and also in log window
                self._interface.log_info(msg1)


    def _fileSaveCallback(self, event):
        self._helper_file_save(always_ask=False)

    def _handler_file_save_as(self, event):
        self._helper_file_save(always_ask=True)

    def _get_all_glyphs(self):
        """Return list with all glyphs on canvas.
        """
        ag = self.canvas.getObjectsOfClass(
            DeVIDECanvasGlyph)
        return ag
        

    def _observer_glyph_dragging(self, glyph):
        canvas = self.canvas

        # this clause will execute once at the beginning of a drag...
        if not glyph.draggedPort:
            # we're dragging, but we don't know if we're dragging a port yet
            port = glyph.get_port_containing_mouse()
            dprint("_observer_glyph_dragging:: port", port)
            if port:
                # 
                glyph.draggedPort = port
            else:
                # this indicates that the glyph is being dragged, but that
                # we don't have to check for a port during this drag
                glyph.draggedPort = (-1, -1)

        # when we get here, glyph.draggedPort CAN't BE None
        if glyph.draggedPort == (-1, -1):
            # this means that there's no port involved, so the glyph itself,
            # or the current selection of glyphs, gets dragged
            if glyph in self._selected_glyphs.getSelectedGlyphs():
                # move the whole selection (MAN THIS IS CLEAN)
                # err, kick yerself in the nads: you CAN'T use glyph
                # as iteration variable, it'll overwrite the current glyph
                for sglyph in self._selected_glyphs.getSelectedGlyphs():
                    canvas.drag_object(sglyph,
                            canvas.get_motion_vector_world(0.0))

                    # we're busy dragging glyphs, do a QUICK reroute
                    # of all lines connected to this glyph.  quick
                    # rerouting ignores all other glyphs
                    self._route_all_glyph_lines_fast(sglyph)

            else:
                # or just the glyph under the mouse
                # this clause should never happen, as the dragged glyph
                # always has the selection.
                canvas.drag_object(glyph,
                        canvas.get_motion_vector_world(0.0))

                self._route_all_glyph_lines_fast(glyph)

            # finished glyph drag event handling, have to redraw.
            canvas.redraw()
                
                
        else:
            if glyph.draggedPort[0] == 1:
                # the user is attempting a new connection starting with
                # an output port 

                cop = glyph.get_centre_of_port(glyph.draggedPort[0],
                                            glyph.draggedPort[1])
                self._draw_preview_line(cop,
                        canvas.event.world_pos)

            elif glyph.inputLines and glyph.inputLines[glyph.draggedPort[1]]:
                # the user is attempting to relocate or disconnect an input
                inputLine = glyph.inputLines[glyph.draggedPort[1]]
                cop = inputLine.fromGlyph.get_centre_of_port(
                    1, inputLine.fromOutputIdx)

                self._draw_preview_line(cop,
                                      canvas.event.world_pos)

#        if not canvas.getDraggedObject():
#            # this means that this drag has JUST been cancelled
#            if glyph.draggedPort == (-1, -1):
#                # and we were busy dragging a glyph around, so we probably
#                # want to reroute all lines!
#
#                # reroute all lines
#                allLines = self._interface._main_frame.canvas.\
#                           getObjectsOfClass(wxpc.coLine)
#
#                for line in allLines:
#                    self._route_line(line)
#
#
#            # switch off the draggedPort
#            glyph.draggedPort = None
#            # redraw everything
#            canvas.redraw()

    def _observer_glyph_motion(self, glyph):
        inout, port_idx = glyph.get_port_containing_mouse()
        if inout >= 0:
            self.update_port_info_statusbar(glyph, inout, port_idx)

    def _observer_glyph_right_button_down(self, glyph):
        module = glyph.moduleInstance
        
        pmenu = wx.Menu(glyph.getLabel())

        vc_id = wx.NewId()
        pmenu.AppendItem(wx.MenuItem(pmenu, vc_id, "View-Configure"))
        wx.EVT_MENU(self.canvas._rwi, vc_id,
                 lambda e: self._viewConfModule(module))

        help_id = wx.NewId()
        pmenu.AppendItem(wx.MenuItem(
            pmenu, help_id, "Help on Module"))
        wx.EVT_MENU(self.canvas._rwi, help_id,
                 lambda e: self.show_module_help_from_glyph(glyph))
        
        reload_id = wx.NewId()
        pmenu.AppendItem(wx.MenuItem(pmenu, reload_id, 'Reload Module'))
        wx.EVT_MENU(self.canvas._rwi, reload_id,
                    lambda e: self._handler_reload_module(module,
                                                          glyph))

        del_id = wx.NewId()
        pmenu.AppendItem(wx.MenuItem(pmenu, del_id, 'Delete Module'))
        wx.EVT_MENU(self.canvas._rwi, del_id,
                 lambda e: self._deleteModule(glyph))

        renameModuleId = wx.NewId()
        pmenu.AppendItem(wx.MenuItem(pmenu, renameModuleId, 'Rename Module'))
        wx.EVT_MENU(self.canvas._rwi, renameModuleId,
                 lambda e: self._handlerRenameModule(module,glyph))

        inject_module_id = wx.NewId()
        pmenu.AppendItem(wx.MenuItem(pmenu, inject_module_id, 
        'Module -> Python shell'))
        wx.EVT_MENU(self.canvas._rwi, inject_module_id,
                lambda e: self._handler_inject_module(module))

        pmenu.AppendSeparator()

        self._appendEditCommands(pmenu, self.canvas._rwi,
                self.canvas.event.world_pos)

        pmenu.AppendSeparator()

        self._append_network_commands(
            pmenu, self.canvas._rwi)

        # popup that menu!
        self.canvas._rwi.PopupMenu(pmenu, 
                wx.Point(self.canvas.event.pos[0],
                    self.canvas.event.pos[1]))

    def _observer_glyph_left_button_down(self, glyph):
        module = glyph.moduleInstance
        
        
        if self.canvas.event.wx_event.ControlDown() or \
                self.canvas.event.wx_event.ShiftDown():
            # with control or shift you can add or remove that glyph
            if glyph.selected:
                self._selected_glyphs.removeGlyph(glyph)
            else:
                self._selected_glyphs.addGlyph(glyph)

            self.canvas.redraw()

        else:
            # if the user already has a selection of which this is a part,
            # we're not going to muck around with that.
            if not glyph.selected:
                self._selected_glyphs.selectGlyph(glyph)

                self.canvas.redraw()
            
    def _observer_glyph_left_button_up(self, glyph):
        dprint("_observer_glyph_left_button_up::")

        if self.canvas.getDraggedObject():
            dprint("_observer_glyph_left_button_up:: draggedObject, " + 
            "draggedPort", self.canvas.getDraggedObject(),
            self.canvas.getDraggedObject().draggedPort)
        

        # whatever the case may be, stop rubber banding.
        if self._rbb_box:
            self._end_rubberbanding()
            # this might mean double redraws, cache it?
            self.canvas.redraw()

        canvas = self.canvas

        # when we receive the ButtonUp that ends the drag event, 
        # canvas.getDraggedObject is still set! - it will be unset
        # right after (by the canvas) and then the final drag event
        # will be triggered
        if canvas.getDraggedObject() and \
               canvas.getDraggedObject().draggedPort and \
               canvas.getDraggedObject().draggedPort != (-1,-1):
            # this means the user was dragging a port... so we're
            # interested
            # first get rid of the preview line...
            self._kill_preview_line()
            # and redraw the canvas so it really disappears
            # (this is also necessary when the handler will do nothing
            # otherwise, for example if the user drops us above a
            # glyph)
            self.canvas.redraw()

            pcm = glyph.get_port_containing_mouse()
            dprint("_observer_glyph_left_button_up:: pcm",pcm)
            if pcm == (-1,-1):
                # the user dropped us inside of the glyph, NOT above a port
                # if the user was dragging an input port, we have to
                # manually disconnect
                if canvas.getDraggedObject().draggedPort[0] == 0:
                    inputIdx = canvas.getDraggedObject().draggedPort[1]
                    self._disconnect(canvas.getDraggedObject(),
                                     inputIdx)
                    self.canvas.redraw()

                else:
                    # the user was dragging a port and dropped us
                    # inside a glyph... we do nothing
                    pass

            else:
                # this means the drag is ended above an input port!
                if pcm[0] == 0:
                    # ended above an INPUT port
                    # checkandconnect will route lines and redraw if
                    # required
                    self._checkAndConnect(
                        canvas.getDraggedObject(),
                        canvas.getDraggedObject().draggedPort,
                        glyph, pcm[1])

                else:
                    # ended above an output port... we can't do anything
                    # (I think)
                    pass

        if canvas.getDraggedObject() and \
        canvas.getDraggedObject().draggedPort == (-1,-1):
            dprint(
            "_observer_glyph_left_button_up:: end of glyph move")
            # this is the end of a glyph move: there is still a
            # draggedObject, but the left mouse button is up.
            # the new VTK canvas event system only switches off draggy
            # things AFTER the left mouse button up event
            all_lines = \
                self.canvas.getObjectsOfClass(DeVIDECanvasLine)
            for line in all_lines:
                dprint("+-- routing line", line)
                self._route_line(line)
            # the old code also switch off the draggedPort here...
            self.canvas.redraw()

    def _observer_glyph_left_button_dclick(self, glyph):
        module = glyph.moduleInstance
        # double clicking on a module opens the View/Config.
        self._viewConfModule(module)

    def _cohenSutherLandClip(self,
                             x0, y0, x1, y1,
                             xmin, ymin, xmax, ymax):
        """Perform Cohen Sutherland line clipping given line defined by
        endpoints (x0, y0) and (x1, y1) and window (xmin, ymin, xmax, ymax).

        See for e.g.:
        http://www.cs.fit.edu/~wds/classes/graphics/Clip/clip/clip.html

        @returns: a list of point coordinates where the line is clipped
        by the window.

        @todo: should be moved out into utility module.
        """

        def outCode(x, y, xmin, ymin, xmax, ymax):
            """Determine Cohen-Sutherland bitcode for a point (x,y) with
            respect to a window (xmin, ymin, xmax, ymax).

            point left of window (x < xmin): bit 1
            point right of window (x > xmax): bit 2
            point below window (y < ymin): bit 3
            point above window (y > ymax): bit 4
            
            """


            a,b,c,d = (0,0,0,0)

            if y > ymax:
                a = 1
            if y < ymin:
                b = 1
                
            if x > xmax:
                c = 1
            elif x < xmin:
                d = 1

            return (a << 3) | (b << 2) | (c << 1) | d

        # determine bitcodes / outcodes for line endpoints
        oc0 = outCode(x0, y0, xmin, ymin, xmax, ymax)
        oc1 = outCode(x1, y1, xmin, ymin, xmax, ymax)

        clipped = False # true when the whole line has been clipped
        accepted = False # trivial accept (line is inside)
        
        while not clipped:
            if oc0 == 0 and oc1 == 0:
                # the line is completely inside
                clipped = True
                accepted = True
                
            elif oc0 & oc1 != 0:
                # trivial reject, the line is nowhere near
                clipped = True
                
            else:
                dx = float(x1 - x0)
                dy = float(y1 - y0)
                if dx != 0.0:
                    m = dy / dx
                else:
                    # if dx == 0.0, we won't need m in anycase (m is only
                    # needed to calc intersection with a vertical edge)
                    m = 0.0
                if dy != 0.0:
                    mi = dx / dy
                else:
                    # same logic here
                    mi = 0.0
                    
                # this means there COULD be a clip

                # pick "outside" point
                oc = [oc1, oc0][bool(oc0)]

                if oc & 8: # y is above (numerically)
                    x = x0 + mi * (ymax - y0)
                    y = ymax
                elif oc & 4: # y is below (numerically)
                    x = x0 + mi * (ymin - y0)
                    y = ymin
                elif oc & 2: # x is right
                    x = xmax
                    y = y0 + m * (xmax - x0)
                else:
                    x = xmin
                    y = y0 + m * (xmin - x0)

                if oc == oc0:
                    # we're clipping off the line start
                    x0 = x
                    y0 = y
                    oc0 = outCode(x0, y0, xmin, ymin, xmax, ymax)
                else:
                    # we're clipping off the line end
                    x1 = x
                    y1 = y
                    oc1 = outCode(x1, y1, xmin, ymin, xmax, ymax)

        clipPoints = []
        if accepted:
            if x0 == xmin or x0 == xmax or y0 == ymin or y0 == ymax:
                clipPoints.append((x0, y0))
            if x1 == xmin or x1 == xmax or y1 == ymin or y1 == ymax:
                clipPoints.append((x1, y1))

        return clipPoints
                
    def _route_all_lines(self):
        """Call _route_line on each and every line on the canvas.
        Refresh canvas afterwards.
        """

        # THEN reroute all lines
        allLines = self.canvas.getObjectsOfClass(DeVIDECanvasLine)
                    
        for line in allLines:
            self._route_line(line)
            
        # redraw all
        self.canvas.redraw()

    def _route_all_glyph_lines_fast(self, glyph):
        """Fast route all lines going into and originating from glyph.
        This is used during glyph drags as a kind of preview.  This
        will not request a redraw of the canvas, the calling method
        has to do that.

        @param glyph: glyph whose lines will all be fast routed.
        """

        for l in glyph.inputLines:
            if l is not None:
                self._route_line_fast(l)

        for lines in glyph.outputLines:
            for l in lines:
                if l is not None:
                    self._route_line_fast(l)

    def dummy(self):
        # dummy method: this code can be used at the end of the
        # previous method for debugging stippling problems.
        allLines = self.canvas.getObjectsOfClass(DeVIDECanvasLine)
        for line in allLines:
            should_draw = True
            if line in glyph.inputLines:
                should_draw = False
            else:
                for lines in glyph.outputLines:
                    if line in lines:
                        should_draw = False
                        break
                   
            if should_draw:
                line.set_normal()

        

    def _route_line(self, line):
        """Route line around all glyphs on canvas.

        Line is routed by inserting a number of control points to make
        it go around all glyphs the canvas.  This is not terribly
        efficient: it's routing a line around ALL glyphs, instead of
        making use of some space partitioning scheme.  However, in the
        worst practical case, this comes down to about 40 glyphs
        
        If you have some time on your hands, feel free to improve.

        @param line: DeVIDECanvasLine instance representing the line
        that has to be routed.
        """
        
        # we have to get a list of all coGlyphs
        allGlyphs = self.canvas.getObjectsOfClass(DeVIDECanvasGlyph)

        # make sure the line is back to 4 points
        line.updateEndPoints()

        # this should be 5 for straight line drawing
        # at least 10 for spline drawing; also remember to change
        # the DrawLines -> DrawSplines in coLine as well as
        # coLine.updateEndPoints() (at the moment they use port height
        # to get that bit out of the glyph)
        overshoot = DeVIDECanvasLine.routingOvershoot
        # sometimes, for instance for spline routing, we need something
        # extra... for straight line drawing, this should be = overshoot
        #moreOvershoot = 2 * overshoot
        moreOvershoot = overshoot

        successfulInsert = True
        numInserts = 0
        while successfulInsert and numInserts < 30:
            
            (x0, y0), (x1, y1) = line.getThirdLastSecondLast()

            clips = {}
            for glyph in allGlyphs:
                (xmin, ymin), (xmax, ymax) = glyph.get_bottom_left_top_right()

                clipPoints = self._cohenSutherLandClip(x0, y0, x1, y1,
                                                       xmin, ymin, xmax, ymax)
                if clipPoints:
                    clips[glyph] = clipPoints

            # now look for the clip point closest to the start of the current
            # line segment!
            currentSd = sys.maxint
            nearestGlyph = None
            nearestClipPoint = None
            for clip in clips.items():
                for clipPoint in clip[1]:
                    xdif = clipPoint[0] - x0
                    ydif = clipPoint[1] - y0
                    sd = xdif * xdif + ydif * ydif
                    if sd < currentSd:
                        currentSd = sd
                        nearestGlyph = clip[0]
                        nearestClipPoint = clipPoint

            successfulInsert = False
            # we have the nearest clip point
            if nearestGlyph:
                (xmin, ymin), (xmax, ymax) = \
                       nearestGlyph.get_bottom_left_top_right()

                # does it clip the horizontal bar
                if nearestClipPoint[1] == ymin or nearestClipPoint[1] == ymax:
                    midPointX = xmin + (xmax - xmin) / 2.0
                    if x1 < midPointX:
                        newX = xmin - moreOvershoot
                    else:
                        newX = xmax + moreOvershoot
                    
                    newY = nearestClipPoint[1]
                    if newY == ymin:
                        newY -= overshoot

                    else:
                        newY += overshoot
                        
                    # if there are clips on the new segment, add an extra
                    # node to avoid those clips!
                    for glyph in allGlyphs:
                        (xmin2, ymin2), (xmax2, ymax2) = \
                                glyph.get_bottom_left_top_right()
                        cp2 = self._cohenSutherLandClip(x0,y0,newX,newY,
                                                        xmin2, ymin2,
                                                        xmax2, ymax2)
                        if cp2:
                            break
                     
                    if cp2:
                        line.insertRoutingPoint(nearestClipPoint[0], newY)
                        numInserts += 1
                        
                    successfulInsert = line.insertRoutingPoint(newX, newY)
                    numInserts += 1
                    
                # or does it clip the vertical bar
                elif nearestClipPoint[0] == xmin or \
                         nearestClipPoint[0] == xmax:
                    midPointY = ymin + (ymax - ymin) / 2.0
                    if y1 < midPointY:
                        newY = ymin - moreOvershoot
                    else:
                        newY = ymax + moreOvershoot

                    newX = nearestClipPoint[0]
                    if newX == xmin:
                        newX -= overshoot
                    else:
                        newX += overshoot

                    # if there are clips on the new segment, add an extra
                    # node to avoid those clips!
                    for glyph in allGlyphs:
                        (xmin2, ymin2), (xmax2, ymax2) = \
                                glyph.get_bottom_left_top_right()
                        cp2 = self._cohenSutherLandClip(x0,y0,newX,newY,
                                                        xmin2, ymin2,
                                                        xmax2, ymax2)
                        if cp2:
                            break
                     
                    if cp2:
                        line.insertRoutingPoint(newX, nearestClipPoint[1])
                        numInserts += 1

                    successfulInsert = line.insertRoutingPoint(newX, newY)
                    numInserts += 1

                else:
                    print "HEEEEEEEEEEEEEEEEEEEELP!!  This shouldn't happen."
                    raise Exception

        line.set_normal()
        line.update_geometry()

    def _route_line_fast(self, line):
        """Similar to _route_line, but does not take into account any
        glyphs on the canvas.  Simply route line from starting point
        to ending point.  This is used for real-time updating during
        glyph moves.

        Think about changing this: keep all current routing points,
        only change two points that are attached to the glyph that is
        being dragged.
        """

        # make sure the line is back to 4 points
        line.updateEndPoints()
        # then get it to update (applying the spline to the control
        # points)
        line.set_highlight()
        line.update_geometry()

    def _viewConfModule(self, module):
        mm = self._devide_app.get_module_manager()
        mm.viewModule(module)

    def _deleteModule(self, glyph, refreshCanvas=True):
        success = True
        try:
            # FIRST remove it from any selections; we have to do this
            # while everything is still more or less active
            self._selected_glyphs.removeGlyph(glyph)
            
            # first we disconnect all consumers
            consumerList = []
            for lines in glyph.outputLines:
                for line in lines:
                    consumerList.append((line.toGlyph, line.toInputIdx))

            for consumer in consumerList:
                self._disconnect(consumer[0], consumer[1])

            # then far simpler all suppliers
            for inputIdx in range(len(glyph.inputLines)):
                self._disconnect(glyph, inputIdx)
            
            # then get the module manager to NUKE the module itself
            mm = self._devide_app.get_module_manager()
            # this thing can also remove all links between supplying and
            # consuming objects (we hope) :)
            mm.deleteModule(glyph.moduleInstance)


        except Exception, e:
            success = False
            self._devide_app.log_error_with_exception(
                'Could not delete module (removing from canvas '
                'anyway): %s' % (str(e)))

        canvas = self.canvas
        # remove it from the canvas
        canvas.remove_object(glyph)
        # take care of possible lyings around
        glyph.close()

        # after all that work, we deserve a redraw
        if refreshCanvas:
            canvas.redraw()

        return success

    def set_current_filename(self, filename):
        """Set current filename.

        This will record this in an ivar, and also change the window
        title to reflect the current filename.
        """

        self._current_filename = filename
        if filename is None:
            filename = 'unnamed.dvn'

        # this changes the window title
        self._interface.set_current_filename(filename)

    def show_module_help_from_glyph(self, glyph):
        module_instance = glyph.moduleInstance
        mm = self._devide_app.get_module_manager()

        spec = mm.get_module_spec(module_instance)
        self.show_module_help(spec)

    def show_module_help(self, module_spec):
        """module_spec is e.g. module:full.module.name
        """

        if module_spec is None or not module_spec.startswith('module:'):
            return
        
        module_name = module_spec.split(':')[1]
        mm = self._devide_app.get_module_manager()
        
        try:
            ht = mm._availableModules[module_name].help
        except AttributeError:
            ht = 'No documentation available for this module.'

        mf = self._interface._main_frame
        
        mf.doc_window.SetPage(self._module_doc_to_html(
            module_name, ht))
        
