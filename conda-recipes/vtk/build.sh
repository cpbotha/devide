#!/bin/bash

if [ `uname` == Linux ]; then
    CC=gcc44
    CXX=g++44
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

mkdir build
cd build

# deactivated OFFSCREEN and activated X instead
# also switching to the new programmable pipeline OpenGL2 renderer
$CMAKE \
    -DCMAKE_INSTALL_PREFIX:PATH="$PREFIX" \
    -DCMAKE_INSTALL_RPATH:STRING="$PREFIX/lib" \
    -DVTK_HAS_FEENABLEEXCEPT:BOOL=OFF \
    -DBUILD_TESTING:BOOL=OFF \
    -DBUILD_EXAMPLES:BOOL=OFF \
    -DBUILD_SHARED_LIBS:BOOL=ON \
    -DPYTHON_EXECUTABLE:FILEPATH=$PYTHON \
    -DPYTHON_INCLUDE_PATH:PATH=$PREFIX/include/python2.7 \
    -DPYTHON_LIBRARY:FILEPATH=$PREFIX/lib/$PY_LIB \
    -DVTK_USE_X:BOOL=OFF \
    -DVTK_WRAP_PYTHON:BOOL=ON \
    -DVTK_RENDERING_BACKEND:STRING="OpenGL2" \
    -DVTK_USE_OFFSCREEN:BOOL=OFF \
    -DVTK_USE_X:BOOL=ON \
    ..

# make the build use 8 concurrent processes
make -j8
make install

# with 6.2.0, these libs already end up in $PREFIX/lib/
# on my setup, that's anaconda/envs/_build/lib/
# if [ `uname` == Linux ]; then
#     mv $PREFIX/lib/VTK-6.2.0/lib* $PREFIX/lib
#     $REPLACE '/lib/VTK-6.2.0/lib' '/lib/lib' \
# 	     $PREFIX/lib/VTK-6.2.0/VTKTargets-debug.cmake
# fi

if [ `uname` == Darwin ]; then
    $SYS_PYTHON $RECIPE_DIR/osx.py
fi
