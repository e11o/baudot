import os.path
import gtk
import gobject
import logging
from functools import partial
import threading

import magic

from core import FileEncoder

logging.basicConfig()

log = logging.getLogger("baudot_gui")
log.setLevel(logging.INFO)

TYPE_FOLDER = "Folder"

class App(object):
    def __init__(self):
        self.win = MainWindow()

    def start(self):
        self.win.show()
        gtk.main()

class MainWindow(object):

    def __init__(self):
        self.encoder = FileEncoder()
        self.file_manager = FileManager(self.encoder)
        builder = gtk.Builder()
        builder.add_from_file("glade/window.glade")
        builder.connect_signals(self)
        self.win = builder.get_object("window")
        self.dst_chooser = builder.get_object("dstFileChooser")

        # TODO: review is this is the best approach
        tree = builder.get_object("fileView")
        tree.set_model(self.file_manager)

    def on_addBtn_clicked(self, widget, data=None):
        chooser = FileDirChooser()
        if chooser.run() == gtk.RESPONSE_OK:
            files = chooser.get_selection()
            chooser.close()
            #TODO: show "in progress" dialog
            for file in files:
                self.file_manager.add_file(file)
        else:
            chooser.close()

    def on_addMenuItem_activate(self, widget, data=None):
        self.on_addBtn_clicked(widget, data)

    def on_window_destroy(self, widget, data=None):
        gtk.main_quit()

    def on_dstCmb_changed(self, widget, data=None):
        self.dst_chooser.set_sensitive(widget.get_active() == 1)

    def show(self):
        self.win.show()


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

    def search(self, path):
        path = path.strip()
        def search(rows, path):
            if not rows: return None
            for row in rows:
                if row[0] == path:
                    return row
                if path.startswith(row[0]):
                    result = search(row.iterchildren(), path)
                    if result: return result
            return None
        return search(self, path)

    def add_file(self, path, parent=None):
        filename = path if parent is None else os.path.basename(path)
        if os.path.isdir(path):
            it = self.append(parent, (path, "folder", filename, 0, "Folder", None))

            # TODO: fix children order
            children = os.listdir(path)
            def folders_first(str):
                prefix = "0" if os.path.isdir(str) else "1"
                return prefix + str
            for child in sorted(children, key=folders_first):
                self.add_file(os.path.join(path, child), it)

            # remove empty or set size
            size = self.iter_n_children(it)
            if size > 0 or parent is None:
                self.set_value(it, 3, "%d items" % size)
            else:
                self.remove(it)
        else:
            ms = magic.open(magic.MAGIC_NONE)
            ms.load()
            type = ms.file(path)
            ms.close()
            # only allow text files
            if "text" in type.lower():
                charset = self.encoder.detect_encoding(path)
                info = os.stat(path)
                if info.st_size < 1000:
                    size = "%d B" % info.st_size
                elif info.st_size < 1000000:
                    size = "%.2f KB" % (info.st_size / 1000)
                else:
                    size = "%.2f MB" % (info.st_size / 1000000)
                self.append(parent, (path, "text-x-script", filename, size, type, charset))


class FileDirChooser(object):

    def __init__(self):
        self.selection = None
        #TODO: create file or folder single dialog
        self.dialog = gtk.FileChooserDialog(title="Choose file ..",
                                        action=gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER,
                                        buttons=(gtk.STOCK_CANCEL,
                                                gtk.RESPONSE_CANCEL,
                                                gtk.STOCK_OPEN,
                                                gtk.RESPONSE_OK))
        self.dialog.set_default_response(gtk.RESPONSE_OK)
        self.dialog.set_select_multiple(True)

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

    def close(self):
        self.dialog.destroy()


class InProgressDialog(object):

    def run(self):
        pass

    def set_message(self, message):
        pass

    def update_progress(self, progress):
        pass

    def close(self):
        pass


class EncodingChooser(object):

    def run(self):
        pass

    def get_selected_encoding(self):
        pass

    def close(self):
        pass


if __name__ == "__main__":
    app = App()
    app.start()
