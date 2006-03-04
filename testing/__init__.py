# testing.__init__.py copyright 2004 by Charl P. Botha http://cpbotha.net/
# $Id$
# this drives the devide unit testing.  neat huh?

import os
import time
import unittest

from testing import basic
from testing import graph_editor


# ----------------------------------------------------------------------------
class devideTesting:
    def __init__(self, devide_app):
        
#         self.basic_suite.addTest(graphEditorBasic('testStartup'))
#         self.basic_suite.addTest(graphEditorBasic('testModuleCreationDeletion'))
#         self.basic_suite.addTest(graphEditorBasic('testModuleHelp'))
#         self.basic_suite.addTest(graphEditorBasic('testSimpleNetwork'))
#         self.basic_suite.addTest(graphEditorBasic('testConfigVtkObj'))
#         self.basic_suite.addTest(testReadersWriters('testVTI'))

#         self.moduleSuite = unittest.TestSuite()
#         self.moduleSuite.addTest(testModulesMisc('testCreateDestroy'))

#         self.itkSuite = unittest.TestSuite()
#         self.itkSuite.addTest(testITKBasic('testConfidenceSeedConnect'))

#         suiteList = [self.basic_suite, self.moduleSuite]

        suite_list = [basic.get_suite(devide_app),
                      graph_editor.get_suite(devide_app)]

        # do check for presence of itk_kit
        #if _devideApp.mainConfig.useInsight:
        #    suiteList.append(self.itkSuite)

        self.main_suite = unittest.TestSuite(tuple(suite_list))
        
    def runAllTests(self):
        runner = unittest.TextTestRunner()
        runner.run(self.main_suite)

    def runSomeTest(self):
        someSuite = unittest.TestSuite()
        someSuite.addTest(testITKBasic('testConfidenceSeedConnect'))

        runner = unittest.TextTestRunner()
        runner.run(someSuite)

