# $Id: transformStackClass.py,v 1.1 2003/12/09 14:01:26 cpbotha Exp $

from genMixins import subjectMixin, updateCallsExecuteModuleMixin

class transformStackClass(list,
                          subjectMixin,
                          updateCallsExecuteModuleMixin):
    
    def __init__(self, d3Module):
        # call base ctors
        subjectMixin.__init__(self)
        updateCallsExecuteModuleMixin.__init__(self, d3Module)

    def close(self):
        subjectMixin.close(self)
        updateCallsExecuteModuleMixin.close(self)

