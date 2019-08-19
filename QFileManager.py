#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import os
from subprocess import Popen
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import QIcon
from PyQt5.Qt import QKeySequence, QCursor
import findFilesWindow
from zipfile import ZipFile
import shutil

class helpWindow(QMainWindow):
    def __init__(self):
        super(helpWindow, self).__init__()
        self.setStyleSheet(mystylesheet(myWindow()))
        self.helpText ="""<span>(see context menu)</strong></span></p><h3>Features:</h3>drag and drop Files to copy (SHIFT to move)<br>open Files with default app<br></span>
                                        </strong></span></p><h3>Shortcuts:</h3><br>
                                        rename File (F2)<br>
                                        copy File(s) (Ctrl-C)<br>
                                        paste File(s) (Ctrl-V)<br>
                                        cut File(s) (Ctrl-X)<br>
                                        open with TextEditor (F6)<br>
                                        cut File(s) (Del)<br>
                                        find File(s) (Ctrl-F)<br>
                                        play with vlc (F3)</strong></span></p>
                                        """
        self.helpViewer = QLabel(self.helpText, self)
        self.helpViewer.setAlignment(Qt.AlignCenter)
        self.btnAbout = QPushButton("about")
        self.btnAbout.setFixedWidth(66)
        self.btnAbout.setIcon(QIcon.fromTheme("help-about"))
        self.btnAbout.clicked.connect(self.aboutApp)

        widget = QWidget(self)
        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignCenter)

        layout.addWidget(self.helpViewer)
        layout.addStretch()
        layout.addWidget(self.btnAbout)
        self.setCentralWidget(widget)

        self.setWindowTitle("Help")
        self.setWindowIcon(QIcon.fromTheme("help-about"))
        self.setGeometry(0, 26, 600, 450)

    def aboutApp(self):
        sysinfo = QSysInfo()
        myMachine = "currentCPU Architecture: " + sysinfo.currentCpuArchitecture() + "<br>" + sysinfo.prettyProductName() + "<br>" + sysinfo.kernelType() + " " + sysinfo.kernelVersion()
        title = "about QFileManager"
        message = """
                    <span style='color: #3465a4; font-size: 20pt;font-weight: bold;text-align: center;'
                    ></span></p><center><h3>QFileManager<br>1.0 Beta</h3></center>created by  
                    <a title='Axel Schneider' href='http://goodoldsongs.jimdo.com' target='_blank'>Axel Schneider</a> with PyQt5<br><br>
                    <span style='color: #555753; font-size: 9pt;'>©2019 Axel Schneider<br><br></strong></span></p>
                        """ + myMachine
        self.infobox(title, message)

    def infobox(self,title, message):
        QMessageBox(QMessageBox.Information, title, message, QMessageBox.NoButton, self, Qt.Dialog|Qt.NoDropShadowWindowHint).show()  


class myWindow(QMainWindow):
    def __init__(self):
        super(myWindow, self).__init__()

        self.setStyleSheet(mystylesheet(self))
        self.setWindowTitle("Filemanager")
        self.setWindowIcon(QIcon.fromTheme("system- file-manager"))
        self.process = QProcess()

        self.settings = QSettings("QFileManager", "QFileManager")

        self.treeview = QTreeView()
        self.listview = QTreeView()

        self.cut = False
        self.hiddenEnabled = False

        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Horizontal)
        self.splitter.addWidget(self.treeview)
        self.splitter.addWidget(self.listview)

        hlay = QHBoxLayout()
        hlay.addWidget(self.splitter)

        wid = QWidget()
        wid.setLayout(hlay)
        self.createStatusBar()
        self.setCentralWidget(wid)
        self.setGeometry(0, 26, 900,500)

        path = QDir.rootPath()
        self.copyPath = ""
        self.copyList = []

        self.dirModel = QFileSystemModel()
        self.dirModel.setReadOnly(True)
        self.dirModel.setRootPath(QDir.rootPath())
        self.dirModel.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Drives)

        self.fileModel = QFileSystemModel()
        self.fileModel.setReadOnly(False)
        self.fileModel.setFilter(QDir.NoDotAndDotDot | QDir.Files)
        self.fileModel.setResolveSymlinks(True)

        self.treeview.setModel(self.dirModel)
        self.treeview.setTreePosition(-1)
        self.treeview.hideColumn(1)
        self.treeview.hideColumn(2)
        self.treeview.hideColumn(3)
        self.listview.setModel(self.fileModel)
        self.treeview.setRootIsDecorated(True)
