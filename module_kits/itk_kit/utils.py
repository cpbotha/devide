# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.

import itk
import re

from module_kits.misc_kit.misc_utils import get_itk_img_type_and_dim
get_img_type_and_dim = get_itk_img_type_and_dim
                

def get_img_type_and_dim_shortstring(itk_img):

    tdv = get_img_type_and_dim(itk_img)
    
    # this turns 'unsigned_char' into 'UC' and 'float' into 'F'
    itkTypeC = ''.join([i.upper()[0] for i in tdv[0].split('_')])

    # the 'this' signature contains 'short_int', but the ITK shortstring for
    # this is SS
    if itkTypeC == 'SI':
        itkTypeC = 'SS'

    if len(tdv[2]) > 0:
        # this will be for instance VF33 or VF22
        shortstring = '%s%s%s%s' % (tdv[2], itkTypeC, tdv[1], tdv[1])

    else:
        # and this F3 or UC2
        shortstring = '%s%s' % (itkTypeC, tdv[1])

    return shortstring

def setupITKObjectProgress(dvModule, obj, nameOfObject, progressText,
                           objEvals=None):

    # objEvals is on optional TUPLE of obj attributes that will be called
    # at each progress callback and filled into progressText via the Python
    # % operator.  In other words, all string attributes in objEvals will be
    # eval'ed on the object instance and these values will be filled into
    # progressText, which has to contain the necessary number of format tokens

    # first we have to find the attribute of dvModule that binds
    # to obj.  We _don't_ want to have a binding to obj hanging around
    # in our callable, because this means that the ITK object can never
    # be destroyed.  Instead we look up the binding everytime the callable
    # is invoked by making use of getattr on the devideModule binding.

    # find attribute string of obj in dvModule
    di = dvModule.__dict__.items()
    objAttrString = None
    for key, value in di:
        if value == obj:
            objAttrString = key
            break

    if not objAttrString:
        raise Exception, 'Could not determine attribute string for ' \
              'object %s.' % (obj.__class__.__name__)

    mm = dvModule._module_manager

    # sanity check objEvals
    if type(objEvals) != type(()) and objEvals != None:
        raise TypeError, 'objEvals should be a tuple or None.'

    def commandCallable():
        # setup for and get values of all requested objEvals
        values = []

        if type(objEvals) == type(()):
            for objEval in objEvals:
                values.append(
                    eval('dvModule.%s.%s' % (objAttrString, objEval)))

        values = tuple(values)
        print values

        # do the actual callback
        mm.generic_progress_callback(getattr(dvModule, objAttrString),
            nameOfObject, getattr(dvModule, objAttrString).GetProgress(),
            progressText % values)

        # get rid of all bindings
        del values

    pc = itk.PyCommand.New()
    pc.SetCommandCallable(commandCallable)
    res = obj.AddObserver(itk.ProgressEvent(), pc.GetPointer())

    # we DON'T have to store a binding to the PyCommand; during AddObserver,
    # the ITK object makes its own copy.  The ITK object will also take care
    # of destroying the observer when it (the ITK object) is destroyed
    #obj.progressPyCommand = pc
