"""Module for independently packaging up whole WrapITK tree.
"""

import itkConfig
import glob
import os
import shutil
import sys

# customise the following variables

if sys.platform == 'win32':
    SO_EXT = 'dll'
    SO_GLOB = '*.%s' % (SO_EXT,)
    raise RuntimeError('Finding of ITK_SO_DIR has to be fixed for windows!')
    ITK_SO_DIR = 'c:/opt/ITK/bin'

else:
    SO_EXT = 'so'
    SO_GLOB = '*.%s.*' % (SO_EXT,)

    # first go down to Insight/lib/InsightToolkit/WrapITK/lib
    os.chdir(itkConfig.swig_lib)
    # then go up twice
    os.chdir(os.path.join('..', '..'))
    # then find the curdir
    ITK_SO_DIR = os.path.abspath(os.curdir)


# Tree() makes a TOC, i.e. a list of tuples with (app_dir relative
# destination, full source file path, 'DATA')

# on windows this doesn't work, because the python files are somewhere
# in RelWithDebInfo...

# we want:
# itk_kit/wrapitk/py (*.py and Configuration and itkExtras subdirs from 
#                     WrapITK/Python)
# itk_kit/wrapitk/lib (*.py and *.so from WrapITK/lib)

def get_wrapitk_tree2():

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

def get_wrapitk_tree():
    """Return tree relative to itk_kit/wrapitk top.
    """
    
    # WrapITK/lib -> itk_kit/wrapitk/lib (py files, so/dll files)
    lib_files = glob.glob('%s/*.py' % (itkConfig.swig_lib,))
    lib_files.extend(glob.glob('%s/*.%s' % (itkConfig.swig_lib, SO_EXT)))

    # on Windows we also need the SwigRuntime.dll in c:/opt/WrapITK/bin!
    # the files above on Windows are in:
    # C:\\opt\\WrapITK\\lib\\InsightToolkit\\WrapITK\\lib
    if sys.platform == 'win32':
        bin_path = os.path.normpath(
            os.path.join(itkConfig.swig_lib, '../../../../bin'))
        lib_files.extend(glob.glob('%s/%s' % (bin_path, SO_GLOB)))
    
    wrapitk_lib = [('lib/%s' %
                    (os.path.basename(i),), i) for i in lib_files]

    # WrapITK/Python -> itk_kit/wrapitk/python (py files)
    py_path = os.path.normpath(os.path.join(itkConfig.config_py, '..'))
    py_files = glob.glob('%s/*.py' % (py_path,))
    wrapitk_py = [('python/%s' %
                   (os.path.basename(i),), i) for i in py_files]

    # WrapITK/Python/Configuration -> itk_kit/wrapitk/python/Configuration
    config_files = glob.glob('%s/*.py' %
                             (os.path.join(py_path,'Configuration'),))
    wrapitk_config = [('python/Configuration/%s' %
                       (os.path.basename(i),), i)
                      for i in config_files]

    # itkExtras
    extra_files = glob.glob('%s/*.py' % (os.path.join(py_path, 'itkExtras'),))
    wrapitk_extra = [('python/itkExtras/%s' %
                      (os.path.basename(i),), i) for i in extra_files]

    # complete tree
    wrapitk_tree = wrapitk_lib + wrapitk_py + wrapitk_config + wrapitk_extra

    return wrapitk_tree

def get_itk_so_tree():
    """Get the ITK DLLs themselves.

    Return tree relative to itk_kit/wrapitk top.
    """

    so_files = glob.glob('%s/%s' % (ITK_SO_DIR, SO_GLOB))
    itk_so_tree = [('lib/%s' % (os.path.basename(i),), i) for i in so_files]
    return itk_so_tree


def copy3(src, dst):
    """Same as shutil.copy2, but copies symlinks as they are, i.e. equivalent
    to --no-dereference parameter of cp.
    """

    dirname = os.path.dirname(dst)
    if dirname and not os.path.exists(dirname):
        os.makedirs(dirname)

    if os.path.islink(src):
        linkto = os.readlink(src)
        os.symlink(linkto, dst)

    else:
        shutil.copy2(src, dst)


def install(devide_app_dir):
    """Install a self-contained wrapitk installation in itk_kit_dir.
    """

    itk_kit_dir = os.path.join(devide_app_dir, 'module_kits/itk_kit')

    print "Deleting existing wrapitk dir."
    sys.stdout.flush()
    witk_dest_dir = os.path.join(itk_kit_dir, 'wrapitk')
    if os.path.exists(witk_dest_dir):
        shutil.rmtree(witk_dest_dir)

    print "Creating list of WrapITK files..."
    sys.stdout.flush()
    wrapitk_tree = get_wrapitk_tree()

    print "Copying WrapITK files..."
    sys.stdout.flush()
    for f in wrapitk_tree:
        copy3(f[1], os.path.join(witk_dest_dir, f[0]))

    print "Creating list of ITK shared objects..."
    sys.stdout.flush()
    itk_so_tree = get_itk_so_tree()

    print "Copying ITK shared objects..."
    sys.stdout.flush()
    for f in itk_so_tree:
        copy3(f[1], os.path.join(witk_dest_dir, f[0]))

    if sys.platform == 'win32':
        # on Windows, it's not easy setting the DLL load path in a running
        # application.  You could try SetDllDirectory, but that only works
        # since XP SP1.  You could also change the current dir, but our DLLs
        # are lazy loaded, so no go.  An invoking batchfile is out of the
        # question.
        print "Moving all SOs back to main DeVIDE dir [WINDOWS] ..."
        lib_path = os.path.join(witk_dest_dir, 'lib')
        so_files = glob.glob(os.path.join(lib_path, SO_GLOB))
        for so_file in so_files:
            shutil.move(so_file, devide_app_dir)

        #also write list of DLLs that were moved to lib_path/moved_dlls.txt
        f = file(os.path.join(lib_path, 'moved_dlls.txt'), 'w')
        f.writelines(['%s\n' % (os.path.basename(fn),) for fn in so_files])
        f.close()
    

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print "Specify devide app dir as argument."

    else:
        install(sys.argv[1])
    
