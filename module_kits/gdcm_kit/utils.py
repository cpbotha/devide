# Copyright (c) Charl P. Botha, TU Delft
# All rights reserved.
# See COPYRIGHT for details.

import gdcm

def sort_ipp(filenames):
    """STOP PRESS.  This is currently incomplete.  I'm waiting to see
    what's going to happen with the IPPSorter in GDCM.
    
    Given a list of filenames, make use of the gdcm scanner to sort
    them all according to IPP.

    @param filenames: list of full pathnames that you want to have
    sorted.
    @returns: tuple with (average z space, 
    """

    s = gdcm.Scanner()
    
    # we need the IOP and the IPP tags
    iop_tag = gdcm.Tag(0x0020, 0x0037)
    s.AddTag(iop_tag)
    ipp_tag = gdcm.Tag(0x0020, 0x0032) 
    s.AddTag(ipp_tag)

    ret = s.Scan(filenames)
    if not ret:
        return (0, [])

    for f in filenames:
        mapping = s.GetMapping(f)

        pttv = gdcm.PythonTagToValue(mapping)
        pttv.Start()
        while not pttv.IsAtEnd():
            tag = pttv.GetCurrentTag()
            val = pttv.GetCurrentValue()
