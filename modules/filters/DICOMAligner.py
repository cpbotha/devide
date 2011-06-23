# DicomAligner.py by Francois Malan - 2011-06-23

from module_base import ModuleBase
from module_mixins import NoConfigModuleMixin
import wx
import os
import vtk
import itk
import math

class DICOMAligner(
    NoConfigModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)

        NoConfigModuleMixin.__init__(
            self, {'Module (self)' : self})

        self.sync_module_logic_with_config()    
        self._ir = vtk.vtkImageReslice()        
           
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for input_idx in range(len(self.get_input_descriptions())):
            self.set_input(input_idx, None)

        # this will take care of GUI
        NoConfigModuleMixin.close(self)

    def set_input(self, idx, input_stream):
        if idx == 0:
            self._imagedata = input_stream
        else:
            self._metadata = input_stream
    
        self._input = input_stream

    def get_input_descriptions(self):
        return ('vtkImageData (from DICOMReader port 0)', 'Medical metadata (from DICOMReader port 1)')

    def get_output_descriptions(self):
        return ('vtkImageData', )

    def get_output(self, idx):
        return self._output

    def _convert_input(self):
        '''
        Performs the required transformation to match the image to the world coordinate system defined by medmeta
        '''


        # the first two columns of the direction cosines matrix represent
        # the x,y axes of the DICOM images in RAH space
        # if we want to resample the images so that x,y are always RA
        # the inverse should do the trick
        dcmatrix = vtk.vtkMatrix4x4()
        dcmatrix.DeepCopy(self._metadata.direction_cosines)
        dcmatrix.Invert()

        origin = self._imagedata.GetOrigin()
        spacing = self._imagedata.GetSpacing()
        extent = self._imagedata.GetExtent()

        # convert our new cosines to something we can give the ImageReslice
        dcm = [[0,0,0] for _ in range(3)]
        for col in range(3):
            for row in range(3):
                dcm[col][row] = dcmatrix.GetElement(row, col)

        # do it.        
        self._ir.SetResliceAxesDirectionCosines(dcm[0], dcm[1], dcm[2])
        self._ir.SetInput(self._imagedata)
        self._ir.Update()
        output = self._ir.GetOutput()

        #We now have to check whether the origin needs to be moved from its prior position
        #Yes folks - the reslice operation screws up the origin and we must fix it. 
        #
        #The origin's coordinates (as provided by the DICOMreader) are in WORLD 
        # coordinates. 
        #We are transforming the voxels (i.e. image coordiante axes) 
        # FROM IMAGE TO WORLD coordinates. We must not transform the origin in this 
        # sense- only the image axes (and therefore voxels). However, vtkImageReslice 
        # (for some strange reason) transforms the origin according to the 
        # transformation matrix (?). So we need to reset this.
        #But, there is a caveat.
        #In the WORLD coordinate system, a voxel's world coordinates 
        # = origin + image_coordinates * spacing.
        # Since both image coordinates and spacing are positive, the origin must be at
        # the "most negative" corner (in world coordinate terms). 
        # But the original origin is defined at the "most negative" corner in IMAGE 
        # coordinates(!). This means that the origin should, in most cases, be 
        # translated from its original position, depending on the relative world and 
        # image axes' orientations.
        #The new origin becomes the WORLD coordinates of the IMAGE corner
        # corresponding to the most negative WORLD coordinates. 
        #To determine this we look along each of the IMAGE axes and see whether it
        # has a negative component along ANY of the WORLD axes. If so, we move it to
        # its most positive image coordinate along this IMAGE axis (most negative WORLD 
        # coordinate along the corresponding world axis that had negative component).

        #Remember that (in matlab syntax)
        #  p_world = dcm_matrix * diag(spacing)*p_image + origin
        #for example: for a 90 degree rotation around the x axis this is
        # [p_x]   [ 1  0  0][nx*dx]   [ox]
        # [p_y] = [ 0  0  1][ny*dy] + [oy]
        # [p_z]   [ 0 -1  0][nz*dz]   [oz]
        #, where p is the world coordinates, d is the spacing, n is the image 
        #  coordinates and o is the origin.

        newOriginX = origin[0];
        newOriginY = origin[1];
        newOriginZ = origin[2];

        #Look along the first image axis
        if (dcm[0][0] < 0) | (dcm[1][0] < 0) | (dcm[2][0] < 0):
            #Transform image coordinate [extent_x, 0, 0] to world coordinates
            newOriginX = dcm[0][0]*extent[1]*spacing[0] + newOriginX
            newOriginY = dcm[1][0]*extent[1]*spacing[0] + newOriginY
            newOriginZ = dcm[2][0]*extent[1]*spacing[0] + newOriginZ  
        #Look along the second image axis
        if (dcm[0][1] < 0) | (dcm[1][1] < 0) | (dcm[2][1] < 0):
            #Transform image coordinate [0, extent_y, 0] to world coordinates
            newOriginX = dcm[0][1]*extent[3]*spacing[1] + newOriginX
            newOriginY = dcm[1][1]*extent[3]*spacing[1] + newOriginY
            newOriginZ = dcm[2][1]*extent[3]*spacing[1] + newOriginZ
        #Look along the third image axis
        if (dcm[0][2] < 0) | (dcm[1][2] < 0) | (dcm[2][2] < 0):
            #Transform image coordinate [0, extent_y, 0] to world coordinates
            newOriginX = dcm[0][2]*extent[5]*spacing[2] + newOriginX
            newOriginY = dcm[1][2]*extent[5]*spacing[2] + newOriginY
            newOriginZ = dcm[2][2]*extent[5]*spacing[2] + newOriginZ

        output.SetOrigin(newOriginX, newOriginY, newOriginZ)
        self._output = output

    def execute_module(self):
        self._convert_input()