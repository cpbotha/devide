# Copyright (c) Charl P. Botha, TU Delft.
# All rights reserved.
# See COPYRIGHT for details.


# wxTreeListCtrl
# wx.TR_HIDE_ROOT

import gdcm

from moduleBase import moduleBase
#from moduleMixins import introspectModuleMixin
from moduleMixins import noConfigModuleMixin
# eventually this is going to be a full view module
# while we are experimenting, it's a noConfig

class Study:
    def __init__(self):
        self.patient_name = None
        self.study_uid = None
        self.study_description = None
        self.study_date = None
        # maps from series_uid to Series instance
        self.series_dict = {}

class Series:
    def __init__(self):
        self.series_uid = None
        self.series_description = None
        self.modality = None
        self.filenames = []

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
        # Study description (0008,1030)
        # Series UID (0020,000E)

        tag_to_symbol = {
                (0x0008, 0x0018) : 'instance_uid',
                (0x0010, 0x0010) : 'patient_name',
                (0x0010, 0x0020) : 'patient_id',
                (0x0020, 0x000d) : 'study_uid',
                (0x0008, 0x1030) : 'study_description',
                (0x0008, 0x0020) : 'study_date',
                (0x0020, 0x000e) : 'series_uid',
                (0x0008, 0x103e) : 'series_description',
                (0x0008, 0x0060) : 'modality'
                }

        # only do this if path is a directory
        d = gdcm.Directory()
        nfiles = d.Load(path, True)

        s = gdcm.Scanner()
        # add the tags we want to the scanner
        for tag_tuple in tag_to_symbol:
            tag = gdcm.Tag(*tag_tuple)
            s.AddTag(tag)

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

        # maps from study_uid to instance of Study
        study_dict = {} 

        for f in d.GetFilenames():
            mapping = s.GetMapping(f)

            # with this we can iterate through all tags for this file
            # let's store them all...
            file_tags = {}
            pttv = gdcm.PythonTagToValue(mapping)
            pttv.Start()
            while not pttv.IsAtEnd():
                tag = pttv.GetCurrentTag() # gdcm::Tag
                val = pttv.GetCurrentValue() # string

                symbol = tag_to_symbol[(tag.GetGroup(), tag.GetElement())]
                file_tags[symbol] = val

                pttv.Next()

            # take information from file_tags, stuff into all other
            # structures...

            # we need at least study and series UIDs to continue
            if not ('study_uid' in file_tags and \
                    'series_uid' in file_tags):
                continue
            
            study_uid = file_tags['study_uid']
            series_uid = file_tags['series_uid']
            
            try:
                study = study_dict[study_uid]
            except KeyError:
                # create new study instance
                study = Study()
                study.study_uid = study_uid
                study_dict[study_uid] = study

            try:
                series = study.series_dict[series_uid]
            except KeyError:
                series = Series()
                series.series_uid = series_uid
                # these should be the same over the whole series
                # fixme: could be that they don't exist (handle)
                series.series_description = \
                    file_tags['series_description']
                series.modality = file_tags['modality']

                study.series_dict[series_uid] = series

            series.filenames.append(f)

        return study_dict


        

