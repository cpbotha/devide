# Introduction #

This page shows how to load DICOM, then edit its tags or metadata, and then how to save the data as either slice-per-file (currently most popular for DICOM) or multi-slice per file (you get one DICOM file for your whole series).

# Details #

Refer to the figure below during the following explanation:

![http://devide.googlecode.com/svn/wiki/help_images/devide_edit_dicom_metadata.png](http://devide.googlecode.com/svn/wiki/help_images/devide_edit_dicom_metadata.png)

First load a DICOM dataset as explained on the [DICOM Basics](HelpDICOMBasics.md) page. Pass the second output of the DICOMReader module through an EditMedicalMetaData. The output of the DICOMReader goes to the first input of a DICOMWriter, and the output of the EditMedicalMetaData goes to the second input of the DICOMWriter.

You have to execute the network once to initialise the EditMedicalMetaData (the DICOMWriter might complain, ignore that for now). Now you can edit the various tags in the EditMedicalMetaData. Remember to click on Apply when you're done.

Finally, configure the DICOMWriter, and then click Execute. You should now have a new modified DICOM dataset in the location that you specified.