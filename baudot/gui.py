#!/usr/bin/python
# -*- coding: UTF-8 -*-

import os
import logging
import tempfile
from threading import Thread

import gtk
import gio
import gobject
from path import path
from pkg_resources import ResourceManager

from core import CharsetConverter

# globals
VERSION = "0.1"
logging.basicConfig()
LOG = logging.getLogger("baudot_gui")
LOG.setLevel(logging.DEBUG)
CONVERTER = CharsetConverter()
GLADE_PATH = path(ResourceManager().resource_filename("baudot.gui", "glade"))

gobject.threads_init()

class App(object):

    def __init__(self):
        self.win = MainWindow()

    def start(self):
        self.win.show()
        gtk.main()


class MainWindow(object):

    def __init__(self, testing=False):
        self._testing = testing
        builder = gtk.Builder()
        builder.add_from_file(GLADE_PATH / "window.glade")
        self.win = builder.get_object("window")
        self.win_box = builder.get_object("winVBox")
        self.dst_cmb = builder.get_object("dstCmb")
        self.dst_chooser = builder.get_object("dstFileChooser")
        self.add_action = builder.get_object("addAction")
        self.remove_action = builder.get_object("removeAction")
        self.remove_all_action = builder.get_object("removeAllAction")
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

        combo_from_strings(CONVERTER.get_encodings(),
                           self.charset_cmb, "UTF-8")

    def show(self):
        self.win.set_visible(True)
        self.win.show()

    def on_row_inserted(self, model, path, data=None):
        enabled = len(model) > 0
        self.convert_action.set_sensitive(enabled)
        self.remove_all_action.set_sensitive(enabled)

    def on_row_deleted(self, model, path, data=None):
        enabled = len(model) > 0
        self.convert_action.set_sensitive(enabled)
        self.remove_all_action.set_sensitive(enabled)

    def on_selection_changed(self, selection):
        (model, it) = self.selection.get_selected()
        if it is None:
            self.remove_action.set_sensitive(False)
            self.edit_charset_action.set_sensitive(False)
        else:
            self.remove_action.set_sensitive(True)
            entry = FileEntry.from_iter(model, it)
            self.edit_charset_action.set_sensitive(entry.filepath.isfile())

    def on_convertAction_activate(self, data=None):
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
            f = chooser.get_filename()
            chooser.destroy()
            #TODO: move this to a processing queue
            try:
                thread = Thread(target=lambda : self.fm.add(f))
                count = self.fm.count_files(f)
                class Namespace(object): pass
                ns = Namespace()
                ns.added = 0
                box = self._create_progress_box(f)
                def on_canceled(widget):
                    self.fm.stop()
                    self.win_box.remove(widget)
                box.connect("canceled", on_canceled)
                def on_file_added(widget, filepath):
                    ns.added += 1
                    progress = float(ns.added) * 100/ count
                    gobject.idle_add(box.update_progress, progress)
                    if progress == 100:
                        gobject.idle_add(self.win_box.remove, box)
                self.fm.connect("file-added", on_file_added)
                thread.start()
                if self._testing:
                    thread.join()                
            except DuplicatedFileException:
                gtk_error_msg(self.win, "File already in Baudot")
        else:
            chooser.destroy()

    def on_removeAction_activate(self, data=None):
        (model, it) = self.selection.get_selected()
        model.remove(it)

    def on_editCharsetAction_activate(self, data=None):
        (model, it) = self.selection.get_selected()
        entry = FileEntry.from_iter(model, it)
        dialog = CharsetChooser(entry.filepath, entry.charset)
        if dialog.run() == gtk.RESPONSE_APPLY:
            entry.charset = dialog.get_selected_charset()
            entry.save(model, it)
        dialog.destroy()

    def on_removeAllAction_activate(self, data=None):
        self.fm.clear()

    def on_aboutMenuItem_activate(self, widget, data=None):
        about = gtk.AboutDialog()
        about.set_program_name("Baudot")
        about.set_version(VERSION)
        about.set_copyright("© 2011 - Esteban Sancho")
        about.set_comments("Baudot is an easy to use tool for converting" +
                           " between charsets")
        about.set_website("http://github.com/drupal4media/baudot")
        about.run()
        about.destroy()

    def on_dstCmb_changed(self, widget, data=None):
        self.dst_chooser.set_sensitive(widget.get_active() == 1)

    def on_quitMenuItem_activate(self, widget, data=None):
        gtk.main_quit()

    def on_window_destroy(self, widget, data=None):
        gtk.main_quit()

    def _create_progress_box(self, filepath):
        progress_box = ProgressBox()
        progress_box.set_message("Adding <b>%s</b>" % filepath)
        self.win_box.pack_start(progress_box, False)
        self.win_box.reorder_child(progress_box, 3)
        return progress_box
        

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

    def save(self, model, it):
        model.set_value(it, 0, self.filepath)
        model.set_value(it, 1, self.icon)
        model.set_value(it, 2, self.filename)
        model.set_value(it, 3, self.size)
        model.set_value(it, 4, self.description)
        model.set_value(it, 5, self.charset)

    @staticmethod
    def from_row(row):
        filepath, icon, filename, size, description, charset = row
        return FileEntry(filepath, icon, filename, size, description, charset)

    @staticmethod
    def from_iter(model, it):
        row = list()
        for i in range(model.get_n_columns()):
            row.append(model.get_value(it, i))
        return FileEntry.from_row(row)


