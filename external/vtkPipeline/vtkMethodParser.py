# $Id: vtkMethodParser.py,v 1.3 2003/02/17 20:07:01 cpbotha Exp $
#
# This python program/module provides functionality to parse the
# methods of a VTK object and the ability to save and reload the
# current state of a VTK object.
#
# This code is distributed under the conditions of the BSD license.
# See LICENSE.txt for details.
#
# Copyright (c) 2000-2002, Prabhu Ramachandran.
#
# This software is distributed WITHOUT ANY WARRANTY; without even the
# implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the above copyright notice for more information.
#
# Author contact information:
#   Prabhu Ramachandran <prabhu_r@users.sf.net>
#   http://www.aero.iitm.ernet.in/~prabhu/

"""  
This python program/module provides functionality to parse the methods
of a VTK object and the ability to save and reload the current state
of a VTK object.

"""

import string, re, sys
import types

# set this to 1 if you want to see debugging messages - very useful if
# you have problems
DEBUG=0

def debug (msg):
    if DEBUG:
	print msg

class VtkDirMethodParser:
    """ Parses the methods from dir(vtk_obj). """
    def initialize_methods (self, vtk_obj):
        debug ("VtkDirMethodParser:: initialize_methods ()")

	self.methods = dir (vtk_obj)[:]
	# stores the <blah>On methods
	self.toggle_meths = []
	# stores the Set<blah>To<blah> methods
	self.state_meths = []
	# stores the methods that have a Get<blah> and Set<blah>
	# only the <blah> is stored
	self.get_set_meths = []
	# pure get methods
	self.get_meths = []
	self.state_patn = re.compile ("To[A-Z0-9]")

        # Removing the Get/SetReferenceCount method
        try:
            self.methods.index ('GetReferenceCount')
        except ValueError:
            pass
        else:
            self.methods.remove ('GetReferenceCount')
            if 'SetReferenceCount' in self.methods:
                self.methods.remove ('SetReferenceCount')
            # The ReferenceCount is merely displayed
            self.get_meths.append ('GetReferenceCount')
        try:
            self.methods.index ('GetGlobalWarningDisplay')
        except ValueError:
            pass
        else:
            for m in ('GetGlobalWarningDisplay', 'SetGlobalWarningDisplay',
                      'GlobalWarningDisplayOff','GlobalWarningDisplayOn'):
                self.methods.remove (m)

        # testing if this version of vtk has David Gobbi's cool
        # stuff.
        try:
            junk = vtk_obj.__class__
        except AttributeError:
            pass
        else:
            # Bug in vtkRenderWindows:(
            if re.match ("vtk\w*RenderWindow", vtk_obj.GetClassName ()):
                for method in self.methods[:]:
                    if string.find (method, "StereoCapableWindow") > -1:
                        self.methods.remove (method)
                    elif string.find (method, "Position") > -1:
                        self.methods.remove (method)
            # Infinite loop bug.in older VTK versions
            if re.match ("vtk\w*Reader", vtk_obj.GetClassName ()):
                for method in self.methods[:]:
                    if re.match ("GetNumberOf\w*InFile", method):
                        self.methods.remove (method)
            # no need to check other bugs.
            return

	done = 0            
	# Bug in vtkRenderWindows:(
        if re.match ("vtk\w*RenderWindow", vtk_obj.GetClassName ()):
	    for method in self.methods[:]:
		if string.find (method, "FileName") > -1:
		    self.methods.remove (method)
		    done = done +1
		elif string.find (method, "StereoCapableWindow") > -1:
		    self.methods.remove (method)
		    done = done +1
		elif string.find (method, "Position") > -1:
		    self.methods.remove (method)
		    done = done + 1
		elif string.find (method, "EventPending") > -1:
		    self.methods.remove (method)
		    done = done + 1		    
		elif done == 7:
		    break

	# Severe bug - causes segfault in older VTK releases
	if re.match ("vtk\w*Reader", vtk_obj.GetClassName ()):
	    #self.methods = []
	    for method in self.methods[:]:
		if string.find (method, "Name") > -1:
		    self.methods.remove (method)
                elif string.find (method, "InputString") > -1:
		    self.methods.remove (method)
                # Infinite loop bug.
                elif re.match ("GetNumberOf\w*InFile", method):
                    self.methods.remove (method)

    def parse_methods (self, vtk_obj):
	self.initialize_methods (vtk_obj)
	
	debug ("VtkDirMethodParser:: parse_methods() : initialized methods")
	
	for method in self.methods[:]:
	    if string.find (method[:3], "Set") >= 0 and \
		 self.state_patn.search (method) is not None :
                try:
                    eval ("vtk_obj.Get%s"%method[3:])
                except AttributeError:
                    self.state_meths.append (method)
                    self.methods.remove (method)
            # finding all the On/Off toggle methods
	    elif string.find (method[-2:], "On") >= 0:
                try:
                    self.methods.index ("%sOff"%method[:-2])
                except ValueError:
                    pass
                else:
                    self.toggle_meths.append (method)
                    self.methods.remove (method)
                    self.methods.remove ("%sOff"%method[:-2])
	    # finding the Get/Set methods.
	    elif string.find (method[:3], "Get") == 0:
		set_m = "Set"+method[3:]
		try: 
		    self.methods.index (set_m) 
		except ValueError:
		    pass
		else:
		    self.get_set_meths.append (method[3:])
		    self.methods.remove (method)
		    self.methods.remove (set_m)

	self.clean_up_methods (vtk_obj)

    def clean_up_methods (self, vtk_obj):
	self.clean_get_set (vtk_obj)
	self.clean_state_methods (vtk_obj)
	self.clean_get_methods (vtk_obj)

    def clean_get_set (self, vtk_obj):
	debug ("VtkDirMethodParser:: clean_get_set()")
	# cleaning up the Get/Set methods by removing the toggle funcs.
	for method in self.toggle_meths:
	    try:
		self.get_set_meths.remove (method[:-2])
	    except ValueError:
		pass

	# cleaning them up by removing any methods that are responsible for
	# other vtkObjects
	for method in self.get_set_meths[:]:
	    try:
		eval ("vtk_obj.Get%s ().GetClassName ()"%method)
	    except (TypeError, AttributeError):
		pass
	    else:
		self.get_set_meths.remove (method)
                continue
	    try:
		val = eval ("vtk_obj.Get%s ()"%method)
	    except (TypeError, AttributeError):
		self.get_set_meths.remove (method)
	    else:
		if val is None:
		    self.get_set_meths.remove (method)
	
    def clean_state_methods (self, vtk_obj):
	debug ("VtkDirMethodParser:: clean_state_methods()")
	# Getting the remaining pure GetMethods 
	for method in self.methods[:]:
	    if string.find (method[:3], "Get") == 0:
		self.get_meths.append (method)
		self.methods.remove (method)

	# Grouping similar state methods
	if len (self.state_meths) != 0:
	    tmp = self.state_meths[:]
	    self.state_meths = []
	    state_group = [tmp[0]]
	    end = self.state_patn.search (tmp[0]).start ()
	    # stores the method type common to all similar methods
	    m = tmp[0][3:end] 
	    for i in range (1, len (tmp)):
		if string.find (tmp[i], m) >= 0:
		    state_group.append (tmp[i])
		else:
		    self.state_meths.append (state_group)
		    state_group = [tmp[i]]	
		    end = self.state_patn.search (tmp[i]).start ()
		    m = tmp[i][3:end]
		try: # remove the corresponding set method in get_set
		    val = self.get_set_meths.index (m)
		except ValueError: 
		    pass
		else:
		    del self.get_set_meths[val]
		    #self.get_meths.append ("Get"+m)
                clamp_m = "Get" + m + "MinValue"
                try: # remove the GetNameMax/MinValue in get_meths
                    val = self.get_meths.index (clamp_m)
                except ValueError:
                    pass
                else:
                    del self.get_meths[val]
                    val = self.get_meths.index ("Get" + m + "MaxValue")
                    del self.get_meths[val]

	    if len (state_group) > 0:
		self.state_meths.append (state_group)

    def clean_get_methods (self, vtk_obj):
	debug ("VtkDirMethodParser:: clean_get_methods()")
	for method in self.get_meths[:]:
            #print method
            try:
		res = eval ("vtk_obj.%s ()"%method)
	    except (TypeError, AttributeError):
		self.get_meths.remove (method)
                continue
	    else:
		try:
		    eval ("vtk_obj.%s ().GetClassName ()"%method)
		except AttributeError:
		    pass
		else:
		    self.get_meths.remove (method)
                    continue
            if string.find (method[-8:], "MaxValue") > -1:
                self.get_meths.remove( method)
            elif string.find (method[-8:], "MinValue") > -1:
                self.get_meths.remove( method)
                
	self.get_meths.sort ()

    def toggle_methods (self):
	return self.toggle_meths

    def state_methods (self):
	return self.state_meths

    def get_set_methods (self):
	return self.get_set_meths

    def get_methods (self):
	return self.get_meths


