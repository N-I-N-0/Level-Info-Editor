#!/usr/bin/python
# -*- coding: latin-1 -*-

# Level Info Editor - Edits NewerSMBW's LevelInfo.bin
# Version 1.5
# Copyright (C) 2013-2014 RoadrunnerWMC

# This file is part of Level Info Editor.

# Level Info Editor is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Level Info Editor is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Level Info Editor.  If not, see <http://www.gnu.org/licenses/>.



# level_info_editor.py
# This is the main executable for Level Info Editor


################################################################
################################################################


version = '1.5'

from PyQt5 import QtCore, QtGui, QtWidgets
import sys



class WorldInfo():
    """Class that represents a world"""
    def __init__(self):
        """Initialises the WorldInfo"""
        self.WorldNumber = None
        self.HasL = False
        self.LName = ''
        self.Levels = []

    def toPyObject(self):
        """Py2/Py3 compatibility"""
        return self

    def setWorldNumber(self, number=None):
        """Sets the world number (None is a valid value)"""
        self.WorldNumber = number

    def setLeftHalf(self, exists):
        """Turns the left half on or off"""
        self.HasL = exists

    def setLeftName(self, name):
        """Sets the left half name"""
        self.LName = name 



class LevelInfo():
    """Class that represents a level"""
    def __init__(self):
        """Initialises the LevelInfo"""
        self.name = ''
        self.FileW = 0
        self.FileL = 0
        self.DisplayW = 0
        self.DisplayL = 0
        self.IsLevel = True
        self.NormalExit = False
        self.SecretExit = False
        self.CreatorIndex = 0
        self.DevRecordTime = 100

    def toPyObject(self):
        """Py2/Py3 compatibility"""
        return self

    def setName(self, name):
        """Sets the level name"""
        self.name = name

    def setFileNameW(self, world):
        """Sets the filename (world number)"""
        self.FileW = world

    def setFileNameL(self, level):
        """Sets the filename (level number)"""
        self.FileL = level

    def setDisplayNameW(self, world):
        """Sets the Display name (world number)"""
        self.DisplayW = world

    def setDisplayNameL(self, level):
        """Sets the Display name (level number)"""
        self.DisplayL = level

    def setFlags(self, flags):
        """Sets some flags"""
        self.IsLevel     = ((flags >> 1)  & 1 == 1)
        self.NormalExit  = ((flags >> 4)  & 1 == 1)
        self.SecretExit  = ((flags >> 5)  & 1 == 1)

    def getFlags(self):
        """Returns an int which represent the two bytes the flags are encoded in"""
        b1 = 0
        b2 = 0
        if self.IsLevel:    b1 += 0x02
        if self.NormalExit: b1 += 0x10
        if self.SecretExit: b1 += 0x20
        return (b2 << 8) | b1

    def setCreator(self, index):
        """Sets the Creator of the level"""
        self.CreatorIndex = index

    def setDevRecordTime(self, time):
        """Sets the Developer Record Time Left"""
        self.DevRecordTime = time


