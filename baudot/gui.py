#!/usr/bin/python
# -*- coding: UTF-8 -*-

VERSION = "0.1"

import logging
import tempfile

import gobject
import gtk
import magic
from path import path
from pkg_resources import resource_filename

from core import CharsetConverter

logging.basicConfig()
log = logging.getLogger("baudot_gui")
log.setLevel(logging.DEBUG)

converter = CharsetConverter()

glade_path = path(resource_filename("baudot.gui", "glade"))

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

        builder = gtk.Builder()
        builder.add_from_file(glade_path / "window.glade")
        self.win = builder.get_object("window")
        self.dst_cmb = builder.get_object("dstCmb")
        self.dst_chooser = builder.get_object("dstFileChooser")
        self.add_action = builder.get_object("addAction")
        self.remove_action = builder.get_object("removeAction")
        self.edit_charset_action = builder.get_object("editCharsetAction")
        self.convert_action = builder.get_object("convertAction")
        self.charset_cmb = builder.get_object("charsetCmb")
        self.file_view = builder.get_object("fileView")
        builder.connect_signals(self)

        self.fm = FileManager()
        self.fm.store.connect("row_deleted", self.on_row_deleted)
        self.fm.store.connect("row_inserted", self.on_row_inserted)

        self.selection = self.file_view.get_selection()
        self.selection.connect('changed', self.on_selection_changed)
        self.file_view.set_model(self.fm.store)

        combo_from_strings(converter.get_encodings(), self.charset_cmb, "UTF-8")

    def show(self):
        self.win.set_visible(True)
        self.win.show()

    def on_row_inserted(self, model, path, data=None):
        if len(model) == 1:
            self.convert_action.set_sensitive(True)

    def on_row_deleted(self, model, path, data=None):
        if len(model) == 0:        
            self.convert_action.set_sensitive(False)

    def on_selection_changed(self, selection):
        (model, iter) = self.selection.get_selected()
        if iter is None:
            self.remove_action.set_sensitive(False)
            self.edit_charset_action.set_sensitive(False)
        else:
            self.remove_action.set_sensitive(True)
            entry = FileEntry.from_iter(model, iter)
            self.edit_charset_action.set_sensitive(entry.filepath.isfile())

    def on_convertAction_activate(self, date=None):
        #TODO: show progress dialog
        dst_charset = self.charset_cmb.get_active_text()
        copy_to = None
        if self.dst_cmb.get_active() == 1:
            copy_to = self.dst_chooser.get_filename()
        self.fm.convert_files(dst_charset, copy_to)
        #TODO: update files in view

    def on_addAction_activate(self, data=None):
        chooser = FileDirChooser()
        if chooser.run() == gtk.RESPONSE_OK:
            file = chooser.get_selection()
            chooser.destroy()
            #TODO: show progress
            try:
                self.fm.add(file)
            except DuplicatedFileException as e:
                gtk_error_msg(self.win, "File already for processing... skipping")
        else:
            chooser.destroy()

    def on_removeAction_activate(self, data=None):
        (model, iter) = self.selection.get_selected()
        model.remove(iter)

    def on_editCharsetAction_activate(self, data=None):
        (model, iter) = self.selection.get_selected()
        entry = FileEntry.from_iter(model, iter)
        dialog = CharsetChooser(entry.filepath, entry.charset)
        if dialog.run() == gtk.RESPONSE_APPLY:
            entry.charset = dialog.get_selected_charset()
            entry.save(model, iter)
        dialog.destroy()

    def on_removeAllAction_activate(self, data=None):
        self.fm.clear()

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
# FileEntry class
#--------------------------------------------------------
class FileEntry(object):
    
    def __init__(self, filepath=None, icon=None, filename=None, 
                 size=None, description=None, charset=None):
        self.filepath = path(filepath)
        self.icon = icon
        self.filename = filename
        self.size = size
        self.description = description
        self.charset = charset
    
    def to_list(self):
        return (self.filepath, self.icon, self.filename, self.size, 
                    self.description, self.charset)
    
    def save(self, model, iter):
        model.set_value(iter, 0, self.filepath)
        model.set_value(iter, 1, self.icon)
        model.set_value(iter, 2, self.filename)
        model.set_value(iter, 3, self.size)
        model.set_value(iter, 4, self.description)
        model.set_value(iter, 5, self.charset)
        
    @staticmethod
    def from_row(row):
        filepath, icon, filename, size, description, charset = row
        return FileEntry(filepath, icon, filename, size, description, charset)

    @staticmethod
    def from_iter(model, iter):
        row = list()
        for i in range(model.get_n_columns()):
            row.append(model.get_value(iter, i))
        return FileEntry.from_row(row)

    # TODO: remove if unused
    @staticmethod
    def get_column_defs():
        # path, icon, filename, size, description, charset
        return(gobject.TYPE_STRING,
               gobject.TYPE_STRING,
               gobject.TYPE_STRING,
               gobject.TYPE_STRING,
               gobject.TYPE_STRING,
               gobject.TYPE_STRING)
    
