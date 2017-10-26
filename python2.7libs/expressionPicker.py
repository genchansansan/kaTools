#https://www.off-soft.net/ja/develop/qt/qtb2.html

import hou
import toolutils
import addExpression
from PySide2 import QtWidgets, QtCore, QtGui

reload(addExpression)

styles = {"valid" : "font: 16pt; background-color: #3e5062"
    , "invalid" : "font: 16pt; background-color: #990000"
    , "initial" : "font: 16pt; background-color: #222222"}

class snippet(QtWidgets.QTextEdit):
    def __init__(self, parent=None, label = None):
        super(snippet, self).__init__(parent)
        self.label = label


    def dragEnterEvent(self, event):
        event.acceptProposedAction()


    def dropEvent(self, event):
        text = event.mimeData().text()
        parm = hou.parm(text)
        if parm != None:
            print "parm!"
            mime = QtCore.QMimeData()
            mime.setText("")
            newEvent = QtGui.QDropEvent(event.pos(), event.dropAction(), mime, event.mouseButtons(), event.keyboardModifiers())
            super(snippet, self).dropEvent(newEvent)
            self.label.setText(text)
            self.setText(parm.eval())
            self.label.setStyleSheet(styles["valid"])
        elif text[0]!="/":
            super(snippet, self).dropEvent(event)
            self.label.setStyleSheet(styles["valid"])
        else:
            mime = QtCore.QMimeData()
            mime.setText("")
            newEvent = QtGui.QDropEvent(event.pos(), event.dropAction(), mime, event.mouseButtons(), event.keyboardModifiers())
            super(snippet, self).dropEvent(newEvent)
            self.label.setText("Invalid. Drop a parameter:")
            self.label.setStyleSheet(styles["invalid"])


class expressionTreeWidget(QtWidgets.QTreeWidget):
    mimeData = QtCore.QMimeData()
    def __init__(self, parent=None):
        QtWidgets.QTreeWidget.__init__(self, parent)

        self.setItemsExpandable(True)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(QtWidgets.QAbstractItemView.DragDrop)
        self.setAlternatingRowColors(True)
        self.ScrollMode(QtWidgets.QAbstractItemView.ScrollPerPixel)


    def mouseReleaseEvent(self, event):
        return_val = super( QtWidgets.QTreeWidget, self ).mouseReleaseEvent( event )
        #print "mouse release"
        #print hou.ui.curDesktop().paneTabUnderCursor().type()
        widget = QtWidgets.QApplication.instance().widgetAt(event.globalX(), event.globalY())
        if widget:
            self.searchChildren(widget)
       

    def mouseMoveEvent(self, event):
        '''
        #return_val = super( QtWidgets.QTreeWidget, self ).mouseReleaseEvent( event )
        allowDrop = False
        widget = QtWidgets.QApplication.instance().widgetAt(event.globalX(), event.globalY())
        if widget:
            #self.searchChildren(widget)
            pass
        '''
        drag = QtGui.QDrag(self)
        drag.setMimeData(self.mimeData)
        drag.exec_(QtCore.Qt.CopyAction | QtCore.Qt.MoveAction, QtCore.Qt.CopyAction)

    def searchChildren(self, parent):
        for child in parent.children():
                #print child
                if child:
                    if isinstance(child, QtGui.QTextFrame):
                        #print child.childFrames()
                        pass
                    self.searchChildren(child)



#############################################################
### 
#############################################################