class LevelInfoFile():
    """Class that represents LevelInfo.bin"""
    def __init__(self, rawdata=None):
        """Initialises the LevelInfoFile"""
        if rawdata == None: self.initAsEmpty()
        else: self.initFromData(rawdata)

    def initAsEmpty(self):
        """Sets all the variables to their defaults"""
        self.worlds = []
        self.comments = ''

    def initFromData(self, rawdata):
        """Initialises the LevelInfoFile from raw binary data"""
        global levelNamesOffset

        # Py2 opens binary files as strings; convert it to bytes
        if sys.version[0] == '2':
            new = []
            for char in rawdata: new.append(ord(char))
            rawdata = new
        else:
            new = []
            for i in rawdata: new.append(i)
            rawdata = new

        # Check for the file header
        if rawdata[0] != ord('N'): return
        if rawdata[1] != ord('W'): return
        if rawdata[2] != ord('R'): return
        #if rawdata[3] != ord('p'): return

        # Load the world data offsets
        numberOfWorlds = rawdata[11]
        worldOffs = []
        for worldNum in range(numberOfWorlds):
            off = (rawdata[14 + (4*worldNum)] << 8) | rawdata[15 + (4*worldNum)]
            worldOffs.append(off)

        # Load the worlds
        worlds = []
        for offset in worldOffs:
            numberOfLevels = rawdata[offset + 3]
            worldData = rawdata[offset+4: (offset+4) + (16*numberOfLevels)]

            # Make a world and add levels/headers to it
            world = WorldInfo()
            headers = []
            for levelOff in range(int(len(worldData)/16)):
                levelData = worldData[levelOff*16:(levelOff*16) + 16]

                # Find the text
                textOffset = (levelData[14] << 8) | levelData[15]
                textLength = levelData[9]
                text = ''
                for char in rawdata[textOffset:textOffset + textLength]:
                    #char = char + 0x30
                    #if char > 255: char -= 256
                    text += chr(char)

                # Add header info or levels
                if levelData[7] >= 100:
                    # It's a world header
                    world.setWorldNumber(levelData[6])
                    if levelData[7] == 100:
                        world.setLeftHalf(True)
                        world.setLeftName(text)
                else:
                    # It's a real level
                    level = LevelInfo()
                    level.setName(text)
                    level.setCreator((levelData[0] << 8) | levelData[1])
                    level.setDevRecordTime((levelData[2] << 8) | levelData[3])
                    print(level.DevRecordTime)
                    level.setFileNameW(levelData[4] + 1)
                    level.setFileNameL(levelData[5] + 1)
                    level.setDisplayNameW(levelData[6])
                    level.setDisplayNameL(levelData[7])
                    flags = (levelData[10] << 8) | levelData[11]
                    level.setFlags(flags)

                    # Add it to world
                    world.Levels.append(level)
            # Add it to worlds
            worlds.append(world)

        # Assign worlds to self.worlds
        self.worlds = worlds

        # Get the creators
        start = self.GetCommentsOffset()
        creatorCount = (rawdata[start] << 8) | rawdata[start + 1]
        creatorLength = (rawdata[start + 2] << 8) | rawdata[start + 3]
        mainWindow.view.creatorListWidget.clear()
        for i in range(creatorCount):
            creatorOffset = (rawdata[start+4*i+4] << 24) | (rawdata[start+4*i+5] << 16) | (rawdata[start+4*i+6] << 8) | rawdata[start+4*i+7]
            item = QtWidgets.QListWidgetItem(self.GetACreator(rawdata[creatorOffset:]))
            item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
            mainWindow.view.creatorListWidget.addItem(item)


    def GetACreator(self, raw):
        result = ''
        i = 0
        while not raw[i] == 0:
            result += chr(raw[i])
            i += 1
        return result


    def GetCommentsOffset(self):
        """Calculates the offset of the comments based on worlds and levels"""
        # I'm trying to make this as easy-to-read as possible.
        offset = 0

        offset += 4 # "NWRq" text
        offset += 4 # creatorsOffset
        offset += 4 # Number of Worlds bytes
        for world in self.worlds:
            offset += 4 # Offset to the world data in the file header
            offset += 4 # Number of Levels bytes

            if world.HasL: offset += 16 # data for that takes 12 bytes
            for level in world.Levels:
                offset += 16 # Each level is 12 bytes

        return offset

    def packCreators(self):
        creators = ''
        creatorOffsets = []
        self.comments = []
        creatorCount = mainWindow.view.creatorListWidget.count()
        currentOffset = self.GetCommentsOffset() + 4 + (4 * creatorCount)             #4 bytes per offset
        for i in range(creatorCount):
            item = mainWindow.view.creatorListWidget.item(i)
            creators += item.text() + '\0'
            self.comments.append((currentOffset >> 24) & 0xFF)
            self.comments.append((currentOffset >> 16) & 0xFF)
            self.comments.append((currentOffset >>  8) & 0xFF)
            self.comments.append((currentOffset >>  0) & 0xFF)
            currentOffset += len(item.text()) + 1
        
        for char in creators:
            self.comments.append(ord(char))
        
        return creatorCount

        
    def save(self):
        """Returns bytes that can be saved back to a LevelInfo.bin file"""
        result = []
        creatorCount = int(self.packCreators())
        creatorLength = int(len(self.comments) + 1)
        TextStart = self.GetCommentsOffset() + creatorLength + 4

        # First things first - add "NWRq"
        result.append(ord('N'))
        result.append(ord('W'))
        result.append(ord('R'))
        result.append(ord('q'))

        creatorsOffset = self.GetCommentsOffset()
        result.append((creatorsOffset >> 24) & 0xFF)                                #creatorsOffset
        result.append((creatorsOffset >> 16) & 0xFF)
        result.append((creatorsOffset >>  8) & 0xFF)
        result.append((creatorsOffset >>  0) & 0xFF)
        
        NumOfWorlds = len(self.worlds)
        result.append((NumOfWorlds >> 24) & 0xFF)                                   #sectionCount
        result.append((NumOfWorlds >> 16) & 0xFF)
        result.append((NumOfWorlds >>  8) & 0xFF)
        result.append((NumOfWorlds >>  0) & 0xFF)

        # Add blank spaces for each world value
        for w in self.worlds:
            for i in range(4): result.append(0)

        # Add worlds and world-offsets at the same time
        CurrentOffset = len(result)
        CurrentTextOffset = int(TextStart) # make a new int
        Text = []
        WorldNumber = 0
        for world in self.worlds:
            # Set the World Offset start value to CurrentOffset
            result[12+(WorldNumber*4)] = (CurrentOffset >> 24) & 0xFF               #sectionOffsets
            result[13+(WorldNumber*4)] = (CurrentOffset >> 16) & 0xFF
            result[14+(WorldNumber*4)] = (CurrentOffset >>  8) & 0xFF
            result[15+(WorldNumber*4)] = (CurrentOffset >>  0) & 0xFF

            # Create a place to store some world info
            worldData = []

            # Add the Number of Levels value
            num = len(world.Levels)
            if world.HasL: num += 1
            worldData.append((num >> 24) & 0xFF)                                    #levelCount
            worldData.append((num >> 16) & 0xFF)
            worldData.append((num >>  8) & 0xFF)
            worldData.append((num >>  0) & 0xFF)

            # Add data to worldData for each world half                             #entry_s
            if world.HasL:
                worldData.append(0x00)                                              #creatorID
                worldData.append(0x00)
                worldData.append(0x00)                                              #devRecordTime
                worldData.append(0x00)
                worldData.append(0x62)                                              #worldSlot      filename: 98-98
                worldData.append(0x62)                                              #levelSlot
                worldData.append(world.WorldNumber)                                 #displayWorld   display name: WN-100
                worldData.append(0x64)                                              #displayLevel
                worldData.append(0x00)                                              #nameLength, padding
                worldData.append(len(world.LName))
                worldData.append(0x00)                                              #flags
                worldData.append(0x00)
                worldData.append(0x00)                                              #nameOffset
                worldData.append(0x00)
                worldData.append((CurrentTextOffset >> 8) & 0xFF)
                worldData.append((CurrentTextOffset >> 0) & 0xFF)
                CurrentTextOffset += len(world.LName) + 1
                for char in world.LName: Text.append(ord(char))
                Text.append(0x00)

            # Add data to worldData for each level                                  #entry_s
            for level in world.Levels:
                flags = level.getFlags()
                worldData.append((level.CreatorIndex >> 8) & 0xFF)                  #creatorID
                worldData.append((level.CreatorIndex >> 0) & 0xFF)
                worldData.append((level.DevRecordTime >> 8) & 0xFF)                 #devRecordTime
                worldData.append((level.DevRecordTime >> 0) & 0xFF)
                print("====")
                print((level.DevRecordTime >> 8) & 0xFF)
                print((level.DevRecordTime >> 0) & 0xFF)
                print(level.DevRecordTime)
                print("====")
                
                worldData.append(level.FileW - 1)                                   #worldSlot
                worldData.append(level.FileL - 1)                                   #levelSlot
                worldData.append(level.DisplayW)                                    #displayWorld
                worldData.append(level.DisplayL)                                    #displayLevel
                worldData.append(0x00)                                              #nameLength, padding
                worldData.append(len(level.name))
                worldData.append((flags >> 8) & 0xFF)                               #flags
                worldData.append((flags >> 0) & 0xFF)
                worldData.append(0x00)                                              #nameOffset
                worldData.append(0x00)
                worldData.append((CurrentTextOffset >> 8) & 0xFF)
                worldData.append((CurrentTextOffset >> 0) & 0xFF)
                CurrentTextOffset += len(level.name) + 1
                for char in level.name: Text.append(ord(char))
                Text.append(0x00)

            # Add worldData to result
            someTestingCount = 0
            for i in worldData:
                result.append(i)
                CurrentOffset += 1
                someTestingCount += 1

            print(someTestingCount)

            # Get ready for the next world
            WorldNumber += 1

        # Add the comments
        result.append((creatorCount >>  8) & 0xFF)                                  #creatorCount
        result.append((creatorCount >>  0) & 0xFF)
        result.append((creatorLength >>  8) & 0xFF)                                 #creatorLength
        result.append((creatorLength >>  0) & 0xFF)
        for char in self.comments: result.append(char)
        result.append(0x00)

        # Add text
        for char in Text:
            #char = char - 0x30
            #if char < 0: char += 256
            result.append(char)

        # Py2 saves binary files as strings
        if sys.version[0] == '2':
            string = ''
            for i in result: string += chr(i)
            return string
        else:
            return bytes(result)


