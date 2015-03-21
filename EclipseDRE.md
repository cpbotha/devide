# Introduction #

This howto explains how you should go about using Eclipse to edit your DRE-enabled (Python, VTK, ITK, numpy, etc.) or DeVIDE source code. In other words, if you want the easiest nicest bestest method to get started with VTK, ITK or numpy code in your eclipse, you are now at the right place!

# Details #

  1. If you don't have a file called "drepython.cmd" (on Windows) or "drepython" (in Linux) in your DeVIDE top-level directory, alongside dre.cmd / dre, download it from http://code.google.com/p/devide/source/browse/dre/core/drepython.cmd or http://code.google.com/p/devide/source/browse/dre/core/drepython.
  1. You'll always have to start eclipse from the command-line (on Windows and Linux), after having executed "dre shell" in that same command-line. Note that when you do this, it'll appear as if nothing happens. However, the DRE is doing all kinds of groovy things to your environment. On Windows it should look something like this:
```
C:\>cd "\Program Files\DeVIDE-RE"
C:\Program Files\DeVIDE-RE>dre shell
Microsoft Windows [Version 6.1.7601]
Copyright (c) 2009 Microsoft Corporation.  All rights reserved.
C:\Program Files\DeVIDE-RE>cd \Apps\eclipse64
C:\Apps\eclipse64>eclipse.exe
```
  1. Make sure you have [PyDev](http://pydev.org/) installed in Eclipse, with optionally Aptana Studio 3.
  1. Create a new PyDev project (File | New) and then either start from scratch, or point it at your DeVIDE / DRE project source code directory.
  1. At one point, you'll be able to choose the interpreter that is going to be used (for an existing project you can find it in Project Properties | PyDev - Interpreter Grammar).
    1. Click on "Click here to configure an interpreter not listed"
    1. Click on "New" then enter "DREPython" as the interpreter name, and select your drepython.cmd / drepython script as the interpreter executable. Click on OK.
    1. Select ALL FOLDERS to be added to the pythonpath, then click on OK.
    1. Click OK again, and wait for Eclipse to scan through all of the DRE.

You can now edit DRE-dependent (e.g. DeVIDE) source code with all of the Eclipse trappings, such as code completion, inline documentation and so forth. For example, with "devide.py" active, press "Ctrl-F11" to execute the whole business. If you're only editing a module (and not the DeVIDE core), it's of course better and faster to just reload that module.

# Screencast #

Here's a screencast demonstrating how to get this going on Linux:

<a href='http://www.youtube.com/watch?feature=player_embedded&v=-b1zS536R2M' target='_blank'><img src='http://img.youtube.com/vi/-b1zS536R2M/0.jpg' width='425' height=344 /></a>