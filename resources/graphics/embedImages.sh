# embed used images into images.py
# $Id: embedImages.sh,v 1.4 2004/01/15 10:36:21 cpbotha Exp $

img2py -n devidelogo64x64 devidelogo64x64.png images.py
img2py -a -n devidelogo32x32 devidelogo32x32.png images.py

img2py -a -n devidelogom32x32 devidelogom32x32.png images.py