class pickerWidget(QtWidgets.QFrame):

    prevClicked = QtWidgets.QTreeWidgetItem()
    
    def __init__(self, parent = None):
        #super(pickerWidget, self).__init__(parent)
        QtWidgets.QFrame.__init__(self, parent)
        
        self.preset = addExpression.wranglePreset(0)
        self.draggedItem = None

        layout = QtWidgets.QVBoxLayout()
        splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        #splitter.setSizes([900,100])

        ### set up label
        #title = QtWidgets.QLabel('Expression Picker')


        ### set up buttons
        buttonLayout = QtWidgets.QHBoxLayout()
        self.refreshButton = QtWidgets.QPushButton("Refresh")
        self.saveButton = QtWidgets.QPushButton("Save")
        self.deleteButton = QtWidgets.QPushButton("Delete")
        buttonLayout.addWidget(self.refreshButton)
        buttonLayout.addWidget(self.saveButton)
        buttonLayout.addWidget(self.deleteButton)
        self.refreshButton.clicked.connect(self.onRefreshClicked)
        self.saveButton.clicked.connect(self.onSaveClicked)
        self.deleteButton.clicked.connect(self.onDeleteClicked)

    
        ### set up tree widget
        self.treeWidget = expressionTreeWidget()
        self.treeWidget.setColumnCount(2)
        self.treeWidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.treeWidget.setColumnWidth(0, 150)
        self.treeWidget.setHeaderLabels(["Name", "Expression"])
        #self.treeWidget.setFocusPolicy(QtWidgets.Qt.WheelFocus)
        self.treeWidget.itemPressed.connect(self.onItemPressed)
        self.treeWidget.itemClicked.connect(self.onItemClicked)
        self.treeWidget.itemDoubleClicked.connect(self.onItemDoubleClicked)

        labelLayout = QtWidgets.QHBoxLayout()
        self.pathLabel = QtWidgets.QLabel()

        self.pathLabel.setStyleSheet(styles["initial"])

        self.pathLabel.setText("Drop parameter above:")
        labelLayout.addWidget(self.pathLabel)

        self.textArea = snippet(label = self.pathLabel)
        self.textArea.setAcceptDrops(True)
        self.textArea.textChanged.connect(self.onTextChanged)
        
        #layout.addWidget(title)
        layout.addLayout(buttonLayout)
        layout.addWidget(splitter)
        splitter.addWidget(self.treeWidget)
        splitter.addWidget(self.textArea)
        layout.addLayout(labelLayout)
        self.setLayout(layout)

        menus = self.importExpressionLabels()
        menus, categories = self.importExpressions(menus)
        self.updateTree(menus, categories)




    def onItemPressed(self, item, colmun):
        #print "item pressed"
        self.draggedItem =  item.text(1)
        self.treeWidget.mimeData = QtCore.QMimeData()
        self.treeWidget.mimeData.setText(item.text(1))


    
    def onItemDoubleClicked(self, item, column):
        self.treeWidget.editItem(item, column)
        


    def onItemClicked(self, item, column):
        if item.isSelected() == True:
            if self.prevClicked is item:
                selectecNodes = hou.selectedNodes()
                selectecNode = None

                if len(selectecNodes) == 0:
                    return
                selectecNode = selectecNodes[0]
                if selectecNode.type() == hou.sopNodeTypeCategory().nodeTypes()["attribwrangle"]:
                    self.draggedItem = item.text(1)
                    parmText = selectecNode.parm("snippet").eval()
                    selectecNode.parm("snippet").set(parmText + self.draggedItem)
            self.prevClicked = item


    def onRefreshClicked(self):
        self.preset = addExpression.wranglePreset(0)
        menus = self.importExpressionLabels()
        menus, categories = self.importExpressions(menus)
        self.updateTree(menus, categories)


    def onSaveClicked(self):
        self.preset = addExpression.wranglePreset(2)

        selectecNodes = hou.selectedNodes()
        selectecNode = None

        if len(selectecNodes) == 0:
            return
        selectecNode = selectecNodes[0]
        if selectecNode.type() == hou.sopNodeTypeCategory().nodeTypes()["attribwrangle"]:
            kwargs = {"parms":[selectecNode.parm("snippet")]}
            self.preset.saveXML(kwargs)

    def onDeleteClicked(self):
        selected = self.treeWidget.selectedItems()
        self.deleteExpression(selected)

    def onTextChanged(self):
        parm = hou.parm(self.pathLabel.text())
        if parm != None:
            parm.set(self.textArea.toPlainText())
            self.pathLabel.setStyleSheet(styles["valid"])
        else:
            self.pathLabel.setText("Invalid. Drop a parameter:")
            self.pathLabel.setStyleSheet(styles["invalid"])

############################################################


    def importExpressionLabels(self):
        # Reaed Presets
        menus = self.preset.makeMenus()
        #print menus
        return menus

    def importExpressions(self, menus):
        num = len(menus)/2
        categories = []
        for i in range(0, num):
            menus[i*2+1] = self.preset.exportExpression({"selectedlabel" : menus[i*2]})
            categories.append(self.preset.exportCategory({"selectedlabel" : menus[i*2]}))
        return menus, categories


    def clearItems(self, item):
        #print item
        length = item.childCount()
        if length > 0:
            for i in range(0, length):
                item.child(0)
                item.removeChild(item.child(0))


    def deleteExpression(self, items):
        length = len(items)
        if length == 0:
            return
        else:
            for item in items:
                self.preset.deleteExpression(item.text(0))
            self.onRefreshClicked()



    def updateTree(self, menus, categories):
        # Add expressions to the tree widget
        try:
            if self.treeWidget.itemPressed is not None:
                self.treeWidget.itemPressed.disconnect()
            if self.treeWidget.itemDoubleClicked is not None:
                self.treeWidget.itemDoubleClicked.disconnect()
        except Exception:
            #print Exception
            pass


        length = self.treeWidget.topLevelItemCount()
        if length > 0:
            for i in range(0, length):
                #print i
                self.clearItems(self.treeWidget.topLevelItem(0))
                self.treeWidget.takeTopLevelItem(0)
        self.treeWidget.clear()

        num = len(menus)/2

        for i in range(0, num):
            font = None
            category = None
            items = self.treeWidget.findItems(categories[i], 0)
            #print items
            if len(items) == 0:
                #print "none"
                parent = QtWidgets.QTreeWidgetItem(self.treeWidget)
                parent.setFlags(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
                parent.setText(0, categories[i])
                parent.setExpanded(False)
                category = parent

                font = category.font(0)
                font.setPointSize(11)
                category.setFont(0, font)
            else:
                category = items[0]
                font = category.font(0)

            
            brush0 = QtGui.QBrush(QtGui.QColor(0.3,0.3,1))
            
            font.setPointSize(10)
            child = QtWidgets.QTreeWidgetItem(category,[menus[2 * i], menus[2 * i + 1]])
            child.setFlags(QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            for column in range(0, child.columnCount()):
                child.setFont(column, font)

        
        self.treeWidget.itemPressed.connect(self.onItemPressed)
        self.treeWidget.itemDoubleClicked.connect(self.onItemDoubleClicked)
