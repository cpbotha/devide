# $Id$

# this one was generated with:
# for i in *.py; do n=`echo $i | cut -f 1 -d .`; \
# echo -e "class $n:\n    kits = ['vtk_kit']\n    cats = ['Filters']\n" \
# >> blaat.txt; done

class appendPolyData:
    kits = ['vtk_kit']
    cats = ['Filters']

class clipPolyData:
    kits = ['vtk_kit']
    cats = ['Filters']

class closing:
    kits = ['vtk_kit']
    cats = ['Filters']

class contour:
    kits = ['vtk_kit']
    cats = ['Filters']

class decimate:
    kits = ['vtk_kit']
    cats = ['Filters']

class doubleThreshold:
    kits = ['vtk_kit']
    cats = ['Filters']

class extractGrid:
    kits = ['vtk_kit']
    cats = ['Filters']

class extractHDomes:
    kits = ['vtk_kit']
    cats = ['Filters']

class extractImageComponents:
    kits = ['vtk_kit']
    cats = ['Filters']

class glyphs:
    kits = ['vtk_kit']
    cats = ['Filters']

class greyReconstruct:
    kits = ['vtk_kit']
    cats = ['Filters']

class imageFillHoles:
    kits = ['vtk_kit']
    cats = ['Filters']

class imageFlip:
    kits = ['vtk_kit']
    cats = ['Filters']

class imageGaussianSmooth:
    kits = ['vtk_kit']
    cats = ['Filters']

class imageGradientMagnitude:
    kits = ['vtk_kit']
    cats = ['Filters']

class imageGreyDilate:
    kits = ['vtk_kit']
    cats = ['Filters']

class imageGreyErode:
    kits = ['vtk_kit']
    cats = ['Filters']

class ImageLogic:
    kits = ['vtk_kit']
    cats = ['Filters', 'Combine']

class ImageMask:
    kits = ['vtk_kit']
    cats = ['Filters', 'Combine']

class imageMathematics:
    kits = ['vtk_kit']
    cats = ['Filters', 'Combine']

class imageMedian3D:
    kits = ['vtk_kit']
    cats = ['Filters']

class landmarkTransform:
    kits = ['vtk_kit']
    cats = ['Filters']

class marchingCubes:
    kits = ['vtk_kit']
    cats = ['Filters']

class modifyHomotopy:
    kits = ['vtk_kit']
    cats = ['Filters']

class morphGradient:
    kits = ['vtk_kit']
    cats = ['Filters']

class opening:
    kits = ['vtk_kit']
    cats = ['Filters']

class MIPRender:
    kits = ['vtk_kit']
    cats = ['Volume Rendering']

class polyDataConnect:
    kits = ['vtk_kit']
    cats = ['Filters']

class polyDataNormals:
    kits = ['vtk_kit']
    cats = ['Filters']

class probeFilter:
    kits = ['vtk_kit']
    cats = ['Filters']

class resampleImage:
    kits = ['vtk_kit']
    cats = ['Filters']

class seedConnect:
    kits = ['vtk_kit']
    cats = ['Filters']

class selectConnectedComponents:
    kits = ['vtk_kit']
    cats = ['Filters']

class shellSplatSimple:
    kits = ['vtk_kit']
    cats = ['Volume Rendering']

class streamTracer:
    kits = ['vtk_kit']
    cats = ['Filters']

class surfaceToDistanceField:
    kits = ['vtk_kit']
    cats = ['Filters']

class transformPolyData:
    kits = ['vtk_kit']
    cats = ['Filters']

class transformVolumeData:
    kits = ['vtk_kit']
    cats = ['Filters']

class warpPoints:
    kits = ['vtk_kit']
    cats = ['Filters']

class wsMeshSmooth:
    kits = ['vtk_kit']
    cats = ['Filters']

