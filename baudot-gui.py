import sys
import gtk
	
class BaudotGUI:

    def on_window_destroy(self, widget, data=None):
        gtk.main_quit()

    def on_destinationCombo_changed(self, widget, data=None):
        self.destinationChooser.set_sensitive(widget.get_active() == 1)
     
    def __init__(self):
        builder = gtk.Builder()
        builder.add_from_file("gui/baudot.glade") 
        
        self.window = builder.get_object("window")
        builder.connect_signals(self)

        self.destinationChooser = builder.get_object("destinationFileChooser")

        # create tree for displaying files and folders
        self.filesTreeStore = gtk.TreeStore(str, str, str, str)
        filesTree = builder.get_object("fileView")
        filesTree.set_model(self.filesTreeStore)
        filesColumn = self.create_column("Files")
        sizeColumn = self.create_column("Size")
        descriptionColumn = self.create_column("Description")
        charsetColumn = self.create_column("Charset")
        filesTree.append_column(filesColumn)
        filesTree.append_column(sizeColumn)
        filesTree.append_column(descriptionColumn)
        filesTree.append_column(charsetColumn)
        
    def create_column(self, name):
        column = gtk.TreeViewColumn(name)
        cellRenderer = gtk.CellRendererText()
        column.pack_start(cellRenderer, True)
        return column
        
        
if __name__ == "__main__":
    baudot = BaudotGUI()
    baudot.window.show()
    gtk.main()
