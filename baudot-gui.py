import sys
import gtk
	
class BaudotGUI(object):

    def on_addBtn_clicked(self, widget, data=None):
        chooser = gtk.FileChooserDialog(title="Choose file ..",
                                        action=gtk.FILE_CHOOSER_ACTION_OPEN,
                                        buttons=(gtk.STOCK_CANCEL,gtk.RESPONSE_CANCEL,gtk.STOCK_OPEN,gtk.RESPONSE_OK))
        chooser.set_default_response(gtk.RESPONSE_OK)
        chooser.set_select_multiple(True)

        filter = gtk.FileFilter()
        filter.set_name("Folders and text files")
        filter.add_mime_type("text/*")
        chooser.add_filter(filter)
        
        if chooser.run() == gtk.RESPONSE_OK:
            for file in chooser.get_filenames():
                self.file_store.append(None, (file, "4.3 KB", "Text File", "ISO-8859-1", "text-x-script"))
        chooser.destroy()
        
    def on_addMenuItem_activate(self, widget, data=None):
        self.on_addBtn_clicked(widget, data)
        
    def on_window_destroy(self, widget, data=None):
        gtk.main_quit()

    def on_destinationCombo_changed(self, widget, data=None):
        self.dst_chooser.set_sensitive(widget.get_active() == 1)
     
    def __init__(self):
        builder = gtk.Builder()
        builder.add_from_file("gui/baudot.glade") 
        builder.connect_signals(self)
        
        self.window = builder.get_object("window")
        self.dst_chooser = builder.get_object("dstFileChooser")
        self.file_store = builder.get_object("fileStore")

        
class FileEntry(object):

    def __init__(self, is_dir, path, size, desc, charset):
        self.is_dir = is_dir
        self.path = path
        self.size = size
        self.desc = desc
        self.charset = charset

    def to_list(self):
        return (self.path, self.size, self.desc, self.charset)

    
if __name__ == "__main__":
    baudot = BaudotGUI()
    baudot.window.show()
    gtk.main()