########################################################################
########################################################################
########################################################################
########################################################################


# Drag-and-Drop Picker
class DNDPicker(QtWidgets.QListWidget):
    """A list widget which calls a function when an item's been moved"""
    def __init__(self, handler):
        QtWidgets.QListWidget.__init__(self)
        self.handler = handler
        self.setDragDropMode(QtWidgets.QListWidget.InternalMove)
    def dropEvent(self, event):
        QtWidgets.QListWidget.dropEvent(self, event)
        self.handler()


class LevelInfoViewer(QtWidgets.QWidget):
    """Widget that views level info"""
    def __init__(self):
        """Initialises the widget"""
        QtWidgets.QWidget.__init__(self)
        self.file = LevelInfoFile()

        # Create the Worlds widgets
        WorldBox = QtWidgets.QGroupBox('Worlds')
        self.WorldPicker = DNDPicker(self.HandleWDragDrop)
        self.WABtn = QtWidgets.QPushButton('Add')
        self.WRBtn = QtWidgets.QPushButton('Remove')

        # Add some tooltips
        self.WABtn.setToolTip('<b>Add:</b><br>Adds a world to the file.')
        self.WRBtn.setToolTip('<b>Remove:</b><br>Removes the currently selected world from the file.')

        # Disable some
        self.WRBtn.setEnabled(False)

        # Connect them to handlers
        self.WorldPicker.currentItemChanged.connect(self.HandleWorldSel)
        self.WABtn.clicked.connect(self.HandleWA)
        self.WRBtn.clicked.connect(self.HandleWR)

        # Make a layout
        L = QtWidgets.QGridLayout()
        L.addWidget(self.WorldPicker, 0, 0, 1, 2)
        L.addWidget(self.WABtn,   1, 0)
        L.addWidget(self.WRBtn,   1, 1)
        WorldBox.setLayout(L)


        # Create the World Options widget
        self.WorldEdit = WorldOptionsEditor()
        self.WorldEdit.dataChanged.connect(self.HandleWorldDatChange)


        # Create the Levels widgets
        LevelBox = QtWidgets.QWidget()
        self.LevelPicker = DNDPicker(self.HandleLDragDrop)
        self.LevelEdit = LevelEditor()
        self.LABtn = QtWidgets.QPushButton('Add')
        self.LRBtn = QtWidgets.QPushButton('Remove')

        # Add some tooltips
        self.LABtn.setToolTip('<b>Add:</b><br>Adds a level to the currently selected world.')
        self.LRBtn.setToolTip('<b>Remove:</b><br>Removes the currently selected level from the world.')

        # Disable some
        self.LABtn.setEnabled(False)
        self.LRBtn.setEnabled(False)

        # Connect them to handlers
        self.LevelPicker.currentItemChanged.connect(self.HandleLevelSel)
        self.LevelEdit.dataChanged.connect(self.HandleLevelDatChange)
        self.LevelEdit.navRequest.connect(self.HandleLevelNavRequest)
        self.LABtn.clicked.connect(self.HandleLA)
        self.LRBtn.clicked.connect(self.HandleLR)

        # Make a layout
        L = QtWidgets.QGridLayout()
        L.addWidget(self.LevelPicker, 0, 0, 1, 2)
        L.addWidget(self.LABtn,       1, 0)
        L.addWidget(self.LRBtn,       1, 1)
        L.addWidget(self.LevelEdit,   2, 0, 1, 2)
        LevelBox.setLayout(L)


        # Create the Comments editor and layout
        self.CommentsBox = QtWidgets.QWidget()
        
        self.creatorCurrentlySelectedID = QtWidgets.QLabel("Currently selected: None")
        self.creatorListWidget = QtWidgets.QListWidget()
        self.creatorListAdd = QtWidgets.QPushButton("Add")
        self.creatorListRemove = QtWidgets.QPushButton("Remove")

        self.creatorListAdd.clicked.connect(self.handleAddCreator)
        self.creatorListRemove.clicked.connect(self.handleRemoveCreator)
        self.creatorListWidget.currentRowChanged.connect(self.handleCreatorSelectionChanged)

        STL = QtWidgets.QGridLayout()
        STL.addWidget(self.creatorCurrentlySelectedID, 0, 0, 1, 2)
        STL.addWidget(self.creatorListWidget,          1, 0, 1, 2)
        STL.addWidget(self.creatorListAdd,             2, 0, 1, 1)
        STL.addWidget(self.creatorListRemove,          2, 1, 1, 1)
        self.CommentsBox.setLayout(STL)


        # Create the tab widget
        tab = QtWidgets.QTabWidget()
        tab.addTab(self.WorldEdit, 'World Options')
        tab.addTab(LevelBox, 'Levels')
        tab.addTab(self.CommentsBox, 'Creators')
        
        tab.currentChanged.connect(self.handleTabChanged)

        # Make a main layout
        L = QtWidgets.QHBoxLayout()
        L.addWidget(WorldBox)
        L.addWidget(tab)
        self.setLayout(L)

    def handleTabChanged(self, index):
        if index == 1:
            self.LevelEdit.CreatorEdit.clear()
            for i in range(self.creatorListWidget.count()):
                item = self.creatorListWidget.item(i)
                self.LevelEdit.CreatorEdit.addItem(item.text())
            

    def setFile(self, file):
        """Changes the file to view"""
        self.file = file

        self.WorldPicker.clear()
        self.LevelPicker.clear()

        # Add worlds
        for world in self.file.worlds:
            item = QtWidgets.QListWidgetItem() # self.UpdateNames will add the name
            item.setData(QtCore.Qt.UserRole, world)
            self.WorldPicker.addItem(item)

        # Add comments
        #self.CommentsEdit.setPlainText(self.file.comments)

        # Update world names
        self.UpdateNames()

    def UpdateNames(self):
        """Updates item names in all 3 item-picker widgets"""
        # WorldPicker
        for item in self.WorldPicker.findItems('', QtCore.Qt.MatchContains):
            world = item.data(QtCore.Qt.UserRole)
            text = 'World '
            if world.WorldNumber == None: text += '(unknown)'
            else: text += str(world.WorldNumber)
            item.setText(text)

        # LevelPicker
        for item in self.LevelPicker.findItems('', QtCore.Qt.MatchContains):
            level = item.data(QtCore.Qt.UserRole)
            item.setText(level.name)

    def saveFile(self):
        """Returns the file in saved form"""
        return self.file.save() # self.file does this for us



    # World Functions

    def HandleWorldSel(self):
        """Handles the user picking a world"""
        self.WorldEdit.clear()
        self.LevelPicker.clear()
        self.LevelEdit.clear()

        # Get the current item (it's None if nothing's selected)
        currentItem = self.WorldPicker.currentItem()

        # Enable/disable buttons
        if currentItem == None:
            self.WRBtn.setEnabled(False)
            self.LABtn.setEnabled(False)
            self.LRBtn.setEnabled(False)
        else:
            index = self.WorldPicker.indexFromItem(currentItem).row()
            numberOfItems = self.WorldPicker.count()

            self.WRBtn.setEnabled(True)
            self.LABtn.setEnabled(True)

        # Get the world
        if currentItem == None: return
        world = currentItem.data(QtCore.Qt.UserRole)

        # Set up the World Options Editor
        self.WorldEdit.setWorld(world)

        # Add levels to self.LevelPicker
        for level in world.Levels:
            item = QtWidgets.QListWidgetItem(level.name)
            item.setData(QtCore.Qt.UserRole, level)
            self.LevelPicker.addItem(item)
        self.LevelPicker.setCurrentRow(0)


    def HandleWA(self):
        """Handles Add World button clicks"""
        world = WorldInfo()
        text = 'World (unknown)'

        # Add it to self.file and self.WorldPicker
        self.file.worlds.append(world)
        item = QtWidgets.QListWidgetItem(text)
        item.setData(QtCore.Qt.UserRole, world)
        self.WorldPicker.addItem(item)
        self.WorldPicker.scrollToItem(item)
        item.setSelected(True)

        self.UpdateNames()

    def HandleWR(self):
        """Handles Remove World button clicks"""
        item = self.WorldPicker.currentItem()
        world = item.data(QtCore.Qt.UserRole)

        # Remove it from file and the picker
        self.file.worlds.remove(world)
        self.WorldPicker.takeItem(self.WorldPicker.row(item))

        self.UpdateNames()

    def HandleWDragDrop(self):
        """Handles dragging-and-dropping in the World Picker"""
        newWorlds = []
        for item in self.WorldPicker.findItems('', QtCore.Qt.MatchContains):
            world = item.data(QtCore.Qt.UserRole)
            newWorlds.append(world)
        self.file.Worlds = newWorlds

        self.UpdateNames()

    def HandleWorldDatChange(self):
        """Handles the user changing world data"""
        self.UpdateNames()



    # Level Functions

    def HandleLevelSel(self):
        """Handles the user picking a level"""
        self.LevelEdit.clear()

        # Get the current item (it's None if nothing's selected)
        currentItem = self.LevelPicker.currentItem()

        # Enable/disable buttons
        if currentItem == None:
            self.LRBtn.setEnabled(False)
        else:
            index = self.LevelPicker.indexFromItem(currentItem).row()
            numberOfItems = self.LevelPicker.count()

            self.LRBtn.setEnabled(True)

        # Get the level
        if currentItem == None: return
        level = currentItem.data(QtCore.Qt.UserRole)

        # Set LevelEdit to edit it
        self.LevelEdit.setLevel(level)

    def HandleLevelDatChange(self):
        """Handles the user changing level data"""
        self.UpdateNames()

    def HandleLevelNavRequest(self, isUp, refocusWidget):
        """Handles the user pressing PgUp or PgDn to switch between levels"""
        currentRow = self.LevelPicker.currentRow()

        newRow = currentRow + (-1 if isUp else 1)
        newRow = max(0, newRow)
        newRow = min(newRow, self.LevelPicker.count() - 1)

        if newRow != currentRow:
            self.LevelPicker.setCurrentRow(newRow)
            refocusWidget.setFocus(True)

    def HandleLA(self):
        """Handles Add Level button clicks"""
        level = LevelInfo()
        text = 'New Level'
        level.setName(text)
        item = QtWidgets.QListWidgetItem(text)
        item.setData(QtCore.Qt.UserRole, level)

        # Add it to the current world and self.LevelPicker
        w = self.WorldPicker.currentItem().data(QtCore.Qt.UserRole)
        w.Levels.append(level)
        self.LevelPicker.addItem(item)
        self.LevelPicker.scrollToItem(item)
        item.setSelected(True)

        self.UpdateNames()

    def HandleLR(self):
        """Handles Remove Level button clicks"""
        item = self.LevelPicker.currentItem()
        level = item.data(QtCore.Qt.UserRole)

        # Remove it from file and the picker
        w = self.WorldPicker.currentItem().data(QtCore.Qt.UserRole)
        w.Levels.remove(level)
        self.LevelPicker.takeItem(self.LevelPicker.row(item))

        self.UpdateNames()

    def HandleLDragDrop(self):
        """Handles dragging-and-dropping in the Level Picker"""
        w = self.WorldPicker.currentItem().data(QtCore.Qt.UserRole)
        
        newLevels = []
        for item in self.LevelPicker.findItems('', QtCore.Qt.MatchContains):
            level = item.data(QtCore.Qt.UserRole)
            newLevels.append(level)
        w = self.WorldPicker.currentItem().data(QtCore.Qt.UserRole)
        w.Levels = newLevels

        self.UpdateNames()

    #Creators functions
    def handleAddCreator(self):
        item = QtWidgets.QListWidgetItem("Someone")
        item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)
        self.creatorListWidget.addItem(item)
    
    def handleRemoveCreator(self):
        item = self.creatorListWidget.currentItem()
        self.creatorListWidget.takeItem(self.creatorListWidget.row(item))

    def handleCreatorSelectionChanged(self, row):
        if row < 0:
            self.creatorCurrentlySelectedID.setText("Currently selected: None")
        else:
            self.creatorCurrentlySelectedID.setText("Currently selected: {}".format(row))