class FileManager(gobject.GObject):

    __gsignals__ = {
        'file-added': (gobject.SIGNAL_RUN_LAST, 
                           gobject.TYPE_NONE, 
                           (gobject.TYPE_STRING, )),
    }

    def __init__(self):
        gobject.GObject.__init__(self)
        # path, icon, filename, size, description, charset
        self.store = gtk.TreeStore(gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING)
        self._stop = False

    def stop(self):
        self._stop = True
        
    def __len__(self):
        return len(self.store)

    def clear(self):
        self.store.clear()

    def iter_remove(self, it):
        return self.store.remove(it)

    def search(self, filepath):
        filepath = path(filepath)

        def search(rows, filepath):
            if not rows:
                return None
            for row in rows:
                entry = FileEntry.from_row(row)
                if entry.filepath == filepath:
                    return row
                if filepath.startswith(entry.filepath):
                    result = search(row.iterchildren(), filepath)
                    if result:
                        return result
            return None
        return search(self.store, filepath)

    def convert_files(self, dst_charset, copy_to=None, callback=None):
        self._stop = False
        if copy_to:
            copy_to = path(copy_to)

        def convert(rows, base_path):
            if not rows:
                return
            for row in rows:
                entry = FileEntry.from_row(row)
                src_file = dst_file = entry.filepath
                if src_file.isfile():
                    src_charset = entry.charset
                    if copy_to:
                        if not base_path:
                            base_path = src_file.dirname()
                        dst_file = copy_to / src_file[len(base_path) + 1:]
                    if dst_file.exists():
                        self._create_backup(dst_file)
                    fd, filename = tempfile.mkstemp(prefix="baudot")
                    os.close(fd)
                    tmp_file = path(filename)
                    LOG.debug("Saving file %s with charset %s" %
                              (tmp_file, dst_charset))
                    CONVERTER.convert_encoding(src_file,
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
                            dst_file = copy_to / src_file[len(base_path) + 1:]
                            dst_file.makedirs()
                    convert(children, base_path)
        convert(self.store, None)

    def add(self, filepath, parent=None):
        filepath = path(filepath)
        if parent is None:
            self._stop = False
            if self.search(filepath):
                raise DuplicatedFileException()
        
        if self._stop:
            return

        filename = filepath if parent is None else filepath.basename()
        if filepath.isdir():
            entry = FileEntry(filepath, gtk.STOCK_DIRECTORY, 
                              filename, 0, "Folder")
            it = self.store.append(parent, entry.to_list())
            for d in filepath.dirs():
                self.add(d, it)
            for f in filepath.files():
                self.add(f, it)
            # remove empty or set size
            count = self.store.iter_n_children(it)
            if count > 0 or parent is None:
                entry.size = "%d items" % count
                entry.save(self.store, it)
            else:
                self.iter_remove(it)
        else:
            mime = self._get_mime_type(filepath)
            # only allow text files
            if "text" in mime.lower():
                match = CONVERTER.detect_encoding(filepath)
                #TODO: check detection confidence
                charset = match.charset if match else None
                if filepath.size < 1000:
                    size = "%d B" % filepath.size
                elif filepath.size < 1000000:
                    size = "%.2f KB" % (filepath.size / 1000.0)
                else:
                    size = "%.2f MB" % (filepath.size / 1000000.0)
                entry = FileEntry(filepath, gtk.STOCK_FILE, filename, size,
                                  mime, charset)
                self.store.append(parent, entry.to_list())
        self.emit("file-added", filepath)

    def count_files(self, filepath):
        filepath = path(filepath)
        count = 1
        if filepath.isdir():
            for f in filepath.walk():
                count += 1
        return count

    def _create_backup(self, filepath):
        filepath.copy2(filepath + "~")

    def _normalize(self, filepath):
        # TODO: remove if not used anymore
        filepath = path(filepath)
        if filepath.isdir():
            filepath = filepath.normpath() + '/'
        return filepath

    def _get_mime_type(self, filepath):
        info = gio.File(filepath).query_info("standard::content-type")
        return info.get_content_type()


class FileDirChooser(gtk.Dialog):

    def __init__(self, parent=None):
        super(FileDirChooser, self).__init__(parent=parent)
        self.set_title("Select file or folder...")
        self.set_modal(True)
        self.set_default_size(800, 600)
        self.cancel_btn = gtk.Button(stock=gtk.STOCK_CANCEL)
        self.add_action_widget(self.cancel_btn, gtk.RESPONSE_CANCEL)
        self.ok_btn = gtk.Button(stock=gtk.STOCK_OK)
        self.ok_btn.set_sensitive(False)
        self.add_action_widget(self.ok_btn, gtk.RESPONSE_OK)
        
        self.fc = gtk.FileChooserWidget()
        self.fc.set_select_multiple(True)
        self.fc.set_show_hidden(True)
        self.fc.connect("selection-changed", self.on_selection_changed)
        self.fc.connect("current-folder-changed", self.on_current_folder_changed)
        self.vbox.pack_start(self.fc, True, True)

        default_filter = gtk.FileFilter()
        default_filter.set_name("Text files")
        default_filter.add_mime_type("text/*")
        self.fc.add_filter(default_filter)
        
        all_filter = gtk.FileFilter()
        all_filter.set_name("All files")
        all_filter.add_pattern("*")
        self.fc.add_filter(all_filter)

        self.show_all()

    def on_current_folder_changed(self, filechooser):
        self.fc.unselect_all()
        
    def on_selection_changed(self, filechooser):
        self.ok_btn.set_sensitive(self.fc.get_filename() is not None)
        
    def get_filename(self):
        return self.fc.get_filename()


class ProgressBox(gtk.EventBox):
    __gsignals__ = {
        'canceled': (gobject.SIGNAL_RUN_LAST, gobject.TYPE_NONE, ()),
    }
    
    def __init__(self, is_open=True):
        super(ProgressBox, self).__init__()
        color = gtk.gdk.color_parse("#ffffc8")
        self.modify_bg(gtk.STATE_NORMAL, color)

        main_box = gtk.VBox()
        main_box.set_border_width(5)

        upper_box = gtk.HBox(spacing=5)
        icon = gtk.Image()
        stock = gtk.STOCK_OPEN if is_open else gtk.STOCK_CONVERT
        icon.set_from_stock(stock, gtk.ICON_SIZE_BUTTON)
        upper_box.pack_start(icon, False, False, 5)
        self.label = gtk.Label()
        self.label.set_use_markup(True)
        upper_box.pack_start(self.label, False)
        main_box.pack_start(upper_box, False)
        
        lower_box = gtk.HBox(spacing=5)
        alignment = gtk.Alignment(xalign=0.5, yalign=0.5, xscale=1, yscale=0.0)
        self.progress_bar = gtk.ProgressBar()
        alignment.add(self.progress_bar)
        lower_box.pack_start(alignment, expand=True, fill=True)
        cancel_btn = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancel_btn.connect("clicked", self.on_cancel_btn_clicked)
        lower_box.pack_start(cancel_btn, False)
        main_box.pack_start(lower_box, False)
        
        self.add(main_box)
        self.show_all()
    
    def on_cancel_btn_clicked(self, widget, data=None):
        self.emit("canceled")
    
    def set_message(self, message):
        self.label.set_markup(message)

    def update_progress(self, value):
        self.progress_bar.set_value(value)


# TODO: import only if available
from gtkcodebuffer import CodeBuffer, SyntaxLoader

class CharsetChooser(object):

    def __init__(self, filepath, charset):
        filepath = path(filepath)
        self.data = filepath.bytes()

        builder = gtk.Builder()
        builder.add_from_file(GLADE_PATH / "charset_chooser.glade")
        self.dialog = builder.get_object("chooser")
        self.dialog.set_title(filepath.basename())
        text_view = builder.get_object("textView")
        if str(filepath).endswith(".py"):
            #TODO: choose appropriate syntax
            lang = SyntaxLoader("python")
            self.text_buffer = CodeBuffer(lang=lang)
            text_view.set_buffer(self.text_buffer)
        else:
            self.text_buffer = text_view.get_buffer()
        self.charset_cmb = builder.get_object("encodingCmb")
        builder.connect_signals(self)

        combo_from_strings(self._get_charsets(self.data), 
                           self.charset_cmb, 
                           charset)
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
        except ValueError, e:
            gtk_error_msg(self.dialog, str(e))

    def _get_charsets(self, data):
        good = list()
        for charset in CONVERTER.get_encodings():
            try:
                unicode(data, charset)
                good.append(charset)
            except (ValueError, LookupError):
                pass
        return good

class DuplicatedFileException(Exception):
    pass

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

