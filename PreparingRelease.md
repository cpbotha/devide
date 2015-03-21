# Mercurial-era strategy (new) #
  1. We only branch if the repos are busy for some or other reason.
  1. Make sure the Changelog-Summary is up to date
  1. Edit johannes/config.py and set revision IDs for DeVIDE, VTKDEVIDE and the DRE, as well as the date version for DeVIDE.
  1. Edit johannes.cfg in your build dir, ensure that all library versions are what you want.
  1. do a full build with johannes (okay, you can cheat a bit if you have a full build-dir, just make sure you know what you're doing)
  1. commit fixes until full test suite runs successfully
  1. update the johannes config.py revision IDs one last time.
  1. remove builds of install packages that had test suite related fixes
  1. re-run johannes to update builds
  1. make packages
  1. announce!

# SVN-era strategy (old) #
  1. branch SVN, name branch vX-Y where X is the year and Y the month of the planned release, e.g. v8-2
```
svn copy https://devide.googlecode.com/svn/trunk/ \
https://devide.googlecode.com/svn/branches/v9-8 \
-m "Creating branch in preparation for release."
```
  1. in the branch, update the SVN urls of the relevant johannes install packages (things in DeVIDE SVN):
    * vtkdevide
    * devide
    * setupenvironment (dre checkout)
  1. make sure the Changelog-Summary is up to date
  1. change VERSION variable in devide.py from 'DEV' to 'X.Y'
  1. update the johannes config.py file with a new STAMP and commit so that it contains the latest release number for that branch
  1. do a full build with johannes (okay, you can cheat a bit if you have a full build-dir, just make sure you know what you're doing)
  1. commit fixes until full test suite runs successfully
  1. update the johannes config.py STAMP one last time
  1. remove builds of install packages that had test suite related fixes
  1. re-run johannes to update builds
  1. make packages
  1. announce!