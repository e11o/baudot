import gtk

class FileFolderChooser(gtk.Dialog):

    def __init__(self, parent=None):
        super(FileFolderChooser, self).__init__(parent=parent)
        self.set_title("Select file or folder...")
        self.set_modal(True)
        self.set_default_size(800, 600)
        self.cancel_btn = gtk.Button(stock=gtk.STOCK_CANCEL)
        self.add_action_widget(self.cancel_btn, gtk.RESPONSE_CANCEL)
        self.ok_btn = gtk.Button(stock=gtk.STOCK_ADD)
        self.add_action_widget(self.ok_btn, gtk.RESPONSE_OK)
        
        self.chooser = gtk.FileChooserWidget()
        self.chooser.set_select_multiple(True)
        self.chooser.set_show_hidden(True)
        self.chooser.connect("selection-changed", 
                             self.on_selection_changed)
        self.chooser.connect("current-folder-changed",
                             self.on_current_folder_changed)
        self.chooser.connect("file-activated",
                             self.on_file_activated)
        self.vbox.pack_start(self.chooser, True, True)

        default_filter = gtk.FileFilter()
        default_filter.set_name("Text files")
        default_filter.add_mime_type("text/*")
        self.chooser.add_filter(default_filter)
        
        all_filter = gtk.FileFilter()
        all_filter.set_name("All files")
        all_filter.add_pattern("*")
        self.chooser.add_filter(all_filter)
        
        self.show_all()

    def on_file_activated(self, chooser):
        print "Activado!!!!!"

    def on_current_folder_changed(self, chooser):
        chooser.unselect_all()
                       
    def on_selection_changed(self, chooser):
        pass
        #self.ok_btn.set_sensitive(chooser.get_filename() is not None)
        
    def get_filenames(self):
        return self.chooser.get_filenames()


