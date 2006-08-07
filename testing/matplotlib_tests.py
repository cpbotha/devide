"""Module to test basic matplotlib functionality.
"""

import os
import unittest
import tempfile

class MPLTest(unittest.TestCase):
    def test_figure_output(self):
        """Test if matplotlib figure can be generated and wrote to disc.
        """

        # make sure the pythonshell is running
        self._devide_app.get_interface()._handler_menu_python_shell(None)

        # create new figure
        python_shell = self._devide_app.get_interface()._python_shell
        f = python_shell.mpl_new_figure()
        import pylab

        # make sure we hardcode the font!
        pylab.rcParams['font.sans-serif'] = ['Bitstream Vera Sans']
        pylab.rc('font', family='sans-serif')

        from pylab import arange, plot, sin, cos, legend, grid, xlabel, ylabel
        a = arange(-30, 30, 0.01)
        plot(a, sin(a) / a, label='sinc(x)')
        plot(a, cos(a), label='cos(x)')
        legend()
        grid()
        xlabel('x')
        ylabel('f(x)')

        # width and height in inches
        f.set_figwidth(7.9)
        f.set_figheight(5.28)

        # and save it to disc
        filename1 = tempfile.mktemp(suffix='.png', prefix='tmp', dir=None)
        f.savefig(filename1, dpi=100)

        # get rid of the figure
        python_shell.mpl_close_figure(f)

        # now compare the bugger
        test_fn = os.path.join(self._devide_testing.get_images_dir(),
                               'mpl_test_figure_output.png')

        err = self._devide_testing.compare_png_images(test_fn, filename1)

        self.failUnless(err == 0, '%s differs from %s, err = %.2f' %
                        (filename1, test_fn, err))


def get_suite(devide_testing):
    devide_app = devide_testing.devide_app
    
    # both of these tests require wx
    mm = devide_app.get_module_manager()

    mpl_suite = unittest.TestSuite()

    if 'matplotlib_kit' in mm.module_kits.module_kit_list:
        t = MPLTest('test_figure_output')
        t._devide_app = devide_app
        t._devide_testing = devide_testing
        mpl_suite.addTest(t)

    return mpl_suite

    
    
