#!/usr/bin/env python

import pygtk
pygtk.require('2.0')
import gtk

class Baudot:
    
    def create_column(self, name):
        column = gtk.TreeViewColumn(name)
        cellRenderer = gtk.CellRendererText()
        column.pack_start(cellRenderer, True)
        return column
        
    def __init__(self):
        window = gtk.Window(gtk.WINDOW_TOPLEVEL)
        window.set_title("Baudot")
        window.set_size_request(800, 600)
        window.connect("delete_event", lambda w,e: gtk.main_quit())
        
        # create main panel
        mainPanel = gtk.VPaned()
        window.add(mainPanel)
        mainPanel.show()

        # create tree for displaying files and folders
        filesTreeStore = gtk.TreeStore(str, str, str, str)
        filesTree = gtk.TreeView(filesTreeStore)
        self.filesColumn = self.create_column("Files")
        self.sizeColumn = self.create_column("Size")
        self.descriptionColumn = self.create_column("Description")
        self.charsetColumn = self.create_column("Charset")
        filesTree.append_column(self.filesColumn)
        filesTree.append_column(self.sizeColumn)
        filesTree.append_column(self.descriptionColumn)
        filesTree.append_column(self.charsetColumn)

        # add tree to main panel
        mainPanel.add1(filesTree)
        filesTree.show()

        # finally show the window
        window.show()

    def main(self):
        gtk.main()
        
if __name__ == "__main__":
    app = Baudot()
    app.main()
