#!/usr/bin/env python
#
# $Id$
#
# This file helps test the vtkMethodParser by testing if it is able to
# parse all the objects that vtkpython provides.
#
# Copyright (C) 2001 Prabhu Ramachandran
#
# Distributed under the conditions of the GNU LGPL.
#
# Author contact information:
#   Prabhu Ramachandran <prabhu_r@users.sf.net>
#   http://www.aero.iitm.ernet.in/~prabhu/
#

""" Usage: python test_parser.py

You will receive a whole bunch of error and warning messages from VTK
simply because the parser will also parse the obsolete methods and
that there is no pipeline with which I am testing the objects.  Other
important messages will be surrounded by a line full of *'s.  These
are the messages you should pay attention to.  For instance

$ python test_trace.py

**************************************************
Not testing the following objects since they cause segfaults.
['vtkLODProp3D', 'vtkPropAssembly', 'vtkRayCaster', 'vtkViewRays']
**************************************************
Testing vtk3DSImporter
ok
Testing vtkActor
ok
....

Testing vtkArrayCalculator
ERROR: In vtkDataSetToDataSetFilter.cxx, line 91
vtkArrayCalculator (0x818ced0): Abstract filters require input to be set before 
output can be retrieved
...
Testing vtkCreateKitModuleName
**************************************************
Not testing vtkpython.vtkCreateKitModuleName().  Not a vtk object.
**************************************************
...

I usually prefer redirecting the messages to a file like so:

$ python test_parser.py &> /tmp/err.log

"""

import vtkMethodParser
import vtkpython
import sys, traceback

def exception ():
    
    """ This function handles any exception derived from Exception and
    prints it out in a message box.  Code merrily stolen from the
    Thinking in Python site."""
    
    try:
        type, value, tb = sys.exc_info ()
        info = traceback.extract_tb (tb)
        filename, lineno, function, text = info[-1] # last line only
        print "Exception: %s:%d: %s: %s (in %s)" %\
              (filename, lineno, type.__name__, str (value), function)
    finally:
        type = value = tb = None # clean up


def print_err (msg):
    print "**************************************************"
    print msg
    print "**************************************************"
    

def test_obj (obj_name):

    """ Given a VTK object name this function tests if the object can
    be parsed using the vtkMethodParser.VtkMethodParser.  Useful when
    figuring out which object failed.  This function turns the
    vtkMethodParser.DEBUG flag on so its easier to see where the error
    occured."""
    
    vtkMethodParser.DEBUG = 1
    p = vtkMethodParser.VtkMethodParser ()
    obj = eval ('vtkpython.%s()'%obj_name)
    p.parse_methods (obj)


def remove_segfaulters (obj_names):    
    """ Removes any VTK objects that segfault when parsed without a
    pipeline or an X window."""
    
    segfaulting_objs = ['vtkLODProp3D', 'vtkPropAssembly', 'vtkRayCaster',
                        'vtkViewRays', ]
    for i in segfaulting_objs:
        obj_names.remove(i)

    print_err ("Not testing the following objects since they cause "\
               "segfaults.\n%s"%segfaulting_objs)

    
def check_if_testable (obj):

    """ Checks if the object is testable.  For instance any vtkObject
    that is a vtkImageWindow or vtkRenderWindow cannot be tested
    without a proper window."""
    
    untestable_classes = ['vtkImageWindow',
                          'vtkRenderWindow']
    for i in untestable_classes:
        if obj.IsA (i):
            print_err ("%s IsA %s and is untestable. "%
                       (obj.GetClassName(), i))
            return 0

    # object is testable.
    return 1    


def redirect_vtk_messages ():    
    """ Can be used to redirect VTK related error messages to a
    file."""    
    import tempfile
    tempfile.template = 'vtk-err'
    f = tempfile.mktemp ('.log')
    log = vtkpython.vtkFileOutputWindow ()
    log.SetFlush(1)
    log.SetFileName (f)
    log.SetInstance (log)    
    

def test_all_vtk(debug=0):
    
    """This function tests all available vtk objects and checks if
    their methods can be parsed properly.  Call this function with an
    argument of 1 if you want extensive debugging messages from the
    parser.  The default is set to 0 which is recommended."""
    
    vtkMethodParser.DEBUG = debug
    p = vtkMethodParser.VtkMethodParser ()

    #redirect_vtk_messages ()    
    obj_names = dir (vtkpython)
    remove_segfaulters (obj_names)

    count = 0
    bad_objects = []

    for obj_name in obj_names:
        if obj_name[:3] == 'vtk':
            print "Testing %s"%obj_name            
            try:
                obj = eval ("vtkpython.%s()"%obj_name)
            except TypeError:
                print_err ("Not testing vtkpython.%s().  Not a vtk object."%
                           obj_name)
            else:
                try:
                    obj.IsA('vtkObject')
                except AttributeError:
                    print_err ("%s is not a vtkObject."%obj_name)
                else:
                    if check_if_testable (obj):
                        try:
                            p.parse_methods (obj)
                            print "ok"
                        except Exception, msg:
                            exception ()
                            bad_objects.append (obj_name)
                        else:
                            count = count + 1
                    
    print "Parsed all VTK Python classes.  "\
          "A total of %d classes were parseable."% count
    
    if bad_objects:
        print_err ("The following classes couldnt be parsed - please "\
                   "investigate.\n%s"%bad_objects)


if __name__ == "__main__":
    test_all_vtk()
