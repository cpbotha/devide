Hereby the release of DeVIDE version 9.8 is announced.

DeVIDE, or the Delft Visualization and Image processing Development Environment, is a Python-based dataflow application builder that enables the rapid prototyping of medical visualization and image processing applications via visual programming. In other words, by visually connecting functional blocks (think Yahoo pipes), you can create cool visualizations.  DeVIDE is primarily used in medical visualization research and education.

From release 9.8 onwards, DeVIDE is distributed as part of the DRE, or DeVIDE Runtime Environment. The DRE is in fact a Python distribution that includes cmake, swig, Python, numpy, matplotlib, wxPython, gdcm, VTK, ITK and DeVIDE itself. With the DRE, you can easily develop your own Python applications and also C++ extension modules, as the C++ SDK is included. See the DRE help page for more details.

The central information point is the [main DeVIDE homepage](http://visualisation.tudelft.nl/Projects/DeVIDE), with links to more documentation, binary and source downloads, the mailing list and a news blog.

For a summary of the changes in the new DeVIDE version 9.8, see the [ChangeLog-Summary](http://code.google.com/p/devide/source/browse/branches/v9-8/devide/docs/ChangeLog-Summary.txt).

Each release of DeVIDE contains some major new cool functionality, or at least that's the idea.  9.8 is all about the DRE, or the DeVIDE Runtime Environment.  Read more about the DRE on the [DRE Help Page](HelpDRE.md).

Due to the magnitude of the recent changes, there is a high probability that you run into serious problems.  I have tested on a number of virtual machines, but you never know.  If you come across any bugs, or have any suggestions for improvements, please enter them in the [Issue Tracker](http://code.google.com/p/devide/issues/list).  You can keep up to date on DeVIDE news by subscribing to the [blog](http://devidenews.wordpress.com/) or the [mailing list](http://groups.google.com/group/devide-users).