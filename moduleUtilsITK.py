# $Id: moduleUtilsITK.py,v 1.1 2004/02/29 02:29:31 cpbotha Exp $

import fixitk as itk



def setupITKObjectProgress(dvModule, obj, nameOfObject, progressText):

    mm = dvModule._moduleManager

    def commandCallable():
        mm.genericProgressCallback(
            nameOfObject, obj.GetProgress(), progressText)

    # we have to store this extra reference: I have to fix itkPyCommand
    # to do a PyINCREF when obj is assigned!
    # I also have to check for a non-NULL object in PyExecute.
    obj.commandCallable = commandCallable
    pc = itk.itkPyCommand_New()
    pc.SetCommandCallable(commandCallable)
    obj.AddObserver(itk.itkProgressEvent(), pc.GetPointer())
    
    # we DON'T have to store a binding to the PyCommand; during AddObserver,
    # the ITK object makes its own copy.  The ITK object will also take care
    # of destroying the observer when it (the ITK object) is destroyed
    #obj.progressPyCommand = pc