########################################################################
########################################################################
########################################################################
########################################################################


class WorldOptionsEditor(QtWidgets.QWidget):
    """Widget that allows the user to change world settings"""
    dataChanged = QtCore.pyqtSignal()
    def __init__(self):
        """Initialises the WorldOptionsEditor"""
        QtWidgets.QWidget.__init__(self)
        self.world = None

        # Create the data-editing widgets
        self.NumberEdit = QtWidgets.QSpinBox()
        self.NumberEdit.setMaximum(255)
        self.LExistsEdit = QtWidgets.QCheckBox()
        self.LNameEdit = QtWidgets.QLineEdit()
        self.LNameEdit.setMaxLength(255)

        # Add some tooltips
        numberWarning = '<br><br><b>Note:</b><br>You can only set the world\'s World Number if this is an actual world (checkbox)!'
        self.NumberEdit.setToolTip('<b>World Number:</b><br>Changes the currently selected world\'s World Number.' + numberWarning)
        self.LExistsEdit.setToolTip('<b>Is an actual world:</b><br>Check this for actual worlds that got a world map.' + numberWarning)
        self.LNameEdit.setToolTip('<b>World\'s Name:</b><br>This will be displayed on the map hud.')

        # Disable them all
        self.NumberEdit.setEnabled(False)
        self.LExistsEdit.setEnabled(False)
        self.LNameEdit.setEnabled(False)

        # Connect them to handlers
        self.NumberEdit.valueChanged.connect(self.HandleNumberChange)
        self.LExistsEdit.stateChanged.connect(self.HandleLExistsChange)
        self.LNameEdit.textEdited.connect(self.HandleLNameChange)

        # Create a layout
        L = QtWidgets.QFormLayout()
        L.addRow('World Number:', self.NumberEdit)
        L.addRow('Is an actual world:', self.LExistsEdit)
        L.addRow('World\'s Name:', self.LNameEdit)
        self.setLayout(L)


    def clear(self):
        """Clears all data from the WorldOptionsEditor"""
        self.world = None

        # Disable the boxes
        self.NumberEdit.setEnabled(False)
        self.LExistsEdit.setEnabled(False)
        self.LNameEdit.setEnabled(False)

        # Set them all to defaults
        self.NumberEdit.setValue(0)
        self.LExistsEdit.setChecked(False)
        self.LNameEdit.setText('')

    def setWorld(self, world):
        """Sets the world to be edited"""
        self.world = world

        # Enable the first box, and potentially others
        if world.HasL: self.NumberEdit.setEnabled(True)
        self.LExistsEdit.setEnabled(True)
        self.LNameEdit.setEnabled(world.HasL)
        
        # Set them to the correct values
        if world.HasL: self.NumberEdit.setValue(world.WorldNumber)
        self.LExistsEdit.setChecked(world.HasL)
        if world.HasL: self.LNameEdit.setText(world.LName)
        
    def HandleNumberChange(self):
        """Handles self.NumberEdit changes"""
        if self.world == None: return
        self.world.WorldNumber = self.NumberEdit.value()
        self.dataChanged.emit()

    def HandleLExistsChange(self):
        """Handles self.LExistsEdit changes"""
        if self.world == None: return
        self.world.HasL = self.LExistsEdit.isChecked()
        self.LNameEdit.setEnabled(self.world.HasL)
        if not self.world.HasL: self.LNameEdit.setText('')
        self.NumberEdit.setEnabled(self.world.HasL)
        if not self.world.HasL:
            self.world.WorldNumber = None
            self.NumberEdit.setValue(0)
        elif self.world.WorldNumber == None:
            self.world.WorldNumber = 0
            self.NumberEdit.setValue(0)
        self.dataChanged.emit()

    def HandleLNameChange(self):
        """Handles self.LNameEdit changes"""
        if self.world == None: return
        self.world.LName = str(self.LNameEdit.text())
        self.dataChanged.emit()



