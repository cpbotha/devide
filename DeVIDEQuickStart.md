# Introduction #

So you've downloaded the DeVIDE DRE binaries and you're wondering how to get started.  You've come to the right place!

# Windows #

## Basic ##
  1. Double-click on the setup.exe that you've downloaded, wait for a few minutes as DeVIDE installs itself into \Program Files\DeVIDE (or some other directory of your choice).
  1. Once the installation is done, start DeVIDE by clicking on the DeVIDE icon on your desktop.
  1. Read the online help by pressing F1 or clicking [here](HelpIndex.md).  The [HelpGraphEditor](HelpGraphEditor.md) help section will get you started with a simple example.

## Getting to know the DRE ##

The DRE is the runtime environment that DeVIDE is based on.  You can use it for far more, for example running your own VTK / ITK examples outside of DeVIDE.
  1. Open a command window (WindowsKey-R 'cmd' ENTER, or start -> run -> cmd ENTER).
  1. Go to the directory where you installed DeVIDE:
```
c:
cd "\Program Files\DeVIDE"
```
  1. Read the DRE text help:
```
dre help
```
  1. Start an interactive Python shell:
```
dre ipythonwx
```
  1. Start your own Python script:
```
dre /full/path/to/your/script.py --switches --to --your --script
```
  1. ... or start DeVIDE itself:
```
dre devide
```

# Linux #

## Basic ##

  1. Untar the downloaded archive with:
```
tar xjvf devide-re-v12.2.7-lin64.tar.bz2
```
  1. Then startup DeVIDE:
```
cd devide-re-v12.2.7-lin64
./dre devide
```
  1. Read the online help by pressing F1 or clicking [here](HelpIndex.md).  The [HelpGraphEditor](HelpGraphEditor.md) help section will get you started with a simple example.
  1. If you're seeing errors starting up, please see the [Frequently Asked Questions](FAQ.md).

## Getting to know the DRE ##

The DRE is the runtime environment that DeVIDE is based on.  You can use it for far more, for example running your own VTK / ITK examples outside of DeVIDE.
  1. Start a terminal
  1. Go to the directory where you installed DeVIDE:
```
cd /some/dir/somewhere/devide-re-v9.8.3784-lin64
```
  1. Read the DRE text help:
```
./dre help
```
  1. Start an interactive Python shell:
```
./dre ipythonwx
```
  1. Start your own Python script:
```
./dre /full/path/to/your/script.py --switches --to --your --script
```
  1. ... or start DeVIDE itself:
```
./dre devide
```