#--------------------------------------------------------
# FileManager class
#--------------------------------------------------------
class FileManager(object):

    def __init__(self):
        # path, icon, filename, size, description, charset
        self.store = gtk.TreeStore(gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING)
    def __len__(self):
        return len(self.store)
    
    def clear(self):
        self.store.clear()
        
    def iter_remove(self, iter):
        return self.store.remove(iter)
    
    def search(self, file):
        file = path(file)
        def search(rows, path):
            if not rows: return None
            for row in rows:
                entry = FileEntry.from_row(row)
                if entry.filepath == path:
                    return row
                if path.startswith(entry.filepath):
                    result = search(row.iterchildren(), path)
                    if result: return result
            return None
        return search(self.store, file)

    def convert_files(self, dst_charset, copy_to=None, callback=None):
        if copy_to: copy_to = path(copy_to)
        
        def convert(rows, base_path):
            if not rows: return
            for row in rows:
                entry = FileEntry.from_row(row)
                src_file = dst_file = entry.filepath
                if src_file.isfile():
                    src_charset = entry.charset
                    if copy_to:
                        if not base_path: base_path = src_file.dirname()
                        dst_file = copy_to / src_file[len(base_path)+1:]
                    if dst_file.exists():
                        self._create_backup(dst_file)
                    fd, filename = tempfile.mkstemp(prefix="baudot")
                    tmp_file = path(filename)
                    log.debug("Saving file %s with charset %s" % 
                              (tmp_file, dst_charset))
                    converter.convert_encoding(src_file, 
                                                  tmp_file, 
                                                  src_charset, 
                                                  dst_charset)
                    tmp_file.copyfile(dst_file)
                    tmp_file.remove()
                else: # isdir
                    children = row.iterchildren()
                    if copy_to:
                        if not base_path: 
                            base_path = src_file
                        else:
                            dst_file = copy_to / src_file[len(base_path)+1:]
                            dst_file.makedirs()
                    convert(children, base_path)
        convert(self.store, None)

    def add(self, file, parent=None):
        file = path(file)
        if parent is None and self.search(file):
            raise DuplicatedFileException()
        
        filename = file if parent is None else file.basename()
        if file.isdir():
            entry = FileEntry(file, "folder", filename, 0, "Folder")
            it = self.store.append(parent, entry.to_list())
            for d in file.dirs():
                self.add(d, it)
            for f in file.files():
                self.add(f, it)
            # remove empty or set size
            count = self.store.iter_n_children(it)
            if count > 0 or parent is None:
                entry.size = "%d items" % count
                entry.save(self.store, it)
            else:
                self.iter_remove(it)
        else:
            filetype = self._get_filetype(file)
            # only allow text files
            if "text" in filetype.lower():
                match = converter.detect_encoding(file)
                #TODO: check detection confidence
                charset = match.charset if match else None
                if file.size < 1000:
                    size = "%d B" % file.size
                elif file.size < 1000000:
                    size = "%.2f KB" % (file.size / 1000.0)
                else:
                    size = "%.2f MB" % (file.size / 1000000.0)
                entry = FileEntry(file, "text-x-script", filename, size, 
                                  filetype, charset)
                self.store.append(parent, entry.to_list())

    def _create_backup(self, file):
        file.copy2(file + "~")
    
    def _normalize(self, file):
        # TODO: remove if not used anymore
        file = path(file)
        if file.isdir():
            file = file.normpath() + '/'
        return file
    
    def _get_filetype(self, path):
        # TODO: improve recognition (missing UTF-8 files converted to ISO-8859-1)
        ms = magic.open(magic.MAGIC_NONE)
        ms.load()
        type = ms.file(path)
        ms.close()
        return type
        
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
            self.selection = self.dialog.get_filename()
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
# TODO: import only if available
from gtkcodebuffer import CodeBuffer, SyntaxLoader

class CharsetChooser(object):

    def __init__(self, file, charset):
        file = path(file)
        self.data = file.bytes()
        
        builder = gtk.Builder()
        builder.add_from_file(glade_path / "charset_chooser.glade")
        self.dialog = builder.get_object("chooser")
        self.dialog.set_title(file.basename())
        text_view = builder.get_object("textView")
        #TODO: choose appropriate syntax
        lang = SyntaxLoader("python")
        self.text_buffer = CodeBuffer(lang=lang)
        text_view.set_buffer(self.text_buffer)
        self.charset_cmb = builder.get_object("encodingCmb")
        builder.connect_signals(self)

        combo_from_strings(self._get_charsets(self.data), self.charset_cmb, charset)
        self.set_data(charset)

    def run(self):
        response = self.dialog.run()
        return gtk.RESPONSE_APPLY if response == 1 else gtk.RESPONSE_CLOSE

    def get_selected_charset(self):
        model = self.charset_cmb.get_model()
        return model.get_value(self.charset_cmb.get_active_iter(), 0)

    def on_encodingCmb_changed(self, widget, data=None):
        charset = self.get_selected_charset()
        self.set_data(charset)
    
    def destroy(self):
        self.dialog.destroy()

    def set_data(self, charset):
        try:
            text = unicode(self.data, charset)
            self.text_buffer.set_text(text)
        except Exception as e:
            gtk_error_msg(self.dialog, str(e))

    def _get_charsets(self, data):
        good = list()
        for charset in converter.get_encodings():
            try:
                unicode(data, charset)
                good.append(charset)
            except:
                pass
        return good

#--------------------------------------------------------
# EXCEPTIONS
#--------------------------------------------------------
class DuplicatedFileException(Exception):
    pass

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
    
def combo_from_strings(str_list, combo, default=None):
    '''Helper function to populate a combo with a list of strings
    '''
    store = gtk.ListStore(gobject.TYPE_STRING)
    index = -1
    for i in range(len(str_list)):
        store.append((str_list[i],))
        if index < 0 and str_list[i] == default:
            index = i
    cell = gtk.CellRendererText()
    combo.pack_start(cell, True)
    combo.add_attribute(cell, 'text', 0)
    combo.set_model(store)
    combo.set_active(index)
    
