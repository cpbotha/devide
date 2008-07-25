# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

from module_base import ModuleBase
from moduleMixins import ScriptedConfigModuleMixin
import module_utils
import vtk

class RegionGrowing(ScriptedConfigModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        ModuleBase.__init__(self, module_manager)

        self._image_threshold = vtk.vtkImageThreshold()
        # seedconnect wants unsigned char at input
        self._image_threshold.SetOutputScalarTypeToUnsignedChar()
        self._image_threshold.SetInValue(1)
        self._image_threshold.SetOutValue(0)
        
        self._seed_connect = vtk.vtkImageSeedConnectivity()
        self._seed_connect.SetInputConnectValue(1)
        self._seed_connect.SetOutputConnectedValue(1)
        self._seed_connect.SetOutputUnconnectedValue(0)

        self._seed_connect.SetInput(self._image_threshold.GetOutput())

        module_utils.setupVTKObjectProgress(self, self._seed_connect,
                                           'Performing region growing')
        
        module_utils.setupVTKObjectProgress(self, self._image_threshold,
                                           'Thresholding data')

        # we'll use this to keep a binding (reference) to the passed object
        self._input_points = None
        # this will be our internal list of points
        self._seed_points = []

        self._config._thresh_interval = 5

        config_list = [
            ('Auto threshold interval:', '_thresh_interval', 'base:float',
             'text',
             'Used to calculate automatic threshold.')]
             
        ScriptedConfigModuleMixin.__init__(
            self, config_list,
            {'Module (self)' : self,
             'vtkImageSeedConnectivity' : self._seed_connect,
             'vtkImageThreshold' : self._image_threshold})

        self.sync_module_logic_with_config()

    def close(self):
        ScriptedConfigModuleMixin.close(self)

        # get rid of our reference
        del self._image_threshold
        self._seed_connect.SetInput(None)
        del self._seed_connect

        ModuleBase.close(self)

    def get_input_descriptions(self):
        return ('vtkImageData', 'Seed points')
    
    def set_input(self, idx, input_stream):
        if idx == 0:
            # will work for None and not-None
            self._image_threshold.SetInput(input_stream)
        else:
            if input_stream != self._input_points:
                self._input_points = input_stream
    
    def get_output_descriptions(self):
        return ('Region growing result (vtkImageData)',)
    
    def get_output(self, idx):
        return self._seed_connect.GetOutput()

    def logic_to_config(self):
        pass
    
    def config_to_logic(self):
        pass

    def execute_module(self):
        self._sync_to_input_points()
        
        # calculate automatic thresholds (we can only do this if we have
        # seed points and input data)
        ii = self._image_threshold.GetInput()
        if ii and self._seed_points:
            ii.Update()
            mins, maxs = ii.GetScalarRange()
            ranges = maxs - mins

            sums = 0.0
            for seed_point in self._seed_points:
                # we assume 0'th component!
                print seed_point
                v = ii.GetScalarComponentAsDouble(
                    seed_point[0], seed_point[1], seed_point[2], 0)
                print "BLAAT ", v
                sums = sums + v

            means = sums / float(len(self._seed_points))

            
            lower_thresh = means - \
                           float(self._config._thresh_interval / 100.0) * \
                           float(ranges)
            upper_thresh = means + \
                           float(self._config._thresh_interval / 100.0) * \
                           float(ranges)

            print "Auto thresh: ", lower_thresh, " - ", upper_thresh

            self._image_threshold.ThresholdBetween(lower_thresh, upper_thresh)


        self._seed_connect.Update()
        

    def _sync_to_input_points(self):
        # extract a list from the input points
        temp_list = []
        if self._input_points:
            for i in self._input_points:
                temp_list.append(i['discrete'])

        if temp_list != self._seed_points:
            self._seed_points = temp_list
            self._seed_connect.RemoveAllSeeds()
            # we need to call Modified() explicitly as RemoveAllSeeds()
            # doesn't.  AddSeed() does, but sometimes the list is empty at
            # this stage and AddSeed() isn't called.
            self._seed_connect.Modified()
            
            for seedPoint in self._seed_points:
                self._seed_connect.AddSeed(seedPoint[0], seedPoint[1],
                                           seedPoint[2])
        
        
        
        
        
