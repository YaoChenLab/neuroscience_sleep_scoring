import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import *
from pathlib import Path
import numpy as np
from numpy import asarray
from numpy import savetxt
import pandas as pd
import csv
from matplotlib import pyplot as plt



def isint(s):
    try:
        print(int(s))
        return True
    except ValueError:
        return False

def isfloat(s):
  try:
    print(float(s))
    return True
  except ValueError:
    return False

class NPYfile():
    def __init__(self,data,filename):
        self.data = data
        self.filename = filename
    def __str__(self):
        if hasattr(self.data, 'dtype'):
            return "Filename = "+str(self.filename )  +" \nDtype = "+str(self.data.dtype)+"\nShape = "+str(self.data.shape)
        else:
            return "Filename = " + str(self.filename) + " \nDtype = "  + "\nShape = " + str(self.data.shape)

class MainApp(QMainWindow):

    def __init__(self):
        super().__init__()
        self.left = 0
        self.top = 0
        self.width = 800
        self.height = 640
        #np.save('/home/user/tst.npy', np.array([255.0,50.0,10.0,5.0]))
        self.npyfile=None
        self.initUI()




    def saveAs(self):
        home = str(Path.home())
        path = QFileDialog.getSaveFileName(
            self, 'Save File', home, 'NPY (*.npy);;CSV(*.csv)')[0]
        #path = QFileDialog.getSaveFileName(
        #    self, 'Save File', home, 'CSV(*.csv)')[0]
        if  path !="" and ".csv" in path:
            with open((path.replace(".csv","")+".csv"), 'w') as stream:
                writer = csv.writer(stream)
                for row in range(self.tableWidget.rowCount()):
                    rowdata = []
                    for column in range(self.tableWidget.columnCount()):
                        item = self.tableWidget.item(row, column)
                        if item is not None:
                            rowdata.append(item.text())

                        else:
                            rowdata.append('')
                    writer.writerow(rowdata)
        else:
            OutMatrix=[]
            for row in range(self.tableWidget.rowCount()):
                rowdata = []
                for column in range(self.tableWidget.columnCount()):
                    item = self.tableWidget.item(row, column)
                    if item is not None:
                        if item.text().isnumeric():
                            rowdata.append(int(item.text()))
      
                if rowdata !=[]:
                    OutMatrix.append(rowdata)
            OutMatrix=np.array(OutMatrix)
            np.save(path, np.array(OutMatrix))

    def openNPY(self):
        home = str(Path.home())
        filename =  QFileDialog.getOpenFileName(self, 'Open .NPY file', home,".NPY files (*.npy);;.CSV files (*.csv)")[0]
        data=[]
        datafr=[]
        if filename != "":
            if ".npy" in filename:
                data=np.load(filename,allow_pickle=True)
                datafr = pd.DataFrame.from_records(data.tolist())
            else:
                data = np.array(pd.read_csv(filename).values.tolist())

            npyfile=NPYfile(data,filename)
            print(npyfile)
            self.setWindowTitle('NPYViewer v.1.1:  '+npyfile.filename)
            self.infoLb.setText("NPY Properties:\n"+str(npyfile))
            self.tableWidget.clear()

            rows= npyfile.data.shape[0]
            #print(npyfile.data.shape[0][0])

            if filename != ".npy" in filename:
                self.tableWidget.setRowCount(data.shape[0])
                self.tableWidget.setColumnCount(data.shape[1])
            else:
                self.tableWidget.setRowCount(data.shape[0])
                self.tableWidget.setColumnCount(data.shape[1])
                print (npyfile.data)
            for i, value1 in enumerate(npyfile.data):  # loop over items in first column
                print (value1)
                for j, value in enumerate(value1):
                    self.tableWidget.setItem(i, j, QTableWidgetItem(str(value)))
                    #print(i,j)
                    #print(value)
            self.npyfile=npyfile

            #for n, value in enumerate(df['T']):  # loop over items in second column
            #    self.data.setItem(n, 1, QTableWidgetItem(str(value)))



    def createMenu(self):

        exitAct = QAction(QIcon('exit.png'), '&Exit', self)
        exitAct.setShortcut('Ctrl+Q')
        exitAct.setStatusTip('Exit application')
        exitAct.triggered.connect(qApp.quit)

        openAct = QAction(QIcon('Open.png'), '&Open', self)
        openAct.setShortcut('Ctrl+O')
        openAct.setStatusTip('Open .NPY file')
        openAct.triggered.connect(self.openNPY)
        self.statusBar()

        saveAct = QAction(QIcon('Save.png'), '&Save As', self)
        saveAct.setShortcut('Ctrl+S')
        saveAct.setStatusTip('Save As')
        saveAct.triggered.connect(self.saveAs)
        self.statusBar()

        grayscalevVewAct = QAction(QIcon(None), '&View as Grayscale', self)
        grayscalevVewAct.setShortcut('Ctrl+V')
        grayscalevVewAct.setStatusTip('View as Grayscale')
        grayscalevVewAct.triggered.connect(self.grayscaleView)
        self.statusBar()
        
        View3dAct = QAction(QIcon(None), 'View &3D Point Cloud', self)
        View3dAct.setShortcut('Ctrl+3')
        View3dAct.setStatusTip('View 3D Point Cloud')
        View3dAct.triggered.connect(self.View3dPoints)
        self.statusBar()
        
        menubar = self.menuBar()
        fileMenu = menubar.addMenu('&Functionalities')
        fileMenu.addAction(openAct)
        fileMenu.addAction(saveAct)
        fileMenu.addAction(grayscalevVewAct)
        fileMenu.addAction(View3dAct)
        fileMenu.addAction(exitAct)

    def grayscaleView(self):
        OutMatrix=[]
        for row in range(self.tableWidget.rowCount()):
            rowdata = []
            for column in range(self.tableWidget.columnCount()):
                item = self.tableWidget.item(row, column)
                #print(item.text())
                if item is not None:
                        rowdata.append(np.int32(item.text()))
  
            if len(rowdata)>0 and rowdata !=None:
                OutMatrix.append(rowdata)
            
        
        OutMatrix=np.array(OutMatrix)
        print(OutMatrix)
        plt.imshow(OutMatrix, cmap='gray')
        plt.show()
        return
    

    
    def View3dPoints(self):
        OutMatrix=[]
        for row in range(self.tableWidget.rowCount()):
            rowdata = []
            for column in range(self.tableWidget.columnCount()):
                item = self.tableWidget.item(row, column)

                if item is not None:
                    if item.text():
                        rowdata.append(np.float32(item.text()))
            if len(rowdata)>0 and rowdata !=None:
                OutMatrix.append(rowdata)
        print(OutMatrix)
        OutMatrix=np.array(OutMatrix)



    
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        
        xs = OutMatrix[:,0]

        ys = OutMatrix[:,1]
        zs = OutMatrix[:,2]
        ax.scatter(xs, ys, zs, c='r', marker='o')
        
        ax.set_xlabel('X Label')
        ax.set_ylabel('Y Label')
        ax.set_zlabel('Z Label')

        plt.show()
        return
    
    def initUI(self):
        self.createMenu()

        self.infoLb = QLabel("NPY Properties:")
        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(100)
        self.tableWidget.setColumnCount(100)

        # table selection change
        #self.tableWidget.doubleClicked.connect(self.on_click)

        self.setGeometry(0, 0, 800, 600)
        self.setWindowTitle('NPYViewer v.1.1')

        self.widget = QWidget(self)
        layout = QGridLayout()
        layout.addWidget(self.infoLb)
        layout.addWidget(self.tableWidget)
        self.widget.setLayout(layout)
        self.setCentralWidget(self.widget)
        #self.tableWidget.setItesetTextAlignmentmDelegate(AlignDelegate())


        self.layout = QVBoxLayout()

        self.setLayout(self.layout)
        self.show()


def main():
    app = QApplication(sys.argv)
    ex = MainApp()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()