# snippet to be ran in the introspection window of a slice3dVWR to 
# export the whole scene as a RIB file.  Before you can do this, 
# both BACKGROUND_RENDERER and GRADIENT_BACKGROUND in slice3dVWR.py
# should be set to False.

obj._orientation_widget.Off()
rw = obj._threedRenderer.GetRenderWindow()
re = vtk.vtkRIBExporter()
re.SetRenderWindow(rw)
re.SetFilePrefix('/tmp/slice3dVWR')
re.Write()
