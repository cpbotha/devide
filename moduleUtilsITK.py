# $Id: moduleUtilsITK.py,v 1.2 2004/02/29 17:51:36 cpbotha Exp $

import fixitk as itk



def setupITKObjectProgress(dvModule, obj, nameOfObject, progressText):

    mm = dvModule._moduleManager

    def commandCallable():
        mm.genericProgressCallback(
            nameOfObject, obj.GetProgress(), progressText)

    pc = itk.itkPyCommand_New()
    pc.SetCommandCallable(commandCallable)
    obj.AddObserver(itk.itkProgressEvent(), pc.GetPointer())
    
    # we DON'T have to store a binding to the PyCommand; during AddObserver,
    # the ITK object makes its own copy.  The ITK object will also take care
    # of destroying the observer when it (the ITK object) is destroyed
    #obj.progressPyCommand = pc

