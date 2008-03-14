# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.


import gdcm

from moduleBase import moduleBase
#from moduleMixins import introspectModuleMixin
from moduleMixins import noConfigModuleMixin
# eventually this is going to be a full view module
# while we are experimenting, it's a noConfig

class DICOMBrowser(noConfigModuleMixin, moduleBase):
    def __init__(self, module_manager):
        moduleBase.__init__(self, module_manager)

        noConfigModuleMixin.__init__(
            self,
            {'Module (self)' : self})

        self.sync_module_logic_with_config()

    def close(self):
        noConfigModuleMixin.close(self)

    def get_input_descriptions(self):
        return ()

    def get_output_descriptions(self):
        return ()

    def set_input(self, idx, input_stream):
        pass

    def get_output(self, idx):
        pass

    def execute_module(self):
        pass

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass

    def view_NOT(self):
        pass

    def _scan(self, path):
        """Given a list combining filenames and directories, search
        recursively to find all valid DICOM files.  Build
        dictionaries.
        """

        # UIDs are unique for their domains.  Patient ID for example
        # is not unique.
        # Instance UID (0008,0018)
        # Patient ID (0010,0020)
        # Study UID (0020,000D) - data with common procedural context
        # Series UID (0020,000E)

        # only do this if path is a directory
        d = gdcm.Directory()
        nfiles = d.Load(path, True)

        s = gdcm.Scanner()
        tag_study_uid = gdcm.Tag(0x0020, 0x000d) # study UID
        tag_series_uid = gdcm.Tag(0x0020, 0x000e) # series UID

        s.AddTag(tag_study_uid)
        s.AddTag(tag_series_uid)


        ret = s.Scan(d.GetFilenames())
        if not ret:
            print "scanner failed"
            return

        # s now contains a Mapping (std::map) from filenames to stuff
        # calling s.GetMapping(full filename) returns a TagToValue
        # which we convert for our own use with a PythonTagToValue
        #pttv = gdcm.PythonTagToValue(mapping)

        # what i want:
        # a list of studies (indexed on study id): each study object
        # contains metadata we want to list per study, plus a list of
        # series belonging to that study.
        

        return d, s


        

