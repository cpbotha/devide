#!/bin/bash

if [ `uname` == Linux ]; then
    CC=gcc
    CXX=g++
    CMAKE=cmake
    PY_LIB="libpython2.7.so"
fi
if [ `uname` == Darwin ]; then
    CC=cc
    CXX=c++
    CMAKE=$SYS_PREFIX/bin/cmake
    PY_LIB="libpython2.7.dylib"
    export DYLD_LIBRARY_PATH=$PREFIX/lib
fi

# we're in gdcm-2.4.4 == $SRC_DIR
mkdir ../gdcm-build
cd ../gdcm-build

# deactivated OFFSCREEN and activated X instead
# also switching to the new programmable pipeline OpenGL2 renderer
$CMAKE \
    -DCMAKE_INSTALL_PREFIX:PATH="$PREFIX" \
    -DCMAKE_INSTALL_RPATH:STRING="$PREFIX/lib" \
    -DGDCM_BUILD_SHARED_LIBS:BOOL=ON \
    -DGDCM_USE_VTK:BOOL=ON \
    -DVTK_DIR:PATH=$PREFIX/lib/cmake/vtk-6.2 \
    -DGDCM_WRAP_PYTHON:BOOL=ON \
    -DSWIG_EXECUTABLE:FILEPATH=$PREFIX/bin/swig \
    -DPYTHON_EXECUTABLE:FILEPATH=$PYTHON \
    -DPYTHON_INCLUDE_PATH:PATH=$PREFIX/include/python2.7 \
    -DPYTHON_LIBRARY:FILEPATH=$PREFIX/lib/$PY_LIB \
    -DGDCM_INSTALL_PYTHONMODULE_DIR:PATH=$PREFIX/lib/python2.7/site-packages/ \
    $SRC_DIR

# make the build use 8 concurrent processes
make -j8
make install

