# -*- coding: UTF-8 -*-

VERSION = "0.1"

from icu import UnicodeString
import gobject
import logging

import magic
import gtk
import path

from core import FileEncoder

logging.basicConfig()
log = logging.getLogger("baudot_gui")
log.setLevel(logging.DEBUG)

#--------------------------------------------------------
# App class
#--------------------------------------------------------
class App(object):
    def __init__(self):
        self.win = MainWindow()

    def start(self):
        self.win.show()
        gtk.main()

#--------------------------------------------------------
# MainWindow class
#--------------------------------------------------------
class MainWindow(object):

    def __init__(self):
        self.encoder = FileEncoder()

        builder = gtk.Builder()
        builder.add_from_file("glade/window.glade")
        self.win = builder.get_object("window")
        self.dst_cmb = builder.get_object("dstCmb")
        self.dst_chooser = builder.get_object("dstFileChooser")
        self.remove_action = builder.get_object("removeAction")
        self.edit_charset_action = builder.get_object("editCharsetAction")
        self.convert_action = builder.get_object("convertAction")
        self.charset_cmb = builder.get_object("charsetCmb")
        builder.connect_signals(self)

        self.file_manager = FileManager(self.encoder)
        self.file_manager.connect("row_deleted", self.on_row_deleted)
        self.file_manager.connect("row_inserted", self.on_row_inserted)

        tree = builder.get_object("fileView")
        self.file_selection = tree.get_selection()
        self.file_selection.connect('changed', self.on_selection_changed)
        tree.set_model(self.file_manager)

        create_charset_model(self.charset_cmb, "UTF-8")

    def show(self):
        self.win.show()

    def on_row_inserted(self, model, path, data=None):
        if len(model) == 1:
            self.convert_action.set_sensitive(True)

    def on_row_deleted(self, model, path, data=None):
        if len(model) == 0:        
            self.convert_action.set_sensitive(False)

    def on_selection_changed(self, selection):
        (model, iter) = self.file_selection.get_selected()
        if iter is None:
            self.remove_action.set_sensitive(False)
        else:
            self.remove_action.set_sensitive(True)
            file = path.path(model.get_value(iter, 0))
            self.edit_charset_action.set_sensitive(path.isfile())

    def on_convertAction_activate(self, date=None):
        #TODO: show progress dialog
        model = self.charset_cmb.get_model()
        (dst_charset,) = model.get(self.charset_cmb.get_active_iter(), 0)
        copy = self.dst_cmb.get_active() == 1
        copy_to = self.dst_chooser.get_filename() if copy else None
        self.file_manager.convert_files(dst_charset, copy_to)
        #TODO: update files in view

    def on_addAction_activate(self, data=None):
        chooser = FileDirChooser()
        if chooser.run() == gtk.RESPONSE_OK:
            file = path.path(chooser.get_selection())
            chooser.destroy()
            #TODO: show progress
            self.file_manager.add_file(file)
        else:
            chooser.destroy()

    def on_removeAction_activate(self, data=None):
        (model, iter) = self.file_selection.get_selected()
        model.remove(iter)

    def on_editCharsetAction_activate(self, data=None):
        (model, iter) = self.file_selection.get_selected()
        path, charset = model.get(iter, 0, 5)
        dialog = CharsetChooser(path, charset)
        if dialog.run() == gtk.RESPONSE_APPLY:
            charset = dialog.get_selected_charset()
            model.set_value(iter, 5, charset)
        dialog.destroy()

    def on_removeAllAction_activate(self, data=None):
        self.file_manager.clear()

    def on_aboutMenuItem_activate(self, widget, data=None):
        about = gtk.AboutDialog()
        about.set_program_name("Baudot")
        about.set_version(VERSION)
        about.set_copyright("© 2011 - Esteban Sancho")
        about.set_comments("Baudot is an easy to use tool for converting between charsets")
        about.set_website("http://github.com/drupal4media/baudot")
        about.run()
        about.destroy()
    
    def on_dstCmb_changed(self, widget, data=None):
        self.dst_chooser.set_sensitive(widget.get_active() == 1)

    def on_quitMenuItem_activate(self, widget, data=None):
        gtk.main_quit()

    def on_window_destroy(self, widget, data=None):
        gtk.main_quit()


