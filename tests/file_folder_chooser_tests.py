'''Unit tests for file chooser
'''
from guitest.gtktest import GtkTestCase
from pkg_resources import ResourceManager
from path import path

from baudot.widget import FileFolderChooser

SAMPLES = path(ResourceManager().resource_filename(__package__, "samples"))

class FileFolderChooserTest(GtkTestCase):
    '''Unit tests for FileFolderChooser class
    '''
    def test_init(self):
        '''Test __init__ method
        '''
        ffc = FileFolderChooser()
        self.assertIsNotNone(ffc)

    def test_selection(self):
        '''Test file selection scenarios
        '''
        ffc = FileFolderChooser()
        self.assertFalse(ffc.get_filenames())
        ffc.chooser.set_current_folder(SAMPLES / "dir1")
        empty_dir = SAMPLES / "dir1" / "empty"
        self.assertTrue(ffc.chooser.select_filename(empty_dir))
        