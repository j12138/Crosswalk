import sys
import os
import time
import glob
import json
from PyQt5.QtWidgets import QMessageBox, QDialog, QApplication, \
    QWidget, QDesktopWidget, QHBoxLayout, QVBoxLayout, QPushButton, QGroupBox, \
    QGridLayout, QLabel, QCheckBox, QRadioButton, QStyle, QStyleFactory, \
    QTableWidget, QTableWidgetItem, QFileDialog
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtCore import Qt, pyqtSignal
from labeling_tool import LabelingController, LabelingTool, DataSelector
# from labeling import preprocess

startTime = 0


class MainWindow(QWidget):
    """
    PyQt UI widget for main window
    """
    switch_window = pyqtSignal(str)

    def __init__(self):
        QWidget.__init__(self)
        self.setWindowTitle('Crosswalk Data Manager')
        self.initUI()

    def initUI(self):
        app_name = QLabel('Crosswalk Data Manager')
        test = QFont("Calibri", 27)
        test.setBold(10)
        app_name.setFont(test)
        app_name.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        button_styleSheet = "QPushButton{font-size: 25px;font-family: Calibri;}"
        but_preprocess = QPushButton('Preprocess')
        but_preprocess.clicked.connect(self.__do_preprocess)
        but_preprocess.setFixedHeight(50)
        but_preprocess.setFixedWidth(200)
        but_preprocess.setStyleSheet(button_styleSheet)

        but_labeling = QPushButton('Labeling')
        but_labeling.clicked.connect(self.__do_labeling)
        but_labeling.setFixedHeight(50)
        but_labeling.setFixedWidth(200)
        but_labeling.setStyleSheet(button_styleSheet)

        copyright = QLabel('ⓒ2019. Batoners Inc. All Rights Reserved')

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addStretch(2)
        main_layout.addWidget(app_name)
        main_layout.addStretch(5)
        main_layout.addWidget(but_preprocess)
        main_layout.setAlignment(but_preprocess, Qt.AlignHCenter)
        main_layout.addStretch(1)
        main_layout.addWidget(but_labeling)
        main_layout.setAlignment(but_labeling, Qt.AlignHCenter)
        main_layout.addStretch(5)
        main_layout.addWidget(copyright)

        self.resize(600, 500)
        self.put_window_on_center_of_screen()

    def put_window_on_center_of_screen(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def __do_preprocess(self):
        self.switch_window.emit('preprocess')

    def __do_labeling(self):
        self.switch_window.emit('labeling')


class DoPreprocess(QWidget):
    switch_window = pyqtSignal(str)

    def __init__(self):
        QWidget.__init__(self)
        self.initUI()

    def initUI(self):
        self.select_label = QLabel('Select data to preprocess')
        # More widgets here

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        main_layout.addWidget(self.select_label)
        # Organize layout here

        self.resize(500, 500)


class Controller:
    """
    Controller class for switching windows
    """
    def __init__(self):
        # self.lc = LabelingController()
        self.main_window = MainWindow()
        self.selector = DataSelector()

    def show_main_window(self):
        self.main_window.switch_window.connect(self.show_operation_window)
        self.main_window.show()

    def show_operation_window(self, operation):
        if operation == 'preprocess':
            self.do_preprocess = DoPreprocess()
            self.main_window.close()
            self.do_preprocess.show()

        elif operation == 'labeling':
            self.selector.set_data_dir()
            self.show_selector()
            self.selector.put_window_on_center_of_screen()

    def show_selector(self):
        self.selector.switch_window.connect(self.show_tool)
        self.selector.show()
        self.main_window.close()

    def show_tool(self, dir_path):
        global startTime
        startTime = time.time()
        self.tool = LabelingTool(os.path.join(dir_path, 'preprocessed'), startTime)
        self.tool.switch_window.connect(self.show_main_window)
        self.selector.close()
        self.tool.launch()

    def switch_labeling_to_main(self):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    app.setFont(QFont("Calibri", 10))

    controller = Controller()
    controller.show_main_window()

    sys.exit(app.exec())