class LevelEditor(QtWidgets.QGroupBox):
    """Widget that allows the user to change level settings"""
    dataChanged = QtCore.pyqtSignal()
    navRequest = QtCore.pyqtSignal(bool, QtWidgets.QWidget)
    def __init__(self):
        """Initializes the LevelEditor"""
        QtWidgets.QGroupBox.__init__(self)
        self.setTitle('Level')
        self.level = None

        # Create the data-editing widgets
        self.NameEdit = QtWidgets.QLineEdit()
        self.NameEdit.setMaxLength(255)
        self.FileEdit = LevelNameEdit()
        self.FileEdit.setMinToOne()
        self.DisplayEdit = LevelNameEdit()
        self.IsLevelEdit = QtWidgets.QCheckBox()
        self.NormalExitEdit = QtWidgets.QCheckBox()
        self.SecretExitEdit = QtWidgets.QCheckBox()
        self.CreatorEdit = QtWidgets.QComboBox()
        self.DevRecordTimeEdit = QtWidgets.QSpinBox()
        self.DevRecordTimeEdit.setMinimum(0)
        self.DevRecordTimeEdit.setMaximum(65535)
        
        # Add some tooltips
        self.NameEdit.setToolTip('<b>Name:</b><br>Changes the level\'s name.')
        self.FileEdit.setToolTip('<b>Filename:</b><br>Changes the name of the file the level will load from (.arc is automatically added).')
        self.DisplayEdit.setToolTip('<b>Display Name:</b><br>Changes the on-screen name of this level.<br><br><b>Note:</b><br>Special characters are often used here - symbols such as Castle, Tower, Boo House and Toad House. Each can be used by picking a specific number. Look at Newer SMBW\'s original LevelInfo.bin to find some!')
        self.IsLevelEdit.setToolTip('<b>Star Coins Menu:</b><br>If this is checked, the level will appear in the Star Coins Menu.')
        self.NormalExitEdit.setToolTip('<b>Normal Exit:</b><br>If this is checked, the level will have a normal exit.')
        self.SecretExitEdit.setToolTip('<b>Secret Exit:</b><br>If this is checked, the level will have a secret exit.')
        self.CreatorEdit.setToolTip('<b>Creator:</b><br>This changes which side of the Star Coins menu the level appears on.')
        self.DevRecordTimeEdit.setToolTip('<b>Dev Record:</b><br>Time left in-game for the recorded dev replay.')

        # Disable them
        self.NameEdit.setEnabled(False)
        self.FileEdit.setEnabled(False)
        self.DisplayEdit.setEnabled(False)
        self.IsLevelEdit.setEnabled(False)
        self.NormalExitEdit.setEnabled(False)
        self.SecretExitEdit.setEnabled(False)
        self.CreatorEdit.setEnabled(False)
        self.DevRecordTimeEdit.setEnabled(False)

        # Connect them to handlers
        self.NameEdit.textEdited.connect(self.HandleNameChange)
        self.FileEdit.dataChanged.connect(self.HandleFileChange)
        self.DisplayEdit.dataChanged.connect(self.HandleDisplayChange)
        self.IsLevelEdit.stateChanged.connect(self.HandleIsLevelChange)
        self.NormalExitEdit.stateChanged.connect(self.HandleNormalExitChange)
        self.SecretExitEdit.stateChanged.connect(self.HandleSecretExitChange)
        self.CreatorEdit.currentIndexChanged.connect(self.HandleCreatorChange)
        self.DevRecordTimeEdit.valueChanged.connect(self.HandleDevRecordChange)

        # Create a layout
        L = QtWidgets.QFormLayout()
        L.addRow('Name:', self.NameEdit)
        L.addRow('Filename:', self.FileEdit)
        L.addRow('Display Name:', self.DisplayEdit)
        L.addRow('Normal Exit:', self.NormalExitEdit)
        L.addRow('Secret Exit:', self.SecretExitEdit)
        L.addRow('Star Coins Menu:', self.IsLevelEdit)
        L.addRow('Creator:', self.CreatorEdit)
        L.addRow('Dev Record:', self.DevRecordTimeEdit)
        self.setLayout(L)

        # Watch for PageUp/PageDown
        for leafWidget in [self.NameEdit,
                           self.FileEdit.WEdit,
                           self.FileEdit.LEdit,
                           self.DisplayEdit.WEdit,
                           self.DisplayEdit.LEdit,
                           self.NormalExitEdit,
                           self.SecretExitEdit,
                           self.IsLevelEdit,
                           self.CreatorEdit,
                           self.DevRecordTimeEdit]:
            leafWidget.installEventFilter(self)


    def eventFilter(self, obj, event):
        """Filter events for leaf widgets, looking for PageUp/PageDown"""
        # Changing the selected level causes the field edit widget to
        # lose focus, so we pass it in the signal and ask that the
        # handler function please refocus it after switching levels.
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_PageUp:
                self.navRequest.emit(True, obj)
                return True
            elif event.key() == QtCore.Qt.Key_PageDown:
                self.navRequest.emit(False, obj)
                return True

        return super(QtWidgets.QGroupBox, self).eventFilter(obj, event)

    def clear(self):
        """Clears all data from the LevelEditor"""
        self.level = None
        self.setTitle('Level')

        # Disable all of the data-editing widgets
        self.NameEdit.setEnabled(False)
        self.FileEdit.setEnabled(False)
        self.DisplayEdit.setEnabled(False)
        self.IsLevelEdit.setEnabled(False)
        self.NormalExitEdit.setEnabled(False)
        self.SecretExitEdit.setEnabled(False)
        self.CreatorEdit.setEnabled(False)
        self.DevRecordTimeEdit.setEnabled(False)

        # Set them all to '', 0, and False
        self.NameEdit.setText('')
        self.FileEdit.reset()
        self.DisplayEdit.reset()
        self.IsLevelEdit.setChecked(False)
        self.NormalExitEdit.setChecked(False)
        self.SecretExitEdit.setChecked(False)
        self.CreatorEdit.setCurrentIndex(0)
        self.DevRecordTimeEdit.setValue(0)

    def setLevel(self, level):
        """Sets the level to be edited"""
        self.level = level
        self.setTitle(self.level.name)

        # Enable all of the data-editing widgets
        self.NameEdit.setEnabled(True)
        self.FileEdit.setEnabled(True)
        self.DisplayEdit.setEnabled(True)
        self.IsLevelEdit.setEnabled(True)
        self.NormalExitEdit.setEnabled(True)
        self.SecretExitEdit.setEnabled(True)
        self.CreatorEdit.setEnabled(True)
        self.DevRecordTimeEdit.setEnabled(True)

        # Set them to the correct values
        self.NameEdit.setText(level.name)
        self.FileEdit.setData(level.FileW, level.FileL)
        self.DisplayEdit.setData(level.DisplayW, level.DisplayL)
        self.IsLevelEdit.setChecked(level.IsLevel)
        self.NormalExitEdit.setChecked(level.NormalExit)
        self.SecretExitEdit.setChecked(level.SecretExit)
        self.CreatorEdit.setCurrentIndex(level.CreatorIndex)
        self.DevRecordTimeEdit.setValue(level.DevRecordTime)

    def HandleNameChange(self):
        """Handles self.NameEdit changes"""
        if self.level == None: return
        self.level.name = str(self.NameEdit.text())
        self.dataChanged.emit()
        self.setTitle('Level - ' + self.level.name)

    def HandleFileChange(self):
        """Handles self.FileEdit changes"""
        if self.level == None: return
        self.level.FileW = self.FileEdit.world()
        self.level.FileL = self.FileEdit.level()
        self.dataChanged.emit()

    def HandleDisplayChange(self):
        """Handles self.DisplayEdit changes"""
        if self.level == None: return
        self.level.DisplayW = self.DisplayEdit.world()
        self.level.DisplayL = self.DisplayEdit.level()
        self.dataChanged.emit()

    def HandleIsLevelChange(self):
        """Handles self.IsLevelEdit changes"""
        if self.level == None: return
        self.level.IsLevel = self.IsLevelEdit.isChecked()
        self.dataChanged.emit()

    def HandleNormalExitChange(self):
        """Handles self.NormalExitEdit changes"""
        if self.level == None: return
        self.level.NormalExit = self.NormalExitEdit.isChecked()
        self.dataChanged.emit()

    def HandleSecretExitChange(self):
        """Handles self.SecretExitEdit changes"""
        if self.level == None: return
        self.level.SecretExit = self.SecretExitEdit.isChecked()
        self.dataChanged.emit()

    def HandleCreatorChange(self):
        """Handles self.CreatorEdit changes"""
        if self.level == None: return
        self.level.CreatorIndex = self.CreatorEdit.currentIndex()
        self.dataChanged.emit()

    def HandleDevRecordChange(self, value):
        """Handles self.DevRecordTime changes"""
        if self.level == None: return
        self.level.DevRecordTime = value
        self.dataChanged.emit()



