"""InsightToolkit support module to help load its packages."""
import sys,os

# Python "help(sys.setdlopenflags)" states:
#
# setdlopenflags(...)
#     setdlopenflags(n) -> None
#     
#     Set the flags that will be used for dlopen() calls. Among other
#     things, this will enable a lazy resolving of symbols when
#     importing a module, if called as sys.setdlopenflags(0) To share
#     symbols across extension modules, call as
#
#     sys.setdlopenflags(dl.RTLD_NOW|dl.RTLD_GLOBAL)
#
# GCC 3.x depends on proper merging of symbols for RTTI:
#   http://gcc.gnu.org/faq.html#dso
#

def preimport():
  """Called by InsightToolkit packages before loading a C module."""
  # Save the current dlopen flags and set the ones we need.
  try:
    import dl
    newflags = dl.RTLD_NOW|dl.RTLD_GLOBAL
  except:
    newflags = 0x102  # No dl module, so guess (see above).
  try:
    oldflags = sys.getdlopenflags()
    sys.setdlopenflags(newflags)
  except:
    oldflags = None

  return oldflags

def postimport(data):
  """Called by InsightToolkit packages after loading a C module."""
  # Restore the original dlopen flags.
  try:
    sys.setdlopenflags(data)
  except:
    pass
