# BatchConverter.py by Francois Malan - 2010-03-05. Updated 2011-12-11#

import os.path
from module_base import ModuleBase
from module_mixins import ScriptedConfigModuleMixin
import wx
import os
import vtk
import itk

class batchConverter(
    ScriptedConfigModuleMixin, ModuleBase):

    def __init__(self, module_manager):
        # initialise our base class
        ModuleBase.__init__(self, module_manager)

        self._config.source_folder = ''
        self._config.source_file_type = -1
        self._config.source_forced_numerical_type = 0
        self._config.source_numerical_type = 0
        self._config.target_folder = ''
        self._config.target_file_type = -2
        self._config.target_forced_numerical_type = 0
        self._config.target_numerical_type = 0
        self._config.overwrite = False
        self._config.delete_after_conversion = False

        #Make sure that the values below match the definitions in the config list!
        self._config.extensions = {0 : '.vti', 1 : '.mha', 2 : '.mhd', 3 : '.gipl'}
        self._vtk_data_types = (0, 1, 2)   #The list of the above extensions which are VTK types

        #Make sure that these two dictionaries match the definitions in the config list!
        self._config.data_types_by_number = {0 : 'auto', 1 : 'float', 2 : 'short', 3 : 'unsigned char', 4 : 'binary (uchar)'}
        self._config.data_types_by_name = {'auto' : 0, 'float' : 1, 'short' : 2, 'unsigned char' : 3, 'binary (uchar)' : 4}

        config_list = [
            ('Source Folder:', 'source_folder', 'base:str', 'dirbrowser',
             'Select the source directory'),
            ('Source type:', 'source_file_type', 'base:int', 'choice',
             'The source file type',
             ('VTK Imagedata (.vti)', 'MetaImage (.mha)', 'MetaImage: header + raw (.mhd, .raw)', 'Guys Image Processing Lab (.gipl)')),
            ('Read input as:', 'source_forced_numerical_type', 'base:int', 'choice',
             'The data type we assume the input to be in',
             ('auto detect', 'float', 'signed int', 'unsigned char', 'binary (uchar)')),
            ('Delete source after conversion', 'delete_after_conversion', 'base:bool', 'checkbox',
             'Do you want to delete the source files after conversion? (not recommended)'),
            ('Destination Folder:', 'target_folder', 'base:str', 'dirbrowser',
             'Select the target directory'),
            ('Destination type:', 'target_file_type', 'base:int', 'choice',
             'The destination file type',
             ('VTK Imagedata (.vti)', 'MetaImage (.mha)', 'MetaImage: header + raw (.mhd, .raw)', 'Guys Image Processing Lab (.gipl)')),
            ('Cast output to:', 'target_forced_numerical_type', 'base:int', 'choice',
             'The data type we cast and write the output to',
             ('auto detect', 'float', 'signed int', 'unsigned char', 'binary (uchar)')),
            ('Automatically overwrite', 'overwrite', 'base:bool', 'checkbox',
             'Do you want to automatically overwrite existing files?'),
             ]

        ScriptedConfigModuleMixin.__init__(
            self, config_list,
            {'Module (self)' : self})

        self.sync_module_logic_with_config()
           
    def close(self):
        # we play it safe... (the graph_editor/module_manager should have
        # disconnected us by now)
        #for input_idx in range(len(self.get_input_descriptions())): self.set_input(input_idx, None)

        # this will take care of GUI
        ScriptedConfigModuleMixin.close(self)

    def set_input(self):
        pass

    def get_input_descriptions(self):
        return ()

    def get_output_descriptions(self):
        return ()