class LevelNameEdit(QtWidgets.QWidget):
    """Widget that allows a level name to be edited"""
    dataChanged = QtCore.pyqtSignal()
    def __init__(self):
        """Initialises the LevelNameEdit"""
        QtWidgets.QWidget.__init__(self)

        self.WEdit = QtWidgets.QSpinBox()
        self.WEdit.setMaximum(255)
        Label = QtWidgets.QLabel('-')
        Label.setMaximumWidth(Label.minimumSizeHint().width())
        self.LEdit = QtWidgets.QSpinBox()
        self.LEdit.setMaximum(255)

        self.WEdit.valueChanged.connect(self.emitDataChange)
        self.LEdit.valueChanged.connect(self.emitDataChange)

        L = QtWidgets.QHBoxLayout()
        L.setContentsMargins(0, 0, 0, 0)
        L.addWidget(self.WEdit)
        L.addWidget(Label)
        L.addWidget(self.LEdit)
        self.setLayout(L)

    def setData(self, w, L):
        """Sets the world and level values"""
        self.WEdit.setValue(w)
        self.LEdit.setValue(L)
    def world(self):
        """Returns the world value"""
        return self.WEdit.value()
    def level(self):
        """Returns the level value"""
        return self.LEdit.value()
    def setEnabled(self, enabled):
        """Enables or disables the widget"""
        self.WEdit.setEnabled(enabled)
        self.LEdit.setEnabled(enabled)
    def reset(self):
        """Resets the widget"""
        self.WEdit.setValue(0)
        self.LEdit.setValue(0)
    def emitDataChange(self):
        """Emits the dataChange signal"""
        self.dataChanged.emit()
    def setMinToOne(self):
        """Sets the minimum for each spinbox to 1"""
        self.WEdit.setMinimum(1)
        self.LEdit.setMinimum(1)



