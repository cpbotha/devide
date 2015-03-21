# Requirements #

  * Volumes.
  * Slices, both in space and orthogonal (linked motion).

# Plugins #

  * ViewerNG has small core with bunches of plugins.  Each plugin does a tab in the interface.
  * Each ViewerNG plugin can register for events with ViewerNG input changes (and others).  A plugin HAS to delete all internal references to a given input when it is disconnected from ViewerNG.
  * Should the slice viewer also be a plugin?  basic 3d + 2d views probably not.  stuff like superimposed label maps == definitely plugins.