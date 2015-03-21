# Introduction #

With the DeVIDE DICOMBrowser, released with 8.5, you can easily explore collections of DICOM data.  It is intended to be used as a visual interface with which DICOM series can be easily selected and loaded, using the companion DICOMReader module, into DeVIDE for further processing.

Below a screenshot of the DICOMBrowser GUI is shown:

![http://devide.googlecode.com/svn/wiki/help_images/dicombrowser_ss.png](http://devide.googlecode.com/svn/wiki/help_images/dicombrowser_ss.png)

Also see our introductory YouTube screencast:

<a href='http://www.youtube.com/watch?feature=player_embedded&v=iLfu6JXkWP4' target='_blank'><img src='http://img.youtube.com/vi/iLfu6JXkWP4/0.jpg' width='425' height=344 /></a>

# Starting the exploration #
Enter any number of directories and or filenames into the "Files and Directories to Scan" text input box, separated by semicolons.  You can either type these in yourself, cut and paste them from some other application, or make use of the "Add Dirs" and "Add Files" dialog buttons.

After having entered all paths that you wish to scan, click on the "Scan" button.  Post 8.5 versions of the DICOMBrowser will show a progress bar whilst scanning.

When scanning has been completed, all other panels in the interface will be filled out with information.

# Exploring your data #
DICOM data is divided up into studies, where each study is associated with a patient, a number of series per study, and a number of images per series.  The DICOMBrowser allows you to select any of these elements by clicking in the relevant panel.
Once you've selected a specific series, which can usually be seen as a single data volume, you can browse through the images in that series by clicking on the relevant file in the "Image Files" panel, or by making use of the Ctrl-N Ctrl-P hotkeys for next image and previous image, or by clicking on the image and then using the mousewheel to move, 1 image at a time, through the series.  Control-Mousewheel will skip 10 images at a time and allows rapid scrolling through a series.

# Loading data for further processing #
Once you have identified an interesting series, you can create a DICOMReader module on the DeVIDE canvas, and then drag directly from the series item or from a selection of filenames onto the DICOMReader.  The DICOMReader will now be configured with the correct filenames and can be executed to load the data for further processing by DeVIDE networks.

You can also drag a series or selection of files onto most file manager windows (explorer on Windows, nautilus on Gnome) to copy those files into the destination directory.

# Shortcuts #

| Ctrl-N, mousewheel down on image | Next image in series |
|:---------------------------------|:---------------------|
| Ctrl-P, mousewheel up on image | Previous image in series |
| Ctrl-mousewheel on image | Skip 10 images |
| Ctrl-0, Ctrl-1 | Change view layouts (default, max image) |