#    def get_output(self, idx):
#        return ()

    def logic_to_config(self):
        pass

    def config_to_logic(self):
        pass

    def _read_input(self, source_file_path):
        """
        Reads the input specified by the source file path, according to the parameters chosen by the user
        """
        #We choose the correct reader for the job
        reader = None
        if self._config.source_file_type == 0:       # VTI
            reader = vtk.vtkXMLImageDataReader()
        elif self._config.source_file_type == 1 or self._config.source_file_type == 2:     # MHA or MHD
            reader = vtk.vtkMetaImageReader()
        elif self._config.source_file_type == 3:     # GIPL.
            #GIPL needs an ITK reader, and that needs an explicit type
            if self._config.source_forced_numerical_type == 0:  #auto

                # create ImageFileReader we'll be using for autotyping
                autotype_reader = itk.ImageFileReader[itk.Image.F3].New()

                #and the actual reader
                reader = itk.ImageFileReader[itk.Image.F3].New()
                reader_type_text_default = 'F3'

                autotype_reader.SetFileName(source_file_path)
                autotype_reader.UpdateOutputInformation()
                iio = autotype_reader.GetImageIO()
                comp_type = iio.GetComponentTypeAsString(iio.GetComponentType())
                if comp_type == 'short':
                    comp_type = 'signed_short'
                # lc will convert e.g. unsigned_char to UC
                short_type = ''.join([i[0].upper() for i in comp_type.split('_')])
                dim = iio.GetNumberOfDimensions()
                num_comp = iio.GetNumberOfComponents()

                reader_type_text = '%s%d' % (short_type, dim)
                if num_comp > 1:
                    # e.g. VF33
                    reader_type_text = 'V%s%d' % (reader_type_text, num_comp)

                # if things have changed, make a new reader, else re-use the old
                if reader_type_text != reader_type_text_default:
                    # equivalent to e.g. itk.Image.UC3
                    reader = itk.ImageFileReader[
                        getattr(itk.Image, reader_type_text)].New()
                    print '%s was auto-detected as ITK %s' % (source_file_path, reader_type_text)

                if reader_type_text == 'F3':
                    self._config.source_numerical_type = 1
                elif reader_type_text == 'SS3':
                    self._config.source_numerical_type = 2
                elif reader_type_text == 'UC3':
                    self._config.source_numerical_type = 3
                else:
                    print "Warning: data of type '%s' is not explicitly supported. Reverting to IF3 (float)." % reader_type_text
                    self._config.source_numerical_type = 1
                    reader = autotype_reader

            elif self._config.source_forced_numerical_type == 1:   #float
                reader = itk.ImageFileReader.IF3.New()
                self._config.source_numerical_type = 1
            elif self._config.source_forced_numerical_type == 2:   #short
                reader = itk.ImageFileReader.ISS3.New()
                self._config.source_numerical_type = 2
            elif self._config.source_forced_numerical_type == 3 or self._config.source_forced_numerical_type == 4:   #unsigned char
                reader = itk.ImageFileReader.IUC3.New()
                self._config.source_numerical_type = 3
            else:
                raise Exception('Undefined input data type with numerical index %d' % self._config.source_forced_numerical_type)
        else:
            raise Exception('Undefined file type with numerical index %d' % self._config.source_file_type)

        print "Reading %s ..." % source_file_path
        reader.SetFileName(source_file_path)
        reader.Update()
        return reader.GetOutput()

    def _convert_input(self, input_data):
        """
        Converts the input data so that it can be sent to the writer.
        This includes VTK to ITK conversion as well as type casting.
        """
        #These values will be used to determine if conversion is required
        source_is_vtk = self._config.source_file_type in self._vtk_data_types
        target_is_vtk = self._config.target_file_type in self._vtk_data_types

        #Set up the relevant data converter (e.g. VTK2ITK or ITK2VTK)
        converter = None
        caster = None
        output_data = None

        if source_is_vtk:            
            #We autotype the VTK data, and compare it to the specified input type, if specified
            auto_data_type_as_string = input_data.GetPointData().GetArray(0).GetDataTypeAsString()

            auto_data_type_as_number =  self._config.data_types_by_name[auto_data_type_as_string]
            if self._config.source_forced_numerical_type == 0:     #auto
                self._config.source_numerical_type = auto_data_type_as_number
            else:
                set_data_type_as_string = self._config.data_types_by_number[self._config.source_forced_numerical_type]
                if auto_data_type_as_number == self._config.source_forced_numerical_type:
                    self._config.source_numerical_type = self._config.source_forced_numerical_type
                else:
                    raise Exception("Auto-detected data type (%s) doesn't match specified type (%s)" % (auto_data_type_as_string, set_data_type_as_string) )

            #Perform type casting, if required
            if (self._config.source_numerical_type == self._config.target_forced_numerical_type) or (self._config.target_forced_numerical_type == 0):
                self._config.target_numerical_type = self._config.source_numerical_type
            else:
                self._config.target_numerical_type = self._config.target_forced_numerical_type
                print 'Type casting VTK data from (%s) to (%s)...' % (self._config.data_types_by_number[self._config.source_numerical_type], self._config.data_types_by_number[self._config.target_numerical_type])
                caster = vtk.vtkImageCast()
                caster.SetInput(input_data)
                if self._config.target_numerical_type == 1:      #float
                    caster.SetOutputScalarTypeToFloat()
                elif self._config.target_numerical_type == 2:    #short
                    caster.SetOutputScalarTypeToShort()
                elif self._config.target_numerical_type == 3 or self._config.target_numerical_type == 4:    #unsigned char
                    caster.SetOutputScalarTypeToUnsignedChar()

            if target_is_vtk:
                if caster == None:
                    output_data = input_data
                else:
                    caster.Update()
                    output_data = vtk.vtkImageData()
                    output_data.DeepCopy(caster.GetOutput())

            else:   #target is ITK - requires vtk2itk
                print 'Converting from VTK to ITK... (%s)' % self._config.data_types_by_number[self._config.target_numerical_type]

                if self._config.target_numerical_type == 1:      #float
                    converter = itk.VTKImageToImageFilter[itk.Image.F3].New()
                elif self._config.target_numerical_type == 2:    #short
                    converter = itk.VTKImageToImageFilter[itk.Image.SS3].New()
                elif self._config.target_numerical_type == 3 or self._config.target_numerical_type == 4:    #unsigned char
                    converter = itk.VTKImageToImageFilter[itk.Image.UC3].New()
                else:
                    raise Exception('Conversion of VTK %s to ITK not currently supported.' % data_types_by_number[source_dt])

                if caster == None:
                    converter.SetInput(input_data)
                else:
                    converter.SetInput(caster.GetOutput())

                converter.Update()
                output_data = converter.GetOutput()

        else:   #Source is ITK
            #The source type was already set when the data was read, so we don't need to autotype.
            #We don't know how to autotype ITK data anyway
            if self._config.source_numerical_type == 0:
                raise 'This should never happen - ITK data should be typed upon being read and not require autotyping'

            #Perform type casting, if required
            if (self._config.source_numerical_type == self._config.target_forced_numerical_type) or (self._config.target_forced_numerical_type == 0):
                self._config.target_numerical_type = self._config.source_numerical_type
            else:
                self._config.target_numerical_type = self._config.target_forced_numerical_type
                print 'Type casting ITK data from (%s) to (%s)...' % (self._config.data_types_by_number[self._config.source_numerical_type], self._config.data_types_by_number[self._config.target_numerical_type])

                if self._config.source_numerical_type == 1:       #float
                    if self._config.target_numerical_type == 2:   #short
                        caster = itk.CastImageFilter.IF3ISS3()
                    elif self._config.target_numerical_type == 3 or self._config.target_numerical_type == 4: #unsigned char
                        caster = itk.CastImageFilter.IF3IUC3()
                    else:
                        raise Exceception('Error - this case should not occur!')

                if self._config.source_numerical_type == 2:       #short
                    if self._config.target_numerical_type == 1:   #float
                        caster = itk.CastImageFilter.ISS3IF3()
                    elif self._config.target_numerical_type == 3 or self._config.target_numerical_type == 4: #unsigned char
                        caster = itk.CastImageFilter.ISS3IUC3()
                    else:
                        raise Exceception('Error - this case should not occur!')

                if self._config.source_numerical_type == 3 or self._config.source_numerical_type == 4:       #unsigned short
                    if self._config.target_numerical_type == 1:   #float
                        caster = itk.CastImageFilter.IUC3IF3()
                    elif self._config.target_numerical_type == 2: #short
                        caster = itk.CastImageFilter.IUC3ISS3()
                    else:
                        raise Exceception('Error - this case should not occur!')

                caster.SetInput(input_data)

            if not target_is_vtk:
                if caster == None:
                    output_data = input_data
                else:
                    caster.Update()
                    output_data = vtk.vtkImageData()
                    output_data.DeepCopy(caster.GetOutput())

            else:   #target is VTK - requires itk2vtk
                print 'Converting from ITK to VTK... (%s)' % self._config.data_types_by_number[self._config.target_numerical_type]

                if self._config.target_numerical_type == 1:      #float
                    converter = itk.ImageToVTKImageFilter[itk.Image.F3].New()
                elif self._config.target_numerical_type == 2:    #short
                    converter = itk.ImageToVTKImageFilter[itk.Image.SS3].New()
                elif self._config.target_numerical_type == 3 | self._config.target_numerical_type == 4:    #unsigned char
                    converter = itk.ImageToVTKImageFilter[itk.Image.UC3].New()
                else:
                    raise Exception('Conversion of ITK %s to VTK not currently supported.' % data_types_by_number[source_dt])

                data_to_convert = None
                if caster == None:
                    data_to_convert = input_data
                else:
                    data_to_convert = caster.GetOutput()                    

                #These three lines are from DeVIDE's ITKtoVTK. Not clear why, but it's necessary
                data_to_convert.UpdateOutputInformation()
                data_to_convert.SetBufferedRegion(data_to_convert.GetLargestPossibleRegion())
                data_to_convert.Update()
                
                converter.SetInput(data_to_convert)
                converter.Update()
                output_data = vtk.vtkImageData()
                output_data.DeepCopy(converter.GetOutput())
        
        return output_data

    def _write_output(self, data, target_file_path):
        #Check for existing target file, and ask for overwrite confirmation if required
        if (not self._config.overwrite) and os.path.exists(target_file_path):
            dlg = wx.MessageDialog(self._view_frame, "%s already exists! \nOverwrite?" % target_file_path,"File already exists",wx.YES_NO|wx.NO_DEFAULT)
            if dlg.ShowModal() == wx.ID_NO:
                print 'Skipped writing %s' % target_file_path
                if self._config.delete_after_conversion:
                    print 'Source %s not deleted, since no output was written' % source_file_path
                return    #skip this file if overwrite is denied

        writer = None
        if self._config.target_file_type == 0:       # VTI
            writer = vtk.vtkXMLImageDataWriter()
        elif self._config.target_file_type == 1:     # MHA
            writer = vtk.vtkMetaImageWriter()
            writer.SetCompression(True)
            writer.SetFileDimensionality(3)
        elif self._config.target_file_type == 2:     # MHD
            writer = vtk.vtkMetaImageWriter()
            writer.SetCompression(False)
            writer.SetFileDimensionality(3)            
        elif self._config.target_file_type == 3:     # GIPL. We assume floating point values.
            if self._config.target_numerical_type == 1:      #float
                writer = itk.ImageFileWriter.IF3.New()
            elif self._config.target_numerical_type == 2:    #short
                writer = itk.ImageFileWriter.ISS3.New()
            elif self._config.target_numerical_type == 3 or self._config.target_numerical_type == 4:    #unsigned char
                writer = itk.ImageFileWriter.IUC3.New()
            else:
                raise Exception('Writing ITK %s is not currently supported.' % data_types_by_number[source_dt])
        else:
            raise Exception('Undefined file type with numerical index %d' % self._config.target_file_type)

        final_data = data
        if self._config.target_numerical_type == 4:
            th = vtk.vtkImageThreshold()
            th.ThresholdByLower(0.0)
            th.SetInValue(0.0)
            th.SetOutValue(1.0)
            th.SetOutputScalarTypeToUnsignedChar()
            th.SetInput(data)
            th.Update()
            final_data = th.GetOutput()        
            
        #Write the output
        writer.SetInput(final_data)
        writer.SetFileName(target_file_path)
        print "Writing %s ..." % target_file_path
        writer.Write()

    def execute_module(self):
        if self._config.source_folder == '':
            dlg = wx.MessageDialog(self._view_frame, "No source folder specified", "No source folder",wx.OK)
            dlg.ShowModal()
            return
        elif self._config.target_folder == '':
            dlg = wx.MessageDialog(self._view_frame, "No destination folder specified", "No destination folder",wx.OK)
            dlg.ShowModal()
            return
        elif self._config.source_file_type < 0:
            dlg = wx.MessageDialog(self._view_frame, "No source type selected", "No source type",wx.OK)
            dlg.ShowModal()
            return
        elif self._config.target_file_type < 0:
            dlg = wx.MessageDialog(self._view_frame, "No destination type selected", "No destination type",wx.OK)
            dlg.ShowModal()
            return

        source_ext = self._config.extensions[self._config.source_file_type]
        target_ext = self._config.extensions[self._config.target_file_type]

        print 'Source type = %s, target type = %s' % (source_ext, target_ext)
        print 'source dir = %s' % (self._config.source_folder)
        print 'target dir = %s' % (self._config.target_folder)

        all_files = os.listdir(self._config.source_folder)

        #First we set up a list of files with the correct extension
        file_list = []
        source_ext = self._config.extensions[self._config.source_file_type]
        for f in all_files:
            file_name = os.path.splitext(f)
            if file_name[1] == source_ext:
                file_list.append(file_name[0])
        
        source_file_type_str = self._config.extensions[self._config.source_file_type]
        target_extension_str = self._config.extensions[self._config.target_file_type]

        #Iterate over all input files
        for file_prefix in file_list:
            #Read the input file
            source_file_name = '%s%s' % (file_prefix, source_file_type_str)
            source_file_path = os.path.join(self._config.source_folder, source_file_name)
            input_data = self._read_input(source_file_path)

            converted_data = self._convert_input(input_data)

            target_file_name = '%s%s' % (file_prefix, target_extension_str)
            target_file_path = os.path.join(self._config.target_folder, target_file_name)
            self._write_output(converted_data, target_file_path)
            
            #Now we delete the input IFF the check-box is checked, and only if source and destination names differ
            if self._config.delete_after_conversion:
                if source_file_path != target_file_path:
                    print 'Deleting source %s' % source_file_path
                    os.remove(source_file_path)
                else:
                    print 'Source not deleted, since already overwritten by output: %s' % source_file_path
                
        print 'Done'
