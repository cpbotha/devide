# $Id: moduleUtilsITK.py,v 1.3 2004/03/25 12:32:10 cpbotha Exp $

import fixitk as itk



def setupITKObjectProgress(dvModule, obj, nameOfObject, progressText):

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

    mm = dvModule._moduleManager

    def commandCallable():
        mm.genericProgressCallback(
            nameOfObject, getattr(dvModule, objAttrString).GetProgress(),
            progressText)

    pc = itk.itkPyCommand_New()
    pc.SetCommandCallable(commandCallable)
    obj.AddObserver(itk.itkProgressEvent(), pc.GetPointer())
    
    # we DON'T have to store a binding to the PyCommand; during AddObserver,
    # the ITK object makes its own copy.  The ITK object will also take care
    # of destroying the observer when it (the ITK object) is destroyed
    #obj.progressPyCommand = pc