#        self.listview.setSelectionBehavior (QAbstractItemView.SelectRows )
#        self.listview.customContextMenuRequested.connect(self.contextMenuEvent)
        self.listview.header().resizeSection(0, 320)
        self.listview.header().resizeSection(1, 80)
        self.listview.header().resizeSection(2, 80)

        self.createActions()

        self.treeview.setRootIndex(self.dirModel.index(path))

        self.treeview.clicked.connect(self.on_clicked)
        self.treeview.selectionModel().selectionChanged.connect(self.on_selectionChanged)
        self.listview.doubleClicked.connect(self.list_doubleClicked)

        docs = QStandardPaths.standardLocations(QStandardPaths.DocumentsLocation)[0]
        self.treeview.setCurrentIndex(self.dirModel.index(docs))
        self.treeview.expand(self.treeview.currentIndex())

        self.splitter.setSizes([20, 160])

        self.listview.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.listview.setDragDropMode(QAbstractItemView.DragDrop)
        self.listview.setDragEnabled(True)
        self.listview.setAcceptDrops(True)
        self.listview.setDropIndicatorShown(True)
        self.listview.setEditTriggers(QAbstractItemView.SelectedClicked)

        self.treeview.setDragDropMode(QAbstractItemView.DropOnly)
#        self.treeview.setDragEnabled(True)
        self.treeview.setAcceptDrops(True)
        self.treeview.setDropIndicatorShown(True)
        self.readSettings()

    def closeEvent(self, e):
        self.writeSettings()

    def readSettings(self):
        if self.settings.value("pos") != "":
            pos = self.settings.value("pos", QPoint(200, 200))
            self.move(pos)
        else:
            self.move(0, 26)
        if self.settings.value("size") != "":
            size = self.settings.value("size", QSize(400, 400))
            self.resize(size)
        else:
            self.resize(800, 600)

    def writeSettings(self):
        self.settings.setValue("pos", self.pos())
        self.settings.setValue("size", self.size())

    def enableHidden(self):
        print("toggle hidden files")
        if self.hiddenEnabled == False:
            self.fileModel.setFilter(QDir.NoDotAndDotDot | QDir.Hidden | QDir.Files)
            self.dirModel.setFilter(QDir.NoDotAndDotDot | QDir.Hidden | QDir.AllDirs)
            self.hiddenEnabled = True
            self.hiddenAction.setChecked(True)
        else:
            self.fileModel.setFilter(QDir.NoDotAndDotDot | QDir.Files)
            self.dirModel.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs)
            self.hiddenEnabled = False
            self.hiddenAction.setChecked(False)

    def openNewWin(self):
        index = self.treeview.selectionModel().currentIndex()
        path = self.dirModel.fileInfo(index).absoluteFilePath()
        theApp =  sys.argv[0]
        if QDir(path).exists:
            print("open '", path, "' in new window")
            self.process.startDetached("python3", [theApp, path])

    def createActions(self):
        self.openAction = QAction(QIcon.fromTheme("system-run"), "open File",  triggered=self.openFile)
        self.openAction.setShortcut(QKeySequence(Qt.Key_Return))
        self.openAction.setShortcutVisibleInContextMenu(True)
        self.listview.addAction(self.openAction) 

        self.newWinAction = QAction(QIcon.fromTheme("folder-open"), "open in new window",  triggered=self.openNewWin)
        self.newWinAction.setShortcut(QKeySequence("Shift+Ctrl+n"))
        self.newWinAction.setShortcutVisibleInContextMenu(True)
        self.listview.addAction(self.newWinAction) 

        self.openActionText = QAction(QIcon.fromTheme("system-run"), "open File with Texteditor",  triggered=self.openFileText)
        self.openActionText.setShortcut(QKeySequence(Qt.Key_F6))
        self.openActionText.setShortcutVisibleInContextMenu(True)
        self.listview.addAction(self.openActionText) 

        self.renameAction = QAction(QIcon.fromTheme("accessories-text-editor"), "rename File",  triggered=self.renameFile) 
        self.renameAction.setShortcut(QKeySequence(Qt.Key_F2))
        self.renameAction.setShortcutVisibleInContextMenu(True)
        self.listview.addAction(self.renameAction) 

        self.copyAction = QAction(QIcon.fromTheme("edit-copy"), "copy File(s)",  triggered=self.copyFile) 
        self.copyAction.setShortcut(QKeySequence("Ctrl+c"))
        self.copyAction.setShortcutVisibleInContextMenu(True)
        self.listview.addAction(self.copyAction) 

        self.cutAction = QAction(QIcon.fromTheme("edit-cut"), "cut File(s)",  triggered=self.cutFile) 
        self.cutAction.setShortcut(QKeySequence("Ctrl+x"))
        self.cutAction.setShortcutVisibleInContextMenu(True)
        self.listview.addAction(self.cutAction) 

        self.pasteAction = QAction(QIcon.fromTheme("edit-paste"), "paste File(s)",  triggered=self.pasteFile) 
        self.pasteAction.setShortcut(QKeySequence("Ctrl+v"))
        self.pasteAction.setShortcutVisibleInContextMenu(True)
        self.listview.addAction(self.pasteAction) 

        self.delAction = QAction(QIcon.fromTheme("edit-delete"), "delete File",  triggered=self.deleteFile)
        self.delAction.setShortcut(QKeySequence("Shift+Del"))
        self.delAction.setShortcutVisibleInContextMenu(True)
        self.listview.addAction(self.delAction) 

        self.delActionTrash = QAction(QIcon.fromTheme("user-trash"), "move to trash",  triggered=self.deleteFileTrash)
        self.delActionTrash.setShortcut(QKeySequence("Del"))
        self.delActionTrash.setShortcutVisibleInContextMenu(True)
        self.listview.addAction(self.delActionTrash) 

        self.findFilesAction = QAction(QIcon.fromTheme("edit-find"), "find in folder",  triggered=self.findFiles)
        self.findFilesAction.setShortcut(QKeySequence("Ctrl+f"))
        self.findFilesAction.setShortcutVisibleInContextMenu(True)
        self.treeview.addAction(self.findFilesAction) 

        self.zipAction = QAction(QIcon.fromTheme("zip"), "create zip from folder",  triggered=self.createZipFromFolder)
        self.treeview.addAction(self.zipAction) 

        self.zipFilesAction = QAction(QIcon.fromTheme("zip"), "create zip from selected files",  triggered=self.createZipFromFiles)
        self.listview.addAction(self.zipFilesAction) 

        self.playAction = QAction(QIcon.fromTheme("multimedia-player"), "play with Qt5Player",  triggered=self.playVLC)
        self.playAction.setShortcut(QKeySequence(Qt.Key_F3))
        self.playAction.setShortcutVisibleInContextMenu(True)
        self.listview.addAction(self.playAction) 

        self.playVLCAction = QAction(QIcon.fromTheme("vlc"), "play with vlc",  triggered=self.playMedia)
        self.listview.addAction(self.playVLCAction) 

        self.mp3Action = QAction(QIcon.fromTheme("audio-x-generic"), "convert to mp3",  triggered=self.makeMP3)
        self.listview.addAction(self.mp3Action) 

        self.playlistAction = QAction(QIcon.fromTheme("audio-x-generic"), "make playlist",  triggered=self.makePlaylist)
        self.listview.addAction(self.playlistAction)

        self.refreshAction = QAction(QIcon.fromTheme("view-refresh"), "refresh View",  triggered=self.refreshList)
        self.refreshAction.setShortcut(QKeySequence(Qt.Key_F5))
        self.refreshAction.setShortcutVisibleInContextMenu(True)
        self.listview.addAction(self.refreshAction) 

        self.hiddenAction = QAction("show hidden Files",  triggered=self.enableHidden)
        self.hiddenAction.setShortcut(QKeySequence("Ctrl+h"))
        self.hiddenAction.setCheckable(True)
        self.hiddenAction.setShortcutVisibleInContextMenu(True)
        self.listview.addAction(self.hiddenAction)

        self.helpAction = QAction(QIcon.fromTheme("help"), "Help",  triggered=self.showHelp)
        self.helpAction.setShortcut(QKeySequence(Qt.Key_F1))
        self.helpAction.setShortcutVisibleInContextMenu(True)
        self.listview.addAction(self.helpAction) 

    def createZipFromFolder(self):
        index = self.treeview.selectionModel().currentIndex()
        path = self.dirModel.fileInfo(index).filePath()
        fname = self.dirModel.fileInfo(index).fileName()
        print("folder to zip:", path)
        self.copyFile()
        target, _ = QFileDialog.getSaveFileName(self, "Save as... (do not add .zip)", path + "/" + fname,"zip files (*.zip)")
        if (target != ""):
            shutil.make_archive(target, 'zip', path)

    def createZipFromFiles(self):
        index = self.treeview.selectionModel().currentIndex()
        path = self.dirModel.fileInfo(index).filePath()
        fname = self.dirModel.fileInfo(index).fileName()
        print("folder to zip:", path)
        self.copyFile()
        target, _ = QFileDialog.getSaveFileName(self, "Save as...", path + "/" + "archive.zip","zip files (*.zip)")
        if (target != ""):
            zipText = ""
            with ZipFile(target, 'w') as myzip:
                for file in self.copyList:
                    fname = os.path.basename(file)
                    myzip.write(file, fname)

    def findFiles(self):
        index = self.treeview.selectionModel().currentIndex()
        path = self.dirModel.fileInfo(index).filePath()
        print("open findWindow")
        self.w = findFilesWindow.ListBox()
        self.w.show()
        self.w.folderEdit.setText(path)

    def refreshList(self):
        index = self.listview.selectionModel().currentIndex()
        path = self.fileModel.fileInfo(index).filePath()
        print("%s: %s" % ("current path", path))
        self.listview.setRootIndex(self.fileModel.setRootPath(path))
        self.treeview.setRootIndex(self.dirModel.setRootPath(path))


    def makeMP3(self):
        index = self.listview.selectionModel().currentIndex()
        path = self.fileModel.fileInfo(index).filePath()
        ext = self.fileModel.fileInfo(index).suffix()
        newpath = path.replace("." + ext, ".mp3")
        print(ext)
        self.statusBar().showMessage("%s '%s'" % ("converting:", path))
        self.process.startDetached("ffmpeg", ["-i", path, newpath])
        print("%s '%s'" % ("converting", path))

    def makePlaylist(self):
        index = self.treeview.selectionModel().currentIndex()
        foldername = self.dirModel.fileInfo(index).fileName()

        path = self.currentPath + "/" + foldername + ".m3u"
        self.process.execute("touch", [path])
        mp3List = []
        
        for name in os.listdir(self.currentPath):
            if os.path.isfile(os.path.join(self.currentPath, name)):
                if ".mp3" in name:
                    mp3List.append(self.currentPath + "/" + name)
        
        mp3List.sort(key=str.lower)
        print('\n'.join(mp3List))

        with open(path, 'w') as playlist:
            playlist.write('\n'.join(mp3List))
            playlist.close()

    def showHelp(self):
        self.w = helpWindow()
        self.w.show()

    def on_clicked(self, index):
        expand = not(self.treeview.isExpanded(index))
        self.treeview.setExpanded(index, expand)

    def getFolderSize(self, path):
        size = sum(os.path.getsize(f) for f in os.listdir(folder) if os.path.isfile(f))
        return size

    def on_selectionChanged(self):
        index = self.treeview.selectionModel().currentIndex()
        path = self.dirModel.fileInfo(index).absoluteFilePath()
