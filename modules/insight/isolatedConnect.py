# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

from moduleBase import moduleBase
from moduleMixins import scriptedConfigModuleMixin
import itk
import module_kits.itk_kit as itk_kit

class isolatedConnect(scriptedConfigModuleMixin, moduleBase):

    def __init__(self, moduleManager):
        # call parent constructor
        moduleBase.__init__(self, moduleManager)

        self._config.replace_value = 1.0
        self._config.upper_threshold = False
        

        config_list = [
            ('Replace value:', 'replace_value', 'base:float', 'text',
             'Voxels touching the first set of seeds will be set to this '
             'value.'),
            ('Upper threshold:', 'upper_threshold', 'base:bool', 'checkbox',
            'Derive upper threshold (for dark areas) or lower threshold '
            '(for lighter areas).')]


        
        if3 = itk.Image.F3
        self._isol_connect = \
                              itk.IsolatedConnectedImageFilter[if3,if3].New()

        # this will be our internal list of points
        self._seeds1 = []
        self._seeds2 = []

        itk_kit.utils.setupITKObjectProgress(
            self, self._isol_connect,
            'IsolatedConnectedImageFilter', 'Performing isolated connect')

        scriptedConfigModuleMixin.__init__(
            self, config_list,
            {'Module (self)' : self,
             'IsolatedConnectedImageFilter' :
             self._isol_connect})

        self.sync_module_logic_with_config()
        
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        for inputIdx in range(len(self.get_input_descriptions())):
            self.set_input(inputIdx, None)

        # this will take care of all display thingies
        scriptedConfigModuleMixin.close(self)
        # and the baseclass close
        moduleBase.close(self)

        del self._isol_connect

    def get_input_descriptions(self):
	return ('ITK Image data', 'Seed points 1', 'Seed points 2')
    
    def set_input(self, idx, input_stream):
        if idx == 0:
            self._isol_connect.SetInput(input_stream)

        else:

            seeds = [self._seeds1, self._seeds2]
            conn_map = {'ClearSeeds' : [self._isol_connect.ClearSeeds1,
                                        self._isol_connect.ClearSeeds2],
                        'AddSeeds' : [self._isol_connect.AddSeed1,
                                      self._isol_connect.AddSeed2],
                        'seeds' : [self._seeds1, self._seeds2]}
                          
            if input_stream == None:
                # this means we get to nuke all seeds
                conn_map['ClearSeeds'][idx-1]()

            elif hasattr(input_stream, 'devideType') and \
                 input_stream.devideType == 'namedPoints':

                dpoints = [i['discrete'] for i in input_stream]
                our_list = conn_map['seeds'][idx-1]
                # if the new list differs from ours, copy it
                if dpoints != our_list:
                    print "isolatedConnect: copying new list"
                    del our_list[:]
                    our_list.extend(dpoints)
                    conn_map['ClearSeeds'][idx-1]()

                    for p in our_list:
                        index = itk.Index[3]()
                        for ei in range(3):
                            index.SetElement(ei, int(p[ei]))
                            
                        conn_map['AddSeeds'][idx-1](index)

            else:
                raise TypeError, 'This input requires a named points type.'

    
    def get_output_descriptions(self):
	return ('Segmented ITK image', 'Derived threshold')
    
    def get_output(self, idx):
        if idx == 0:
            return self._isol_connect.GetOutput()
        else:
            return self._isol_connect.GetIsolatedValue()

    def logic_to_config(self):
        self._config.upper_threshold = \
                                     self._isol_connect.GetFindUpperThreshold()

        self._config.replace_value = self._isol_connect.GetReplaceValue()
        
    
    def config_to_logic(self):
        self._isol_connect.SetFindUpperThreshold(self._config.upper_threshold)
        self._isol_connect.SetReplaceValue(self._config.replace_value)
        
    
    def execute_module(self):
        self._isol_connect.Update()

    
    def _inputPointsObserver(self, obj):
        # extract a list from the input points
        tempList = []
        if self._inputPoints:
            for i in self._inputPoints:
                tempList.append(i['discrete'])
            
        if len(tempList) >= 2 and tempList != self._seedPoints:
            self._seedPoints = tempList
            #self._seedConnect.RemoveAllSeeds()

            idx1 = itk.itkIndex3()
            idx2 = itk.itkIndex3()
            
            for ei in range(3):
                idx1.SetElement(ei, self._seedPoints[0][ei])
                idx2.SetElement(ei, self._seedPoints[1][ei])

            self._isol_connect.SetSeed1(idx1)
            self._isol_connect.SetSeed2(idx2)



