# testing.__init__.py copyright 2006 by Charl P. Botha http://cpbotha.net/
# $Id$
# this drives the devide unit testing.  neat huh?

import os
import time
import unittest

from testing import basic_wx
from testing import graph_editor

module_list = [basic_wx, graph_editor]
for m in module_list:
    reload(m)


# ----------------------------------------------------------------------------
class DeVIDETesting:
    def __init__(self, devide_app):

        self._devide_app = devide_app
        
        suite_list = [basic_wx.get_suite(devide_app),
                      graph_editor.get_suite(devide_app)]

        # do check for presence of itk_kit
        #if _devideApp.mainConfig.useInsight:
        #    suiteList.append(self.itkSuite)

        self.main_suite = unittest.TestSuite(tuple(suite_list))
        
    def runAllTests(self):
        runner = unittest.TextTestRunner()
        runner.run(self.main_suite)

    def runSomeTest(self):
        some_suite = graph_editor.get_some_suite(self._devide_app)

        runner = unittest.TextTestRunner()
        runner.run(some_suite)