class VtkMethodParser:

    """ This class finds the methods for a given vtkObject.  It uses
    the output from vtkObject->Print() (or in Python str(vtkObject))
    and output from the VtkDirMethodParser to obtain the methods. """
    
    def parse_methods (self, vtk_obj):
	"Parse for the methods."
	debug ("VtkMethodParser:: parse_methods()")
        self.vtk_warn = -1
        try:
            self.vtk_warn = vtk_obj.GetGlobalWarningDisplay ()
        except AttributeError:
            pass
        else:
            vtk_obj.GlobalWarningDisplayOff ()

        if self._initialize_methods (vtk_obj):
            # if David Gobbi's improvements are in this version of VTK
            # then I need to go no further.
            self._reset_warning_status (vtk_obj)
            return

	for method in self.methods[:]:
	    # removing methods that have nothing to the right of the ':'
	    if (method[1] == '') or \
	       (string.find (method[1], "none") > -1) :
		self.methods.remove (method)
	    elif method[0] == "ReferenceCount":
		self.get_meths.append ("Get"+method[0])
		self.methods.remove (method)	

	for method in self.methods:
	    # toggle methods are first identified
	    if (method[1] == "On") or (method[1] == "Off"):
		# bug in vtkRenderWindow.cxx ver 1.104. so fixing it.
		if re.match ("vtk\w*RenderWindow", vtk_obj.GetClassName ()):
		    if method[0] == "Swapbuffers":
			method[0] = "SwapBuffers"
		# more bugs
		if re.match ("vtk\w*Renderer", vtk_obj.GetClassName ()):
		    if method[0] == "Two-sidedLighting":
			method[0] = "TwoSidedLighting"
		try:
		    val = eval ("vtk_obj.Get%s ()"%method[0])
		    if val == 1:
			eval ("vtk_obj.%sOn ()"%method[0])
		    elif val == 0:
			eval ("vtk_obj.%sOff ()"%method[0])
		except AttributeError:
		    pass
		else:
		    self.toggle_meths.append (method[0]+"On")		
	    else: # see it it is get_set or get or a state method
		found = 0
		# checking if it is a state func.
		# figure out the long names from the dir_state_meths
		for sms in self.dir_state_meths[:]:
		    if string.find (sms[0], method[0]) >= 0:
			self.state_meths.append (sms)
			self.dir_state_meths.remove (sms)
			found = 1
		if found:
		    self.get_meths.append ("Get"+method[0])
		    try:
			t = eval ("vtk_obj.Get%sAsString ()"%method[0])
		    except AttributeError:
			pass
		    else:
			self.get_meths.append ("Get"+method[0]+"AsString")
		else: 
		    # the long name is inherited or it is not a state method
		    try:
			t = eval ("vtk_obj.Get%s ().GetClassName ()"%
				  method[0])
		    except AttributeError:
			pass
		    else:
			continue	
		    val = 0
		    try:
			val = eval ("vtk_obj.Get%s ()"%method[0])
		    except (TypeError, AttributeError):
			pass
		    else:
                        try:
                            f = eval ("vtk_obj.Set%s"%method[0])
                        except AttributeError:
                            self.get_meths.append ("Get"+method[0])
                        else:
                            try:
                                apply (f, val)
                            except TypeError:
                                try:
                                    apply (f, (val, ))
                                except TypeError:
                                    self.get_meths.append ("Get"+method[0])
                                else:
                                    self.get_set_meths.append (method[0])
                            else:
                                self.get_set_meths.append (method[0])
                        
        self._clean_up_methods (vtk_obj)

    def _get_str_obj (self, vtk_obj):
	debug ("VtkMethodParser:: _get_str_obj()")
	self.methods = str (vtk_obj)
	self.methods = string.split (self.methods, "\n")
	del self.methods[0]

    def _initialize_methods (self, vtk_obj):
	"Do the basic parsing and setting up"
	debug ("VtkMethodParser:: _initialize_methods()")
	dir_p = VtkDirMethodParser ()
	dir_p.parse_methods (vtk_obj)

        # testing if this version of vtk has David Gobbi's cool
        # stuff. If it does then no need to do other things.
        try:
            junk = vtk_obj.__class__
        except AttributeError:
            pass
        else:
            self.toggle_meths = dir_p.toggle_methods ()
            self.state_meths = dir_p.state_methods ()
            self.get_set_meths = dir_p.get_set_methods ()
            self.get_meths = dir_p.get_methods ()
            return 1

	self.dir_toggle_meths = dir_p.toggle_methods ()
	self.dir_state_meths = dir_p.state_methods ()
	self.dir_get_set_meths = dir_p.get_set_methods ()
	self.dir_get_meths = dir_p.get_methods ()

	self._get_str_obj (vtk_obj)
	patn = re.compile ("  \S")
    
	for method in self.methods[:]:
	    if not patn.match (method):
		self.methods.remove (method)
    
	for method in self.methods[:]:
	    if string.find (method, ":") == -1:
		self.methods.remove (method)

	for i in range (0, len (self.methods)):
	    strng = self.methods[i]
	    strng = string.replace (strng, " ", "")
	    self.methods[i] = string.split (strng, ":")

	done = 0
	if re.match ("vtk\w*RenderWindow", vtk_obj.GetClassName ()):
	    for method in self.methods[:]:
		if string.find (method[0], "Position") > -1:
		    self.methods.remove (method)
		    done = done +1
		elif done == 2:
		    break

	self.toggle_meths = []
	self.state_meths = []
	self.get_set_meths = []
	self.get_meths = []    

        return 0

    def _clean_up_methods (self, vtk_obj):
	"Merge dir and str methods.  Finish up."
	debug ("VtkMethodParser:: _clean_up_methods()")
	for meth_list in ((self.dir_toggle_meths, self.toggle_meths),\
			  (self.dir_get_set_meths, self.get_set_meths),\
			  (self.dir_get_meths, self.get_meths)):
	    for method in meth_list[0]:
		try:
		    meth_list[1].index (method)
		except ValueError:
		    meth_list[1].append (method)	    

	# Remove all get_set methods that are already in toggle_meths
	# This case can happen if the str produces no "On/Off" but
	# dir does and str produces a get_set instead.
	for method in self.toggle_meths:
	    try:
		self.get_set_meths.remove (method[:-2])
	    except ValueError:
		pass

	self.toggle_meths.sort ()
	self.state_meths.sort ()
	self.get_set_meths.sort ()
	self.get_meths.sort ()
        self._reset_warning_status (vtk_obj)

    def _reset_warning_status (self, vtk_obj):
	debug ("VtkMethodParser:: _reset_warning_status ()")
        if self.vtk_warn > -1:
            vtk_obj.SetGlobalWarningDisplay (self.vtk_warn)
    
    def toggle_methods (self):
	return self.toggle_meths

    def state_methods (self):
	return self.state_meths

    def get_set_methods (self):
	return self.get_set_meths

    def get_methods (self):
	return self.get_meths


