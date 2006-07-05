import itkConfig
import glob
import os

# Tree() makes a TOC, i.e. a list of tuples with (app_dir relative
# destination, full source file path, 'DATA')

# on windows this doesn't work, because the python files are somewhere
# in RelWithDebInfo...

# we want:
# itk_kit/wrapitk/py (*.py and Configuration and itkExtras subdirs from 
#                     WrapITK/Python)
# itk_kit/wrapitk/lib (*.py and *.so from WrapITK/lib)

def get_wrapitk_tree():

    # WrapITK/lib -> itk_kit/wrapitk/lib
    lib_files = glob.glob('%s/*.py' % (itkConfig.swig_lib,))
    lib_files.extend(glob.glob('%s/*.so' % (itkConfig.swig_lib,)))
    wrapitk_lib = [('module_kits/itk_kit/wrapitk/lib/%s' %
                    (os.path.basename(i),), i, 'DATA') for i in lib_files]

    # WrapITK/Python -> itk_kit/wrapitk/python
    py_path = os.path.normpath(os.path.join(itkConfig.config_py, '..'))
    py_files = glob.glob('%s/*.py' % (py_path,))
    wrapitk_py = [('module_kits/itk_kit/wrapitk/python/%s' %
                   (os.path.basename(i),), i, 'DATA') for i in py_files]

    # WrapITK/Python/Configuration -> itk_kit/wrapitk/python/Configuration
    config_files = glob.glob('%s/*.py' %
                             (os.path.join(py_path,'Configuration'),))
    wrapitk_config = [('module_kits/itk_kit/wrapitk/python/Configuration/%s' %
                       (os.path.basename(i),), i, 'DATA')
                      for i in config_files]

    # complete tree
    wrapitk_tree = wrapitk_lib + wrapitk_py + wrapitk_config

    return wrapitk_tree

