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
import preprocess
sys.path.append(os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
import server

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

        btn_styleSheet = "QPushButton{font-size: 24px;font-family: Calibri;}"
        btn_preprocess = QPushButton('Preprocess')
        btn_preprocess.clicked.connect(self.__do_preprocess)
        btn_preprocess.setFixedHeight(40)
        btn_preprocess.setFixedWidth(200)
        btn_preprocess.setStyleSheet(btn_styleSheet)

        btn_labeling = QPushButton('Labeling')
        btn_labeling.clicked.connect(self.__do_labeling)
        btn_labeling.setFixedHeight(40)
        btn_labeling.setFixedWidth(200)
        btn_labeling.setStyleSheet(btn_styleSheet)

        btn_upload = QPushButton('Upload DB')
        btn_upload.clicked.connect(self.__do_upload_DB)
        btn_upload.setFixedHeight(40)
        btn_upload.setFixedWidth(200)
        btn_upload.setStyleSheet(btn_styleSheet)

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
        self.window_switch_signal.emit('upload')


class PreprocessWindow(QWidget):
    window_switch_signal = pyqtSignal()

    def __init__(self):
        QWidget.__init__(self)
        self.setWindowTitle('Preprocess')
        self.data_dir = ''
        self.initUI()

    def initUI(self):
        self.select_label = QLabel('Select data to preprocess :')
        self.btn_filedialog = QPushButton(' Browse.. ')
        self.textbox_datadir = QLineEdit()
        self.btn_filedialog.clicked.connect(self.select_directory)
        self.btn_filedialog.setFixedWidth(150)
        self.userID_label = QLabel('User ID :')
        self.textbox_userID = QLineEdit()
        self.textbox_userID.setFixedWidth(200)
        self.btn_start = QPushButton('Start Preprocess')
        self.btn_start.clicked.connect(self.start_preprocess)
        self.btn_start.setFixedHeight(50)
        self.btn_start.setFixedWidth(150)
        self.btn_start.setStyleSheet("background-color: skyblue")
        # More widgets here

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        browse_layout = QHBoxLayout()
        browse_layout.addWidget(self.textbox_datadir)
        browse_layout.addWidget(self.btn_filedialog)
        browse_layout.setSpacing(10)

        userID_layout = QHBoxLayout()
        userID_layout.addWidget(self.userID_label)
        userID_layout.addWidget(self.textbox_userID)
        userID_layout.addStretch(10)

        start_layout = QHBoxLayout()
        start_layout.addWidget(self.btn_start, Qt.AlignCenter)

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

    def start_preprocess(self):
        if self.textbox_userID.text() == '':
            print('userID: blank!')
        elif ' ' in self.textbox_userID.text():
            print('userID: space!')
        elif self.textbox_datadir.text() == '':
            print('data_dir: blank!')
        else:
            print('.......')
            preprocess.Controller(self.textbox_datadir.text(), self.textbox_userID.text()).show_progrees()
            # preprocess.ProgressBar(self.textbox_datadir.text(), self.textbox_userID.text()).show()
            # self.close()
            # preprocess_main(self.textbox_datadir.text(),
            #                 self.textbox_userID.text())
        pass

    def closeEvent(self, event):
        self.window_switch_signal.emit()


class UploadWindow(QWidget):
    window_switch_signal = pyqtSignal()

    def __init__(self):
        QWidget.__init__(self)
        self.setWindowTitle('Upload to Server')
        self.initUI()

    def initUI(self):
        self.userid_label = QLabel('User ID :')
        self.userpw_label = QLabel('User PW :')
        self.textbox_userid = QLineEdit()
        self.textbox_userpw = QLineEdit()
        self.textbox_userid.setFixedWidth(200)
        self.textbox_userpw.setFixedWidth(200)
        self.select_label = QLabel('Data directory to upload :')
        self.btn_filedialog = QPushButton(' Browse.. ')
        self.btn_filedialog.clicked.connect(self.select_directory)
        self.textbox_datadir = QLineEdit()
        self.btn_filedialog.setFixedWidth(150)
        self.btn_upload = QPushButton('Upload all DB')
        self.btn_upload.clicked.connect(self.upload_all_db)
        self.btn_upload.setFixedHeight(50)
        self.btn_upload.setFixedWidth(150)

        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        gbox_login = QGroupBox('Server Login Info')
        vbox_login = QVBoxLayout()

        hbox_id = QHBoxLayout()
        hbox_id.addWidget(self.userid_label)
        hbox_id.addWidget(self.textbox_userid)
        hbox_id.addStretch(10)

        hbox_pw = QHBoxLayout()
        hbox_pw.addWidget(self.userpw_label)
        hbox_pw.addWidget(self.textbox_userpw)
        hbox_pw.addStretch(10)

        vbox_login.addLayout(hbox_id)
        vbox_login.addLayout(hbox_pw)
        gbox_login.setLayout(vbox_login)

        browse_layout = QHBoxLayout()
        browse_layout.addWidget(self.textbox_datadir)
        browse_layout.addWidget(self.btn_filedialog)
        browse_layout.setSpacing(10)

        upload_layout = QHBoxLayout()
        upload_layout.addWidget(self.btn_upload, Qt.AlignCenter)

        main_layout.addWidget(gbox_login)
        main_layout.addStretch(1)
        main_layout.addWidget(self.select_label)
        main_layout.addLayout(browse_layout)
        main_layout.addStretch(2)
        main_layout.addLayout(upload_layout)
        main_layout.addStretch(10)

        self.resize(600, 500)
        put_window_on_center_of_screen(self)

    def select_directory(self):
        picked_dir = str(QFileDialog.getExistingDirectory(self,
                         "Select Directory"))
        self.data_dir = picked_dir
        self.textbox_datadir.setText(self.data_dir)

    def upload_all_db(self):
        if self.textbox_userid.text() == '':
            print('userID: blank!')
        elif self.textbox_userpw.text() == '':
            print('userPW: blank!')
        elif self.textbox_datadir.text() == '':
            print('datadir: blank!')
        else:
            server.main(True, self.textbox_userid.text(),
                              self.textbox_userpw.text(),
                              self.textbox_datadir.text())

    def closeEvent(self, event):
        self.window_switch_signal.emit()


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
            self.preprocess_window.window_switch_signal.connect(self.show_main_window)
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

        elif operation == 'upload':
            print('TODO: upload DB window')
            self.upload_db_window = UploadWindow()
            self.upload_db_window.window_switch_signal.connect(self.show_main_window)
            self.main_window.close()
            self.upload_db_window.show()

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