class VtkPicklerException (Exception):
    pass


class VtkPickler:

    """ Enables saving/loading the configuration of VTK objects by
    printing out the methods and the corresponding arguments to a
    file.  While dumping it uses the VtkMethodParser to get the
    methods."""

    def parse_methods (self, vtk_obj):
	debug ("VtkPickler:: parse_methods()")
	parser = VtkMethodParser ()
	parser.parse_methods (vtk_obj)
	self.toggle_meths = parser.toggle_methods ()
	self.state_meths = parser.state_methods ()
	self.get_set_meths = parser.get_set_methods ()

    def dump (self, vtk_obj, file):
	"Dump the configuration for the vtk object into the file passed."
	debug ("VtkPickler:: dump()")
	self.obj = vtk_obj
	self.out = file
	self.parse_methods (vtk_obj)
        self.vtk_warn = -1
        try:
            self.vtk_warn = vtk_obj.GetGlobalWarningDisplay ()
        except AttributeError:
            pass
        else:
            vtk_obj.GlobalWarningDisplayOff ()
        try:
            self.write_config ()
        finally:
            # reset warning status
            if self.vtk_warn > -1:
                vtk_obj.SetGlobalWarningDisplay (self.vtk_warn)

    def load (self, vtk_obj, file, equiv=""):
        
	"""Load the configuration for the vtk object from the file
	passed.  Input args: vtk_obj - the VTK object, file - the fiel
	from which to load the configuration, equiv - a hack to allow
	name changes (arghh) made in VTK."""
        
	debug ("VtkPickler:: load()")
	self.obj = vtk_obj
	self.input = file
        self.vtk_warn = -1
        try:
            self.vtk_warn = vtk_obj.GetGlobalWarningDisplay ()
        except AttributeError:
            pass
        else:
            vtk_obj.GlobalWarningDisplayOff ()
        try:
            self.load_config (equiv)
        finally:
            # reset warning status 
            if self.vtk_warn > -1:
                vtk_obj.SetGlobalWarningDisplay (self.vtk_warn)

    def write_config(self):
	debug ("VtkPickler:: write_config()")
	state_patn = re.compile ("To[A-Z0-9]")
	methods = []
	args = []
	for method in self.toggle_meths:
            func = "Set"+method[:-2]
            val = eval ("self.obj.Get%s ()"%func[3:])
	    methods.append ((func, val))
	for method in self.state_meths:
	    end = state_patn.search (method[0]).start ()
	    func = method[0][:end]
	    val = eval ("self.obj.Get%s ()"%func[3:])
	    methods.append ((func, val))
	for method in self.get_set_meths:
            func = "Set"+method
	    val = eval ("self.obj.Get%s ()"%method)
	    methods.append ((func, val))

	self.out.write (self.obj.GetClassName ()+"\n")
	self.out.write (str (methods))
	self.out.write ("\n")

    def write_old_config (self):
	debug ("VtkPickler:: write_old_config()")
	state_patn = re.compile ("To[A-Z0-9]")
	methods = []
	args = []
	for method in self.toggle_meths:    
	    methods.append ("Set"+method[:-2])
	    val = eval ("self.obj.Get%s ()"%method[:-2])
	    args.append (val)
	for method in self.state_meths:
	    end = state_patn.search (method[0]).start ()
	    m = method[0][:end]
	    methods.append (m)
	    val = eval ("self.obj.Get%s ()"%m[3:])
	    args.append (val)
	for method in self.get_set_meths:
	    methods.append ("Set"+method)
	    val = eval ("self.obj.Get%s ()"%method)
	    args.append (val)

	self.out.write (self.obj.GetClassName ()+"\n")
	self.out.write (str (methods))
	self.out.write ("\n")
	self.out.write (str (args))
	self.out.write ("\n")

    def load_config (self, equiv):        
        """Loads the configuration.  Input args: equiv - is an
        equivalent name for the object's class.  Useful to get around
        names being renamed by VTK folks. """        
	debug ("VtkPickler:: load_config ()")
	vtk_obj = self.obj
        c_name = self.input.readline ()[:-1]

        obj_name = vtk_obj.GetClassName ()
        if (obj_name != c_name) and (c_name != equiv):
	    msg = "Error: Object given doesn't match object saved in file."
            msg = msg + "\nObject given is %s."%vtk_obj.GetClassName () 
            msg = msg + "\nObject saved in file is %s."%c_name
	    msg = msg + "\nNot loading saved configuration!"
	    raise VtkPicklerException, msg

	methods = eval (self.input.readline ())
        t = type (methods[0]) 
        if t is types.TupleType or t is types.ListType:
            self.load_new_config (methods)
        else:
            self.load_old_config (methods)

    def load_new_config(self, methods):
	debug ("VtkPickler:: load_new_config ()")
	for method in methods:
            func = method[0]
	    arg = method[1]
            if func != 'SetGlobalWarningDisplay':
                self._call_function (func, arg)

    def load_old_config (self, methods):
	debug ("VtkPickler:: load_old_config ()")
	args = eval (self.input.readline ())
	for i in range (0, len (methods)):
            func = methods[i]
            arg = args[i]
            if func != 'SetGlobalWarningDisplay':
                self._call_function (func, arg)

    def _call_function(self, func, arg):
	debug ("VtkPickler:: _call_function ()")
        try:
            f = eval ("self.obj.%s"%func)
        except AttributeError:
            msg = "Warning: The installed version of VTK does "\
                  "not have the member " + func + \
                  "for the class " + self.obj.GetClassName () + \
                  ".\nIgnoring it.\n"
            debug (msg)
        else:
            try:
                apply (f, arg)
            except TypeError:
                apply (f, (arg, ))
        
