This is a temporary package to fix the case-sensitivity problems with ITK on
Windows.  "import itkcommon" can e.g. result in Python trying to import
ITKCommon.dll instead of itkcommon.py.

(this also happens with the pyInstaller as there is an ITKCommon.dll
as well as a
ITK-bin-dir/Wrapping/CSwig/Python/RelWithDebInfo/itkcommon.py)