########################################################################
########################################################################
########################################################################
########################################################################



class MainWindow(QtWidgets.QMainWindow):
    """Main window"""
    def __init__(self):
        """Initialises the window"""
        QtWidgets.QMainWindow.__init__(self)
        self.fp = None # file path

        # Create the viewer
        self.view = LevelInfoViewer()
        self.setCentralWidget(self.view)

        # Create the menubar and a few actions
        self.CreateMenubar()

        # Set window title and show the window
        self.setWindowTitle('Level Info Editor')
        self.show()

    def CreateMenubar(self):
        """Sets up the menubar"""
        m = self.menuBar()

        # File Menu
        f = m.addMenu('&File')

        openAct = f.addAction('Open File...')
        openAct.setShortcut('Ctrl+O') 
        openAct.triggered.connect(self.HandleOpen)

        self.saveAct = f.addAction('Save File')
        self.saveAct.setShortcut('Ctrl+S')
        self.saveAct.triggered.connect(self.HandleSave)
        self.saveAct.setEnabled(False)

        saveAsAct = f.addAction('Save File As...')
        saveAsAct.setShortcut('Ctrl+Shift+S')
        saveAsAct.triggered.connect(self.HandleSaveAs)

        f.addSeparator()

        exitAct = f.addAction('Exit')
        exitAct.setShortcut('Ctrl+Q')
        exitAct.triggered.connect(self.HandleExit)

        # Help Menu
        h = m.addMenu('&Help')

        aboutAct = h.addAction('About...')
        aboutAct.setShortcut('Ctrl+H')
        aboutAct.triggered.connect(self.HandleAbout)


    def HandleOpen(self):
        """Handles file opening"""
        fp = QtWidgets.QFileDialog.getOpenFileName(self, 'Open File', '', 'Binary Files (*.bin);;All Files (*)')[0]
        if fp == '': return
        self.fp = fp

        # Open the file
        file = open(fp, 'rb')
        data = file.read()
        file.close()
        LevelInfo = LevelInfoFile(data)

        # Update the viewer with this data
        self.view.setFile(LevelInfo)

        # Enable saving
        self.saveAct.setEnabled(True)

    def HandleSave(self):
        """Handles file saving"""
        data = self.view.saveFile()

        # Open the file
        file = open(self.fp, 'wb')
        file.write(data)
        file.close()

    def HandleSaveAs(self):
        """Handles saving to a new file"""
        fp = QtWidgets.QFileDialog.getSaveFileName(self, 'Save File', '', 'Binary Files (*.bin);;All Files (*)')[0]
        if fp == '': return
        self.fp = fp

        # Save it
        self.HandleSave()

        # Enable saving
        self.saveAct.setEnabled(True)

    def HandleExit(self):
        """Exits"""
        raise SystemExit

    def HandleAbout(self):
        """Shows the About dialog"""
        try: readme = open('readme.md', 'r').read()
        except: readme = 'Level Info Editor %s by RoadrunnerWMC\n(No readme.md found!)\nLicensed under GPL 3' % version

        txtedit = QtWidgets.QPlainTextEdit(readme)
        txtedit.setReadOnly(True)

        buttonBox = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(txtedit)
        layout.addWidget(buttonBox)

        dlg = QtWidgets.QDialog()
        dlg.setLayout(layout)
        dlg.setModal(True)
        dlg.setMinimumWidth(384)
        buttonBox.accepted.connect(dlg.accept)
        dlg.exec_()



# Main function
if __name__ == '__main__':
    """Main startup function"""
    app = QtWidgets.QApplication(sys.argv)
    mainWindow = MainWindow()
    sys.exit(app.exec_())