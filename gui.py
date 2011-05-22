import sys
import os.path
import gtk
import logging
from functools import partial
import threading

import magic

from core import FileEncoder

logging.basicConfig()

log = logging.getLogger("baudot_gui")
log.setLevel(logging.INFO)

TYPE_FOLDER = "Folder"

class BaudotGUI(object):

    def on_addBtn_clicked(self, widget, data=None):
        chooser = gtk.FileChooserDialog(title="Choose file ..",
                                        action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                        buttons=(gtk.STOCK_CANCEL,
                                                gtk.RESPONSE_CANCEL,
                                                gtk.STOCK_OPEN,
                                                gtk.RESPONSE_OK))
        chooser.set_default_response(gtk.RESPONSE_OK)
        chooser.set_select_multiple(True)

        filter = gtk.FileFilter()
        filter.set_name("Folders and text files")
        filter.add_mime_type("text/*")
        #chooser.add_filter(filter)

        if chooser.run() == gtk.RESPONSE_OK:
            files = []
            filenames = chooser.get_filenames()
            chooser.destroy()
            self.in_progress = 0
            self.completed = 0
            for path in filenames:
                entry = FileEntry.from_path(path)
                self.in_progress += entry.tree_count
                files.append(entry)
            thread = threading.Thread(target=partial(self.process_files, files))
            thread.start()
            self.add_files_msg.set_label("Processing files...")
            self.update_add_progress()
            self.add_files_dlg.show()
            thread.join()
            self.files.append(files)

    def update_add_progress(self):
        log.info("Updating progress bar: completed=%d in_progress=%d" % (self.completed, self.in_progress))
        self.add_files_progress.set_fraction(self.completed / self.in_progress)
        if (self.completed == self.in_progress):
            self.add_files_dlg.destroy()

    def process_files(self, files):
        for file in files:
            self.add_tree_entry(None, file)

    def add_tree_entry(self, parent, file):
        path = file.path if parent is None else file.filename
        mime = file.type
        size = charset = mime = icon = None
        if file.type == TYPE_FOLDER:
            size = "%d items" % file.size
            icon = "folder"
        else:
            charset = self.encoder.detect_encoding(file.path)
            if file.size < 1000:
                size = "%d B" % 1000
            elif file.size < 1000000:
                size = "%.2f KB" % (file.size / 1000)
            else:
                size = "%.2f MB" % (file.size / 1000000)
            icon = "text-x-script"
        p = self.file_store.append(parent,(path, size, mime, charset, icon))
        self.completed += 1
        self.update_add_progress()
        for child in sorted(file.children):
            self.add_tree_entry(p, child)

    def on_addMenuItem_activate(self, widget, data=None):
        self.on_addBtn_clicked(widget, data)

    def on_window_destroy(self, widget, data=None):
        gtk.main_quit()

    def on_destinationCombo_changed(self, widget, data=None):
        self.dst_chooser.set_sensitive(widget.get_active() == 1)

    def __init__(self):
        self.files = []
        self.encoder = FileEncoder()

        builder = gtk.Builder()
        builder.add_from_file("gui/baudot.glade")
        builder.connect_signals(self)

        self.window = builder.get_object("window")
        self.dst_chooser = builder.get_object("dstFileChooser")
        self.file_store = builder.get_object("fileStore")
        self.add_files_dlg = builder.get_object("addFilesDialog")
        self.add_files_msg = builder.get_object("addFilesMessageLbl")
        self.add_files_progress = builder.get_object("addFilesProgressBar")

class FileEntry(object):

    def __init__(self, path, type, children=(), tree_count=0):
        self.path = path
        self.filename = os.path.basename(path)
        self.type = type
        self.tree_count = tree_count
        self.children = children
        info = os.stat(path)
        self.size = len(children) if self.type == TYPE_FOLDER else info.st_size

    @staticmethod
    def from_path(path=None):
        log.debug("Creating entry for path: %s" % path)
        if os.path.isdir(path):
            children = []
            tree_count = 0
            for f in os.listdir(path):
                entry = FileEntry.from_path(os.path.join(path, f))
                if not entry is None:
                    children.append(entry)
                    tree_count += entry.tree_count
            if len(children) > 0:
                return FileEntry(path, TYPE_FOLDER, children, len(children) + tree_count)
        else:
            ms = magic.open(magic.MAGIC_NONE)
            ms.load()
            type = ms.file(path)
            ms.close()
            log.debug("%s is of type %s" % (path, type))
            # only allow text files
            if "text" in type.lower():
                return FileEntry(path, type)

    def __cmp__(self, other):
        if self.type == TYPE_FOLDER:
            if other.type == TYPE_FOLDER:
                return cmp(self.filename, other.filename)
            return -1
        else:
            if other.type == TYPE_FOLDER:
                return 1
            return cmp(self.filename, other.filename)

if __name__ == "__main__":
    baudot = BaudotGUI()
    baudot.window.show()
    gtk.main()
