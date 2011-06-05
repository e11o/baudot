import unittest
from guitest.gtktest import GtkTestCase, guistate
from guitest.utils import mainloop_handler
import gtk

from pkg_resources import resource_filename
from path import path

from baudot.gui import MainWindow, FileManager

samples = path(resource_filename(__package__, "samples"))

class FileChooserStub(object):
    def run(self):
        return gtk.RESPONSE_OK
    def get_selection(self):
        return samples / "dir1"
    def destroy(self):
        pass

class CharsetChooserStub(object):
    def __init__(self, path, charset):
        pass
    def run(self):
        return gtk.RESPONSE_APPLY
    def get_selected_charset(self):
        return "UTF-8"
    def destroy(self):
        pass

charset= copy_to = None
class FileManagerStub(FileManager):
    def convert_files(self, _charset, _copy_to):
        #store values in globals
        global charset, copy_to
        charset = _charset
        copy_to = _copy_to

class MainWindowTest(GtkTestCase):
    overrides = {'baudot.gui.FileDirChooser' : FileChooserStub,
                 'baudot.gui.CharsetChooser' : CharsetChooserStub,
                 'baudot.gui.FileManager' : FileManagerStub}

    def test_init(self):
        win = MainWindow()
        self.assertIsNotNone(win)
        self.assertEqual("UTF-8", win.charset_cmb.get_active_text())
        self.assertEqual(0, len(win.fm))

    def test_add_file(self):
        win = MainWindow()
        self.assertEqual(0, len(win.fm))
        win.add_action.activate()
        self.assertEqual(1, len(win.fm))
        self.assertEqual(samples / "dir1", win.fm.store[0][0])

    def test_remove(self):
        win = MainWindow()
        win.add_action.activate()
        self.assertEqual(1, len(win.fm))
        self.assertFalse(win.remove_action.get_sensitive())
        win.selection.select_path("0")
        self.assertTrue(win.remove_action.get_sensitive())
        win.remove_action.activate()
        self.assertEqual(0, len(win.fm))
        self.assertFalse(win.remove_action.get_sensitive())

    def test_edit_charset(self):
        win = MainWindow()
        win.add_action.activate()
        self.assertEqual(1, len(win.fm))
        self.assertFalse(win.edit_charset_action.get_sensitive())
        win.file_view.expand_all()
        win.selection.select_path("0:0") #folder
        self.assertFalse(win.edit_charset_action.get_sensitive())
        win.selection.select_path("0:2") #file
        self.assertTrue(win.edit_charset_action.get_sensitive())        
        model = win.fm.store
        self.assertEqual("ISO-8859-1", model.get_value(model.get_iter("0:2"), 5))
        win.edit_charset_action.activate()
        self.assertEqual("UTF-8", model.get_value(model.get_iter("0:2"), 5))
    
    def test_select_destination(self):
        win = MainWindow()
        self.assertFalse(win.dst_chooser.get_sensitive())
        win.dst_cmb.set_active(1)
        self.assertTrue(win.dst_chooser.get_sensitive())
        
    def test_convert(self):
        global charset, copy_to
        win = MainWindow()
        self.assertFalse(win.convert_action.get_sensitive())
        win.add_action.activate()
        self.assertTrue(win.convert_action.get_sensitive())
        win.convert_action.activate()
        self.assertEqual("UTF-8", charset)
        self.assertIsNone(copy_to)
        win.dst_cmb.set_active(1)
        win.charset_cmb.set_active(win.charset_cmb.get_active() + 1)
        win.convert_action.activate()
        self.assertNotEqual("UTF-8", charset)
        self.assertIsNotNone(copy_to)
        