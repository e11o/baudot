VERSION = "0.1"

from icu import UnicodeString
import os.path
import gobject
import logging

import magic
import gtk

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
            path = model.get_value(iter, 0)
            self.edit_charset_action.set_sensitive(os.path.isfile(path))

    def on_convertAction_activate(self, date=None):
        model = self.charset_cmb.get_model()
        (dst_charset,) = model.get(self.charset_cmb.get_active_iter(), 0)
        copy = self.dst_cmb.get_active() == 1
        copy_to = self.dst_chooser.get_filename() if copy else None
        self.file_manager.convert_files(dst_charset, copy_to)

    def on_addAction_activate(self, data=None):
        chooser = FileDirChooser()
        if chooser.run() == gtk.RESPONSE_OK:
            files = chooser.get_selection()
            chooser.destroy()
            #TODO: show "in progress" dialog
            for file in files:
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

    def convert_files(self, dst_charset, copy_to=None, callback=None):
        #FIXME: improve this code
        def convert(rows, base_path):
            if not rows: return
            for row in rows:
                src_file = dst_file = row[0]
                src_charset = row[5]
                children = row.iterchildren()
                if copy_to:
                    if not row.parent:
                        base_path = src_file if os.path.isdir(src_file) else os.path.basename(src_file)
                    dst_file = os.path.join(copy_to, src_file[len(base_path)+1:])
                if src_charset:
                    self.encoder.convert_encoding(src_file, dst_file, src_charset, dst_charset)
                log.debug("Saving file to: %s in charset: %s" % (dst_file, dst_charset))
                convert(children, base_path)
        convert(self, None)

    def add_file(self, path, parent=None):
        filename = path if parent is None else os.path.basename(path)

        if os.path.isdir(path):
            row = (path, "folder", filename, 0, "Folder", None)
            it = self.append(parent, row)

            # TODO: fix children order
            children = os.listdir(path)
            def folders_first(p):
                prefix = "0" if os.path.isdir(p) else "1"
                return prefix + p
            for child in sorted(children, key=folders_first):
                self.add_file(os.path.join(path, child), it)

            # remove empty or set size
            size = self.iter_n_children(it)
            if size > 0 or parent is None:
                self.set_value(it, 3, "%d items" % size)
            else:
                self.remove(it)
        else:
            filetype = self._get_filetype(path)
            # only allow text files
            if "text" in filetype.lower():
                charset = self.encoder.detect_encoding(path)
                info = os.stat(path)
                if info.st_size < 1000:
                    size = "%d B" % info.st_size
                elif info.st_size < 1000000:
                    size = "%.2f KB" % (info.st_size / 1000)
                else:
                    size = "%.2f MB" % (info.st_size / 1000000)
                row = (path, "text-x-script", filename, size, filetype, charset)
                self.append(parent, row)

    def _get_filetype(self, path):
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

    def __init__(self, path, charset):
        self.data = self._load_data(path)
        builder = gtk.Builder()
        builder.add_from_file("glade/encoding_chooser.glade")
        self.dialog = builder.get_object("chooser")
        self.dialog.set_title(os.path.basename(path))
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

    def _load_data(self, path):
        f = open(path, 'r')
        data = f.read()
        f.close()
        return data

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
