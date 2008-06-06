"""Module to test basic DeVIDE functionality.
"""

import unittest

class BasicMiscTest(unittest.TestCase):
    def test_sqlite3(self):
        """Test if sqlite3 is available.
        """

        import sqlite3
        
        v = sqlite3.version

        conn = sqlite3.connect(':memory:')
        cur = conn.cursor()
        cur.execute('create table stuff (some text)')
        cur.execute('insert into stuff values (?)', (v,))
        cur.close()

        cur = conn.cursor()
        cur.execute('select some from stuff')
        # cur.fetchall() returns a list of tuples: we get the first
        # item in the list, then the first element in that tuple, this
        # should be the version we inserted.
        self.failUnless(cur.fetchall()[0][0] == v)


def get_suite(devide_testing):
    devide_app = devide_testing.devide_app
    
    mm = devide_app.get_module_manager()

    misc_suite = unittest.TestSuite()

    t = BasicMiscTest('test_sqlite3')
    misc_suite.addTest(t)


    return misc_suite


