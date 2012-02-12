# $Id$

from genMixins import subjectMixin, updateCallsExecuteModuleMixin

class imageStackClass(list,
                      subjectMixin,
                      updateCallsExecuteModuleMixin):
    
    def __init__(self, d3Module):
        # call base ctors
        subjectMixin.__init__(self)
        updateCallsExecuteModuleMixin.__init__(self, d3Module)

    def close(self):
        subjectMixin.close(self)
        updateCallsExecuteModuleMixin.close(self)