#        self.statusBar().showMessage("%s %s" % ("selected folder:", path))
        self.listview.setRootIndex(self.fileModel.setRootPath(path))
        self.currentPath = path
        self.setWindowTitle(path)

    def openFile(self):
        index = self.listview.selectionModel().currentIndex()
        path = self.fileModel.fileInfo(index).absoluteFilePath()
        self.copyFile()
        for files in self.copyList:
            print("%s '%s'" % ("open file", files))
            self.process.startDetached("xdg-open",  [files])

    def openFileText(self):
        index = self.listview.selectionModel().currentIndex()
        path = self.fileModel.fileInfo(index).absoluteFilePath()
        theApp = "/home/brian/myApps/TextEdit/QTextEdit"
        if QFile.exists(theApp):
            self.copyFile()
            for files in self.copyList:
                print("%s '%s'" % ("open file", files))
                self.process.startDetached(theApp, [files])
        else:
            self.copyFile()
            for files in self.copyList:
                print("%s '%s'" % ("open file", files))
                self.process.startDetached("xdg-open", [files])

    def playVLC(self):
        index = self.listview.selectionModel().currentIndex()
        path = self.fileModel.fileInfo(index).filePath()
        self.statusBar().showMessage("%s '%s'" % ("file:", path))
        myapp = "/home/brian/Dokumente/Qt5Player.py"
        if QFile.exists(myapp):
            self.process.startDetached("python3", [myapp, path])
            print("%s '%s'" % ("playing", path))
        else:
            self.process.startDetached("cvlc", [path])
            print("%s '%s'" % ("playing with vlc:", path))

    def playMedia(self):
        index = self.listview.selectionModel().currentIndex()
        path = self.fileModel.fileInfo(index).filePath()
        self.statusBar().showMessage("%s '%s'" % ("file:", path))
        self.process.startDetached("cvlc", [path])
        print("%s '%s'" % ("playing with vlc:", path))

    def list_doubleClicked(self):
        index = self.listview.selectionModel().currentIndex()
        path = self.fileModel.fileInfo(index).absoluteFilePath()
        self.process.startDetached("xdg-open",  [path])

    def infobox(self, message):
        title = "QFilemager"
        QMessageBox(QMessageBox.Information, title, message, QMessageBox.NoButton, self, Qt.Dialog|Qt.NoDropShadowWindowHint).show()  

    def contextMenuEvent(self, event):
        index = self.listview.selectionModel().currentIndex()
        path = self.fileModel.fileInfo(index).absoluteFilePath()
        self.menu = QMenu(self.listview)
        if self.listview.hasFocus():
            self.menu.addAction(self.openAction)
            self.menu.addAction(self.openActionText)
            self.menu.addSeparator()
            if os.path.isdir(path):
                self.menu.addAction(self.newWinAction) 
            self.menu.addSeparator()
            self.menu.addAction(self.renameAction) 
            self.menu.addSeparator()
            self.menu.addAction(self.copyAction) 
            self.menu.addAction(self.cutAction) 
            self.menu.addAction(self.pasteAction) 
            self.menu.addSeparator()
            self.menu.addAction(self.delActionTrash) 
            self.menu.addAction(self.delAction) 
            self.menu.addSeparator()
            extensions = [".mp3", ".mp4", "mpg", ".m4a", ".mpeg", "avi", ".mkv", ".webm", ".wav", ".ogg", ".flv ", ".vob", ".ogv", ".ts", ".m2v", "m4v", "3gp", ".f4v"]
            for ext in extensions:
                if ext in path:
                    self.menu.addSeparator()
                    self.menu.addAction(self.playAction) 
                    self.menu.addAction(self.playVLCAction) 
                    self.menu.addSeparator()
            extensions = [".mp4", "mpg", ".m4a", ".mpeg", "avi", ".mkv", ".webm", ".wav", ".ogg", ".flv ", ".vob", ".ogv", ".ts", ".m2v", "m4v", "3gp", ".f4v"]
            for ext in extensions:
                if ext in path:
                    self.menu.addAction(self.mp3Action) 
                    self.menu.addSeparator()
            if ".mp3" in path:
                self.menu.addAction(self.playlistAction)
            self.menu.addAction(self.refreshAction)
            self.menu.addAction(self.hiddenAction)
            self.menu.addAction(self.zipFilesAction)
            self.menu.addAction(self.helpAction) 
            self.menu.popup(QCursor.pos())
        else:
            index = self.treeview.selectionModel().currentIndex()
            path = self.dirModel.fileInfo(index).absoluteFilePath()
            print("context:", path)
            self.menu = QMenu(self.treeview)
            if os.path.isdir(path):
                self.menu.addAction(self.newWinAction)
                self.menu.addAction(self.findFilesAction)
                self.menu.addAction(self.zipAction)
            self.menu.popup(QCursor.pos())

    def renameFile(self):
        index = self.listview.selectionModel().currentIndex()
        self.listview.edit(index)

    def copyFile(self):
        self.copyList = []
        selected = self.listview.selectionModel().selectedIndexes()
        for index in selected:
            if index.column() == 0:
                self.copyList.append(self.currentPath + "/" + self.fileModel.data(index,
                    self.fileModel.FileNameRole))
        print("%s\n%s" % ("filepath(s) copied:", '\n'.join(self.copyList)))

    def pasteFile(self):
        index = self.treeview.selectionModel().currentIndex()
        for target in self.copyList:
            print(target)
            destination = self.dirModel.fileInfo(index).absoluteFilePath()
            print("%s %s" % ("pasted File to", destination))
            self.process.execute("cp", [target, destination])
            if self.cut == True:
                self.process.execute("rm", [target])
            self.cut == False

    def cutFile(self):
        self.cut = True
        self.copyFile()
        
    def deleteFile(self):
        self.copyFile()
        msg = QMessageBox.question(self, "Info", "Caution!\nReally delete this Files?\n" + '\n'.join(self.copyList), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if msg == QMessageBox.Yes:
            print('Deletion confirmed.')
            index = self.listview.selectionModel().currentIndex()
            self.copyPath = self.fileModel.fileInfo(index).absoluteFilePath()
            print("%s %s" % ("file deleted", self.copyPath))
            for delFile in self.listview.selectionModel().selectedIndexes():
                self.fileModel.remove(delFile)
        else:
            print('No clicked.')

    def deleteFileTrash(self):
        index = self.listview.selectionModel().currentIndex()
        self.copyFile()
        msg = QMessageBox.question(self, "Info", "Caution!\nReally move this Files to Trash\n" + '\n'.join(self.copyList), QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if msg == QMessageBox.Yes:
            print('Deletion confirmed.')
            for delFile in self.copyList:
                self.process.execute("gio", ["trash", delFile])
                print("%s %s" % ("file moved to trash:", delFile))
        else:
            print('No clicked.')

    def createStatusBar(self):
        sysinfo = QSysInfo()
        myMachine = "current CPU Architecture: " + sysinfo.currentCpuArchitecture() + " *** " + sysinfo.prettyProductName() + " *** " + sysinfo.kernelType() + " " + sysinfo.kernelVersion()
        self.statusBar().showMessage(myMachine, 0)      

def mystylesheet(self):
    return """
QTreeView
{
background: #e9e9e9;
selection-color: white;
border: 1px solid lightgrey;
selection-background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #729fcf, stop: 1  #204a87);
color: #202020;
outline: 0;
} 
QTreeView::item::hover{
background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #babdb6, stop: 0.5 #d3d7cf, stop: 1 #babdb6);
}
QTreeView::item::focus
{
background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #729fcf, stop: 1  #204a87);
border: 0px;
}
QMenu
{
background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                 stop: 0 #E1E1E1, stop: 0.4 #DDDDDD,
                                 stop: 0.5 #D8D8D8, stop: 1.0 #D3D3D3);
}
QMenu::item::selected
{
color: white;
background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 lightblue, stop: 1  blue);
border: 0px;
}
QHeaderView
{
background: #d3d7cf;
color: #555753;
font-weight: bold;
}
QStatusBar
{
font-size: 8pt;
color: #555753;
}
QMenuBar
{
background: transparent;
border: 0px;
}
QToolBar
{
background: transparent;
border: 0px;
}
QMainWindow
{
     background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                 stop: 0 #E1E1E1, stop: 0.4 #DDDDDD,
                                 stop: 0.5 #D8D8D8, stop: 1.0 #D3D3D3);
}
QLabel
{
    font-size: 10pt;
    text-align: center;
     background: transparent;
    color:#204a87;
}
QMessageBox
{
    font-size: 10pt;
    text-align: center;
     background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                                 stop: 0 #E1E1E1, stop: 0.4 #DDDDDD,
                                 stop: 0.5 #D8D8D8, stop: 1.0 #D3D3D3);
    color:#204a87;
}
QPushButton{
background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 white, stop: 1 grey);
border-style: solid;
border-color: darkgrey;
height: 26px;
width: 66px;
border-width: 1px;
border-radius: 6px;
}
QPushButton:hover:!pressed{
background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 lightblue, stop: 1  blue);
border-style: solid;
border-color: darkgrey;
height: 26px;
width: 66px;
border-width: 1px;
border-radius: 6px;
}
QPushButton:hover{
background-color: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 lightgreen, stop: 1  green);
border-style: solid;
border-color: darkgrey;
height: 24px;
width: 66px;
border-width: 1px;
border-radius: 4px;
}
    """       

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = myWindow()
    w.show()
    if len(sys.argv) > 1:
        path = sys.argv[1]
        print(path)
        w.listview.setRootIndex(w.fileModel.setRootPath(path))
        w.treeview.setRootIndex(w.dirModel.setRootPath(path))
        w.setWindowTitle(path)
    sys.exit(app.exec_())