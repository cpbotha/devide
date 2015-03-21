
```
cd devide-re/devide/
hg pull
hg up -C
```
  * The last command will overwrite any uncommitted changes, this is to sync up the 12.2.7 devide.py with the main source repo.
  * Fix the broken PIP support:
    1. WINDOWS: edit DeVIDE-RE\dre.cfg and change "python: %(dre\_top)s\python\bin" to just "python: %(dre\_top)s\python" (i.e. remove the \bin)
    1. WINDOWS: edit DeVIDE-RE\dre.cfg and add these two lines to the end:
```
[env:pythonhome]
python: %(dre_top)s\python
```
    1. WINDOWS and LINUX: download an updated dre.py from http://code.google.com/p/devide/source/browse/core/dre.py?repo=dre and copy it OVER your existing dre.py in DeVIDE-RE
    1. LINUX: edit DeVIDE-RE/python/lib/python2.7/config/Makefile and change the "prefix = /some/absolute/path/..." to:
```
prefix = ${DRE_TOP}/python
```


  * Now we can use the fixed PIP to install some new packages that are required (psutil for memory monitor):
```
dre shell
pip install psutil
```

(If under Linux you get md5 / sha1 hashing errors running this last command, remember to install libssl0.9.8)