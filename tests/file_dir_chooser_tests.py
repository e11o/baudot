'''Unit tests for file chooser
'''
from guitest.gtktest import GtkTestCase

from baudot.gui import FileDirChooser


class FileDirChooserTest(GtkTestCase):
    '''Unit tests for FileDirChooser class
    '''
    def test_init(self):
        '''Test __init__ method
        '''
        chooser = FileDirChooser()
        self.assertIsNotNone(chooser)