#--------------------------------------------------------
# FileManager class
#--------------------------------------------------------
class FileManager(gtk.TreeStore):

    def __init__(self, encoder):
        # path, icon, filename, size, description, charset
        super(FileManager, self).__init__(gobject.TYPE_STRING,
                                        gobject.TYPE_STRING,
                                        gobject.TYPE_STRING,
                                        gobject.TYPE_STRING,
                                        gobject.TYPE_STRING,
                                        gobject.TYPE_STRING)
        self.encoder = encoder
    
    def search(self, file):
        file = path.path(file)
        def search(rows, path):
            if not rows: return None
            for row in rows:
                if row[0] == path:
                    return row
                if path.startswith(row[0]):
                    result = search(row.iterchildren(), path)
                    if result: return result
            return None
        return search(self, file)

    def convert_files(self, dst_charset, copy_to=None, callback=None):
        if copy_to: copy_to = path.path(copy_to)
        
        def convert(rows, base_path):
            if not rows: return
            for row in rows:
                src_file = dst_file = path.path(row[0])
                if src_file.isfile():
                    src_charset = row[5]
                    if copy_to:
                        if not base_path: base_path = src_file.dirname()
                        dst_file = copy_to / src_file[len(base_path)+1:]
                    else:
                        self._create_backup(src_file)
                    log.debug("Saving file %s with charset %s" % 
                              (dst_file, dst_charset))
                    self.encoder.convert_encoding(src_file, 
                                                  dst_file, 
                                                  src_charset, 
                                                  dst_charset)
                else: # isdir
                    children = row.iterchildren()
                    if copy_to:
                        if not base_path: 
                            base_path = src_file
                        else:
                            dst_file = copy_to / src_file[len(base_path)+1:]
                            dst_file.makedirs()
                    convert(children, base_path)
        convert(self, None)

    def add_file(self, file, parent=None):
        file = path.path(file)
        if parent is None and self.search(file):
            raise DuplicatedFileException()
        
        filename = file if parent is None else file.basename()
        if file.isdir():
            row = (file, "folder", filename, 0, "Folder", None)
            it = self.append(parent, row)
            for d in file.walkdirs():
                self.add_file(d, it)
            for f in file.walkfiles():
                self.add_file(f, it)
            # remove empty or set size
            size = self.iter_n_children(it)
            if size > 0 or parent is None:
                self.set_value(it, 3, "%d items" % size)
            else:
                self.remove(it)
        else:
            filetype = self._get_filetype(file)
            # only allow text files
            if "text" in filetype.lower():
                charset = self.encoder.detect_encoding(file)
                if file.size < 1000:
                    size = "%d B" % file.size
                elif file.size < 1000000:
                    size = "%.2f KB" % (file.size / 1000.0)
                else:
                    size = "%.2f MB" % (file.size / 1000000.0)
                row = (file, "text-x-script", filename, size, filetype, charset)
                self.append(parent, row)

    def _normalize(self, file):
        # TODO: remove if not used anymore
        file = path.path(file)
        if file.isdir():
            file = file.normpath() + '/'
        return file
    
    def _get_filetype(self, path):
        ms = magic.open(magic.MAGIC_NONE)
        ms.load()
        type = ms.file(path)
        ms.close()
        return type
        
class DuplicatedFileException(Exception):
    pass

#--------------------------------------------------------
# FileDirChooser class
#--------------------------------------------------------
class FileDirChooser(object):

    def __init__(self):
        self.selection = None
        #TODO: create file OR folder single dialog
        self.dialog = gtk.FileChooserDialog(title="Choose file ..",
                                        action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                        buttons=(gtk.STOCK_CANCEL,
                                                gtk.RESPONSE_CANCEL,
                                                gtk.STOCK_OPEN,
                                                gtk.RESPONSE_OK))
        self.dialog.set_default_response(gtk.RESPONSE_OK)
        self.dialog.set_select_multiple(True)

        #TODO: add correct filters
        #filter = gtk.FileFilter()
        #filter.set_name("Folders and text files")
        #filter.add_mime_type("text/*")
        #chooser.add_filter(filter)

    def run(self):
        response = self.dialog.run()
        if  response == gtk.RESPONSE_OK:
            self.selection = self.dialog.get_filenames()
        return response

    def get_selection(self):
        return self.selection

    def destroy(self):
        self.dialog.destroy()


#--------------------------------------------------------
# InProgressDialog class
#--------------------------------------------------------
class InProgressDialog(object):

    def run(self):
        pass

    def set_message(self, message):
        pass

    def update_progress(self, progress):
        pass

    def destroy(self):
        pass


#--------------------------------------------------------
# CharsetChooser class
#--------------------------------------------------------
class CharsetChooser(object):

    def __init__(self, file, charset):
        file = path.path(file)
        self.data = file.bytes()

        builder = gtk.Builder()
        builder.add_from_file("glade/encoding_chooser.glade")
        self.dialog = builder.get_object("chooser")
        self.dialog.set_title(file.basename())
        self.text_buffer = builder.get_object("textView").get_buffer()
        self.charset_cmb = builder.get_object("encodingCmb")
        builder.connect_signals(self)
        
        text = unicode(UnicodeString(self.data, charset))
        self.text_buffer.set_text(text)

        create_charset_model(self.charset_cmb, charset)

    def run(self):
        response = self.dialog.run()
        return gtk.RESPONSE_APPLY if response == 1 else gtk.RESPONSE_CLOSE

    def get_selected_charset(self):
        model = self.charset_cmb.get_model()
        (charset,) = model.get(self.charset_cmb.get_active_iter(), 0)
        return charset

    def on_encodingCmb_changed(self, widget, data=None):
        charset = self.get_selected_charset()
        try:
            text = unicode(UnicodeString(self.data, charset))
            self.text_buffer.set_text(text)
        except Exception as e:
            gtk_error_msg(None, str(e))
    
    def destroy(self):
        self.dialog.destroy()


#--------------------------------------------------------
# HELPER FUNCTIONS
#--------------------------------------------------------
def gtk_error_msg(parent, message):
    md = gtk.MessageDialog(parent, 
                           gtk.DIALOG_DESTROY_WITH_PARENT, 
                           gtk.MESSAGE_ERROR, 
                           gtk.BUTTONS_CLOSE, 
                           message)
    md.set_title("Error")
    md.run()
    md.destroy()
    
def create_charset_model(combo, default=None):
    '''Helper function to create charset combos
    '''
    encoder = FileEncoder()
    charsets = encoder.get_available_encodings()
    store = gtk.ListStore(gobject.TYPE_STRING)
    index = -1
    for i in range(len(charsets)):
        store.append((charsets[i],))
        if index < 0 and charsets[i] == default:
            index = i
    cell = gtk.CellRendererText()
    combo.pack_start(cell, True)
    combo.add_attribute(cell, 'text', 0)
    combo.set_model(store)
    combo.set_active(index)
    

#--------------------------------------------------------
# MAIN
#--------------------------------------------------------
if __name__ == "__main__":
    app = App()
    app.start()
