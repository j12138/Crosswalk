import sys
import os
import time
import glob
import json
from PyQt5.QtWidgets import QMessageBox, QDialog, QApplication, \
    QWidget, QDesktopWidget, QHBoxLayout, QVBoxLayout, QPushButton, QGroupBox, \
    QGridLayout, QLabel, QCheckBox, QRadioButton, QStyle, QStyleFactory, \
    QTableWidget, QTableWidgetItem, QFileDialog, QLineEdit
from PyQt5.QtGui import QImage, QPixmap, QFont
from PyQt5.QtCore import Qt, pyqtSignal
from labeling_tool import LabelingController, LabelingTool, DataSelector
# from labeling import preprocess

startTime = 0


def put_window_on_center_of_screen(window):
    qr = window.frameGeometry()
    cp = QDesktopWidget().availableGeometry().center()
    qr.moveCenter(cp)
    window.move(qr.topLeft())


class MainWindow(QWidget):
    """
    PyQt UI widget for main window
    """
    window_switch_signal = pyqtSignal(str)

    def __init__(self):
        QWidget.__init__(self)
        self.setWindowTitle('Crosswalk Data Manager')
        self.initUI()

    def initUI(self):
        app_name = QLabel('Crosswalk Data Manager')
        test = QFont("Calibri", 24)
        test.setBold(10)
        app_name.setFont(test)
        app_name.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        button_styleSheet = "QPushButton{font-size: 24px;font-family: Calibri;}"
        btn_preprocess = QPushButton('Preprocess')
        btn_preprocess.clicked.connect(self.__do_preprocess)
        btn_preprocess.setFixedHeight(40)
        btn_preprocess.setFixedWidth(200)
        btn_preprocess.setStyleSheet(button_styleSheet)

        btn_labeling = QPushButton('Labeling')
        btn_labeling.clicked.connect(self.__do_labeling)
        btn_labeling.setFixedHeight(40)
        btn_labeling.setFixedWidth(200)
        btn_labeling.setStyleSheet(button_styleSheet)

        btn_upload = QPushButton('Upload DB')
        # btn_upload.clicked.connect(self.__do_upload_DB)
        btn_upload.setFixedHeight(40)
        btn_upload.setFixedWidth(200)
        btn_upload.setStyleSheet(button_styleSheet)

        copyright = QLabel('ⓒ2019. Batoners Inc. All Rights Reserved')

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        main_layout.addStretch(2)
        main_layout.addWidget(app_name)
        main_layout.addStretch(5)

        main_layout.addWidget(btn_preprocess)
        main_layout.setAlignment(btn_preprocess, Qt.AlignHCenter)
        main_layout.addStretch(1)

        main_layout.addWidget(btn_labeling)
        main_layout.setAlignment(btn_labeling, Qt.AlignHCenter)
        main_layout.addStretch(1)

        main_layout.addWidget(btn_upload)
        main_layout.setAlignment(btn_upload, Qt.AlignHCenter)
        main_layout.addStretch(5)

        main_layout.addWidget(copyright)

        self.resize(470, 350)
        put_window_on_center_of_screen(self)

    def __do_preprocess(self):
        self.window_switch_signal.emit('preprocess')

    def __do_labeling(self):
        self.window_switch_signal.emit('labeling')

    def __do_upload_DB(self):
        # self.swit
        pass


class PreprocessWindow(QWidget):
    switch_signal = pyqtSignal()

    def __init__(self):
        QWidget.__init__(self)
        self.setWindowTitle('Preprocess')
        self.data_dir = ''
        self.initUI()

    def initUI(self):
        self.select_label = QLabel('Select data to preprocess :')
        self.button_filedialog = QPushButton(' Browse.. ')
        self.textbox_datadir = QLineEdit()
        self.button_filedialog.clicked.connect(self.select_directory)
        self.button_filedialog.setFixedWidth(150)
        self.userID_label = QLabel('User ID :')
        self.textbox_userID = QLineEdit()
        self.textbox_userID.setFixedWidth(200)
        self.button_preprocess = QPushButton('Start Preprocess')
        self.button_preprocess.setFixedHeight(50)
        self.button_preprocess.setFixedWidth(150)
        self.button_preprocess.setStyleSheet("background-color: skyblue")
        # More widgets here

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        browse_layout = QHBoxLayout()
        browse_layout.addWidget(self.textbox_datadir)
        browse_layout.addWidget(self.button_filedialog)
        browse_layout.setSpacing(10)

        userID_layout = QHBoxLayout()
        userID_layout.addWidget(self.userID_label)
        userID_layout.addWidget(self.textbox_userID)
        userID_layout.addStretch(10)

        start_layout = QHBoxLayout()
        start_layout.addWidget(self.button_preprocess, Qt.AlignCenter)

        main_layout.addStretch(1)
        main_layout.addWidget(self.select_label)
        main_layout.addLayout(browse_layout)
        main_layout.addStretch(1)
        main_layout.addLayout(userID_layout)
        main_layout.addStretch(2)
        main_layout.addLayout(start_layout)
        main_layout.addStretch(15)
        # Organize layout here

        self.resize(600, 500)
        put_window_on_center_of_screen(self)

    def select_directory(self):
        picked_dir = str(QFileDialog.getExistingDirectory(self,
                         "Select Directory"))
        self.data_dir = picked_dir
        self.textbox_datadir.setText(self.data_dir)

    def closeEvent(self, event):
        self.switch_signal.emit()


class Controller:
    """
    Controller class for switching windows
    """
    def __init__(self):
        # self.lc = LabelingController()
        self.main_window = MainWindow()
        self.selector = DataSelector()

    def show_main_window(self):
        self.__init__()
        self.main_window.window_switch_signal.connect(self.show_operation_window)
        self.main_window.show()
        return

    def show_operation_window(self, operation):
        if operation == 'preprocess':
            self.preprocess_window = PreprocessWindow()
            self.preprocess_window.switch_signal.connect(self.show_main_window)
            self.main_window.close()
            self.preprocess_window.show()

        elif operation == 'labeling':
            file_dialog_result = 'Retry'
            while file_dialog_result == 'Retry':
                print('Retry loop')
                file_dialog_result = self.selector.set_data_dir()

            print('esacpe loop!')
            if file_dialog_result == 'Close':
                print('catch close!')
                return

            self.show_selector()
            self.selector.put_window_on_center_of_screen()
        return

    def show_selector(self):
        self.selector.window_switch_signal.connect(self.show_tool)
        self.selector.show()
        self.main_window.close()

    def show_tool(self, dir_path):
        if dir_path == 'cancel':
            self.show_main_window()
            self.selector.close()
            return

        global startTime
        startTime = time.time()
        self.tool = LabelingTool(os.path.join(dir_path, 'preprocessed'), startTime)
        self.tool.window_switch_signal.connect(self.show_main_window)
        self.selector.close()
        self.tool.launch()
        return

    def switch_labeling_to_main(self):
        pass


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    app.setFont(QFont("Calibri", 10))

    controller = Controller()
    controller.show_main_window()

    sys.exit(app.exec())
